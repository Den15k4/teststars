import logging
from bot.database.models import Database
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ReferralSystem:
    def __init__(self, db: Database):
        self.db = db

    async def process_referral(self, user_id: int, referrer_id: int) -> Optional[str]:
        """Обработка нового реферала"""
        async with self.db.pool.acquire() as conn:
            try:
                # Проверяем существование реферера
                referrer = await conn.fetchrow(
                    'SELECT user_id FROM users WHERE user_id = $1',
                    referrer_id
                )
                
                if not referrer:
                    return "Реферер не найден"

                if user_id == referrer_id:
                    return "Нельзя быть своим рефералом"

                # Проверяем, не был ли уже установлен реферер
                existing_user = await conn.fetchrow(
                    'SELECT referrer_id FROM users WHERE user_id = $1',
                    user_id
                )
                
                if existing_user and existing_user['referrer_id']:
                    return "Реферер уже установлен"

                # Проверяем на циклические связи
                referrer_chain = await conn.fetch('''
                    WITH RECURSIVE ref_chain AS (
                        SELECT user_id, referrer_id, 1 as depth
                        FROM users 
                        WHERE user_id = $1
                        UNION ALL
                        SELECT u.user_id, u.referrer_id, rc.depth + 1
                        FROM users u
                        INNER JOIN ref_chain rc ON rc.referrer_id = u.user_id
                        WHERE rc.depth < 10
                    )
                    SELECT user_id FROM ref_chain WHERE user_id = $2
                ''', referrer_id, user_id)

                if referrer_chain:
                    return "Обнаружена циклическая реферальная связь"

                # Устанавливаем реферера
                await conn.execute('''
                    UPDATE users 
                    SET referrer_id = $1 
                    WHERE user_id = $2
                ''', referrer_id, user_id)
                
                # Увеличиваем счетчик рефералов
                await conn.execute('''
                    UPDATE users 
                    SET total_referrals = total_referrals + 1 
                    WHERE user_id = $1
                ''', referrer_id)

                return None

            except Exception as e:
                logger.error(f"Error in process_referral: {e}")
                return "Произошла ошибка при обработке реферала"

    async def process_referral_payment(self, user_id: int, amount: float) -> Optional[float]:
        """Обработка платежа для реферальной системы"""
        async with self.db.pool.acquire() as conn:
            try:
                # Получаем реферера
                referrer = await conn.fetchrow('''
                    SELECT referrer_id 
                    FROM users 
                    WHERE user_id = $1 AND referrer_id IS NOT NULL
                ''', user_id)

                if referrer:
                    referrer_id = referrer['referrer_id']
                    bonus_amount = amount * 0.5  # 50% от суммы платежа

                    # Начисляем бонус рефереру
                    await conn.execute('''
                        UPDATE users 
                        SET referral_earnings = referral_earnings + $1 
                        WHERE user_id = $2
                    ''', bonus_amount, referrer_id)

                    return bonus_amount

                return None

            except Exception as e:
                logger.error(f"Error in process_referral_payment: {e}")
                return None

    async def get_referral_stats(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики рефералов пользователя"""
        async with self.db.pool.acquire() as conn:
            try:
                stats = await conn.fetchrow('''
                    SELECT 
                        total_referrals,
                        COALESCE(referral_earnings, 0) as referral_earnings
                    FROM users 
                    WHERE user_id = $1
                ''', user_id)

                return dict(stats) if stats else {
                    'total_referrals': 0,
                    'referral_earnings': 0
                }

            except Exception as e:
                logger.error(f"Error in get_referral_stats: {e}")
                return {
                    'total_referrals': 0,
                    'referral_earnings': 0
                }

    async def get_referrer(self, user_id: int) -> Optional[int]:
        """Получение ID реферера пользователя"""
        async with self.db.pool.acquire() as conn:
            try:
                result = await conn.fetchval('''
                    SELECT referrer_id 
                    FROM users 
                    WHERE user_id = $1 AND referrer_id IS NOT NULL
                ''', user_id)
                return result

            except Exception as e:
                logger.error(f"Error in get_referrer: {e}")
                return None