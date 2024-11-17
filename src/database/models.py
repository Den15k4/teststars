import asyncpg
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, url: str):
        self.url = url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self) -> None:
        """Создание пула подключений к БД"""
        self.pool = await asyncpg.create_pool(
            self.url,
            max_size=20
        )

    async def close(self) -> None:
        """Закрытие пула подключений"""
        if self.pool:
            await self.pool.close()

    async def init_db(self) -> None:
        """Инициализация таблиц БД"""
        async with self.pool.acquire() as conn:
            # Создаем таблицу пользователей
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

            # Создаем таблицу платежей
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(user_id),
                    payment_id TEXT UNIQUE,
                    amount DECIMAL,
                    credits INTEGER,
                    status TEXT,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
                CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
            ''')

    async def add_user(self, user_id: int, username: str = None) -> None:
        """Добавление нового пользователя"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO users (user_id, username, credits) 
                VALUES ($1, $2, 0) 
                ON CONFLICT (user_id) DO NOTHING
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
                SET pending_task_id = $1
                WHERE user_id = $2
            ''', task_id, user_id)

    async def clear_pending_task(self, user_id: int) -> None:
        """Очистка ID текущей задачи"""
        await self.update_pending_task(user_id, None)

    async def add_payment(self, user_id: int, payment_id: str, amount: float, credits: int) -> None:
        """Добавление записи о платеже"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO payments (user_id, payment_id, amount, credits, status)
                VALUES ($1, $2, $3, $4, 'pending')
            ''', user_id, payment_id, amount, credits)

    async def update_payment_status(self, payment_id: str, status: str) -> None:
        """Обновление статуса платежа"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                UPDATE payments 
                SET status = $1, updated_at = CURRENT_TIMESTAMP
                WHERE payment_id = $2
            ''', status, payment_id)

    async def get_user_referrer(self, user_id: int) -> Optional[int]:
        """Получение ID реферера пользователя"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval('''
                SELECT referrer_id 
                FROM users 
                WHERE user_id = $1 AND referrer_id IS NOT NULL
            ''', user_id)
            return result
