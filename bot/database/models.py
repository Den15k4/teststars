import asyncpg
from typing import Optional, Dict, Any, Tuple, List
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, url: str):
        self.url = url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Создание пула подключений к БД"""
        self.pool = await asyncpg.create_pool(
            self.url,
            max_size=20,
            ssl='require'
        )

    async def close(self) -> None:
        """Закрытие пула подключений"""
        if self.pool:
            await self.pool.close()

    async def init_db(self) -> None:
        """Инициализация таблиц БД"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    credits INT DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMPTZ,
                    pending_task_id TEXT,
                    referrer_id BIGINT,
                    total_referrals INT DEFAULT 0,
                    referral_earnings DECIMAL DEFAULT 0.0
                );

                CREATE INDEX IF NOT EXISTS idx_referrer_id ON users(referrer_id);
                CREATE INDEX IF NOT EXISTS idx_pending_task ON users(pending_task_id);
                CREATE INDEX IF NOT EXISTS idx_last_used ON users(last_used);
            ''')

    async def cleanup_stale_tasks(self, timeout_minutes: int = 30) -> List[Dict]:
        """Очистка зависших задач старше timeout_minutes минут"""
        if not self.pool:
            return []
            
        async with self.pool.acquire() as conn:
            try:
                # Находим все зависшие задачи
                stale_tasks = await conn.fetch('''
                    SELECT 
                        user_id, 
                        pending_task_id,
                        last_used,
                        EXTRACT(EPOCH FROM (NOW() - last_used)) as age_seconds
                    FROM users 
                    WHERE pending_task_id IS NOT NULL 
                    AND last_used < NOW() - INTERVAL $1
                ''', f'{timeout_minutes} minutes')

                if stale_tasks:
                    # Очищаем найденные задачи
                    task_ids = [task['pending_task_id'] for task in stale_tasks]
                    user_ids = [task['user_id'] for task in stale_tasks]
                    
                    await conn.execute('''
                        UPDATE users 
                        SET credits = credits + 1,
                            pending_task_id = NULL,
                            last_used = NULL
                        WHERE user_id = ANY($1)
                    ''', user_ids)

                    logger.info(f"Очищено {len(stale_tasks)} зависших задач: {task_ids}")
                    return [dict(task) for task in stale_tasks]
                
                return []

            except Exception as e:
                logger.error(f"Ошибка при очистке зависших задач: {e}")
                return []

    async def force_cleanup_task(self, user_id: int) -> bool:
        """Принудительная очистка задачи пользователя"""
        if not self.pool:
            return False
            
        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetchrow('''
                    UPDATE users 
                    SET credits = credits + 1,
                        pending_task_id = NULL,
                        last_used = NULL
                    WHERE user_id = $1 
                    AND pending_task_id IS NOT NULL
                    RETURNING pending_task_id
                ''', user_id)
                
                if result:
                    logger.info(f"Принудительно очищена задача {result['pending_task_id']} пользователя {user_id}")
                    return True
                return False

            except Exception as e:
                logger.error(f"Ошибка при принудительной очистке задачи: {e}")
                return False

    async def check_active_task(self, user_id: int) -> Tuple[bool, Optional[str], Optional[float]]:
        """Проверка активной задачи с учетом таймаута"""
        async with self.pool.acquire() as conn:
            try:
                result = await conn.fetchrow('''
                    SELECT 
                        pending_task_id,
                        last_used,
                        EXTRACT(EPOCH FROM (NOW() - last_used)) as age_seconds
                    FROM users 
                    WHERE user_id = $1 
                    AND pending_task_id IS NOT NULL
                ''', user_id)

                if not result:
                    return False, None, None

                age_seconds = result['age_seconds'] if result['age_seconds'] else 0

                # Если задача старше 30 минут
                if age_seconds > 1800:  # 30 minutes
                    # Очищаем эту конкретную задачу
                    await self.force_cleanup_task(user_id)
                    return False, None, None

                return True, result['pending_task_id'], age_seconds

            except Exception as e:
                logger.error(f"Ошибка при проверке активной задачи: {e}")
                return False, None, None

    async def add_user(self, user_id: int, username: str = None) -> None:
        """Добавление нового пользователя"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, username, credits) 
                VALUES ($1, $2, 0) 
                ON CONFLICT (user_id) DO UPDATE 
                SET username = EXCLUDED.username
            ''', user_id, username or 'anonymous')

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе"""
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow(
                'SELECT * FROM users WHERE user_id = $1',
                user_id
            )
            return dict(user) if user else None

    async def check_credits(self, user_id: int) -> int:
        """Проверка баланса кредитов"""
        user = await self.get_user(user_id)
        return user['credits'] if user else 0

    async def use_credit(self, user_id: int) -> bool:
        """Использование кредита"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('''
                UPDATE users 
                SET credits = credits - 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE user_id = $1 AND credits > 0
                RETURNING credits
            ''', user_id)
            return bool(result)

    async def return_credit(self, user_id: int) -> None:
        """Возврат кредита"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE users 
                SET credits = credits + 1
                WHERE user_id = $1
            ''', user_id)

    async def update_pending_task(self, user_id: int, task_id: str) -> None:
        """Обновление ID текущей задачи"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE users 
                SET pending_task_id = $1,
                    last_used = CURRENT_TIMESTAMP
                WHERE user_id = $2
            ''', task_id, user_id)

    async def clear_pending_task(self, user_id: int) -> None:
        """Очистка ID текущей задачи"""
        await self.update_pending_task(user_id, None)

    async def update_credits(self, user_id: int, amount: int) -> None:
        """Обновление количества кредитов"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE users 
                SET credits = credits + $1 
                WHERE user_id = $2
            ''', amount, user_id)

    async def get_user_referrer(self, user_id: int) -> Optional[int]:
        """Получение ID реферера пользователя"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                'SELECT referrer_id FROM users WHERE user_id = $1',
                user_id
            )