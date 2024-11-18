import asyncio
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.enums import ParseMode
from aiogram.types import Message, TelegramObject
from aiogram.filters import CommandStart, CommandObject
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
import json

from bot.config import config
from bot.database.models import Database
from bot.keyboards.markups import Keyboards
from bot.handlers import payments, referral, images, main_handlers
from bot.services.referral import ReferralSystem
from bot.webhooks.clothoff import ClothOffWebhook

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, database: Database):
        super().__init__()
        self.database = database

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data["db"] = self.database
        return await handler(event, data)

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
db = Database(config.DATABASE_URL)

dp.update.middleware.register(DatabaseMiddleware(db))

dp.include_router(main_handlers.router)
dp.include_router(payments.router)
dp.include_router(referral.router)
dp.include_router(images.router)

app = web.Application(client_max_size=50 * 1024 * 1024)
clothoff_webhook = ClothOffWebhook(bot, db)

async def initial_cleanup():
    """Начальная очистка всех зависших задач при старте бота"""
    try:
        async with db.pool.acquire() as conn:
            # Получаем все зависшие задачи для логирования
            stale_tasks = await conn.fetch('''
                SELECT user_id, pending_task_id, last_used
                FROM users 
                WHERE pending_task_id IS NOT NULL
            ''')
            
            if stale_tasks:
                logger.info(f"Found {len(stale_tasks)} stale tasks at startup")
                
                # Очищаем все задачи и возвращаем кредиты
                await conn.execute('''
                    UPDATE users 
                    SET credits = credits + 1,
                        pending_task_id = NULL,
                        last_used = NULL
                    WHERE pending_task_id IS NOT NULL
                ''')
                
                # Уведомляем пользователей
                for task in stale_tasks:
                    try:
                        await bot.send_message(
                            task['user_id'],
                            "⚠️ Бот был перезапущен, ваша предыдущая задача была отменена.\n"
                            "💫 Кредит возвращен на ваш баланс.\n"
                            "Вы можете начать новую обработку.",
                            reply_markup=Keyboards.main_menu()
                        )
                    except Exception as e:
                        logger.error(f"Error notifying user {task['user_id']} about cleanup: {e}")
            
            logger.info("Initial cleanup completed")
    except Exception as e:
        logger.error(f"Error in initial cleanup: {e}")

async def cleanup_tasks():
    """Периодическая очистка зависших задач"""
    while True:
        try:
            async with db.pool.acquire() as conn:
                # Находим и очищаем зависшие задачи старше 30 минут
                stale_tasks = await conn.fetch('''
                    WITH stale AS (
                        UPDATE users 
                        SET credits = credits + 1,
                            pending_task_id = NULL,
                            last_used = NULL
                        WHERE pending_task_id IS NOT NULL 
                        AND last_used < NOW() - INTERVAL '30 minutes'
                        RETURNING user_id, pending_task_id, last_used
                    )
                    SELECT * FROM stale
                ''')
                
                if stale_tasks:
                    logger.info(f"Cleaning up {len(stale_tasks)} stale tasks")
                    for task in stale_tasks:
                        try:
                            await bot.send_message(
                                task['user_id'],
                                "⚠️ Ваша предыдущая задача была отменена из-за превышения времени ожидания.\n"
                                "💫 Кредит возвращен на ваш баланс.\n"
                                "Вы можете начать новую обработку.",
                                reply_markup=Keyboards.main_menu()
                            )
                        except Exception as e:
                            logger.error(f"Error notifying user {task['user_id']}: {e}")
            
            await asyncio.sleep(60)  # Проверяем каждую минуту
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)

async def run_webhook_server():
    """Запуск вебхук сервера"""
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info(f"Started webhook server at port 8080")

# Маршруты
app.router.add_post('/clothoff/webhook', clothoff_webhook.handle_webhook)
app.router.add_get('/health', lambda _: web.Response(text='OK'))

async def main():
    try:
        await db.connect()
        await db.init_db()
        
        # Выполняем начальную очистку
        await initial_cleanup()
        
        await run_webhook_server()
        
        # Запускаем периодическую очистку
        asyncio.create_task(cleanup_tasks())
        
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен!")