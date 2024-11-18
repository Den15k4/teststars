import asyncio
import logging
from datetime import datetime, timedelta
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

# Middleware для передачи db в хэндлеры
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

# Инициализация бота и диспетчера
bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
db = Database(config.DATABASE_URL)

# Подключаем middleware
dp.update.middleware.register(DatabaseMiddleware(db))

# Подключаем роутеры в правильном порядке
dp.include_router(main_handlers.router)  # Общие обработчики должны быть первыми
dp.include_router(payments.router)
dp.include_router(referral.router)
dp.include_router(images.router)

# Создаём приложение для вебхуков
app = web.Application(client_max_size=50 * 1024 * 1024)  # 50 MB
clothoff_webhook = ClothOffWebhook(bot, db)

# Базовые хэндлеры
@dp.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject, db: Database):
    user_id = message.from_user.id
    username = message.from_user.username

    # Добавляем пользователя в БД
    await db.add_user(user_id, username)

    # Обрабатываем реферальный параметр
    args = command.args
    if args and args.startswith('ref'):
        try:
            referrer_id = int(args[3:])
            referral_system = ReferralSystem(db)
            error = await referral_system.process_referral(user_id, referrer_id)
            if not error:
                await message.answer("🎉 Вы успешно присоединились по реферальной ссылке!")
        except ValueError:
            pass

    await message.answer(
        "Добро пожаловать! 👋\n\n"
        "Я помогу вам раздеть любую даму!🔞\n\n"
        "Для начала работы приобретите кредиты 💸\n\n"
        "Выберите действие:",
        reply_markup=Keyboards.main_menu()
    )

async def cleanup_tasks():
    """Периодическая очистка зависших задач"""
    while True:
        try:
            # Получаем список очищенных задач
            stale_tasks = await db.cleanup_stale_tasks()
            
            # Уведомляем пользователей
            for task in stale_tasks:
                try:
                    time_passed = datetime.now(task['last_used'].tzinfo) - task['last_used']
                    minutes_passed = int(time_passed.total_seconds() / 60)
                    
                    await bot.send_message(
                        task['user_id'],
                        f"⚠️ Ваша предыдущая задача была отменена, так как прошло {minutes_passed} минут.\n"
                        "💫 Кредит возвращен на ваш баланс.\n"
                        "Вы можете начать новую обработку.",
                        reply_markup=Keyboards.main_menu()
                    )
                except Exception as e:
                    logger.error(f"Error notifying user {task['user_id']} about stale task: {e}")
            
            await asyncio.sleep(300)  # Проверяем каждые 5 минут
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)  # В случае ошибки ждем минуту
    """Периодическая очистка зависших задач"""
    while True:
        try:
            # Получаем список очищенных задач
            stale_tasks = await db.cleanup_stale_tasks()
            
            # Уведомляем пользователей
            for task in stale_tasks:
                try:
                    time_passed = datetime.now() - task['last_used']
                    minutes_passed = int(time_passed.total_seconds() / 60)
                    
                    await bot.send_message(
                        task['user_id'],
                        f"⚠️ Ваша предыдущая задача была отменена, так как прошло {minutes_passed} минут.\n"
                        "💫 Кредит возвращен на ваш баланс.\n"
                        "Вы можете начать новую обработку.",
                        reply_markup=Keyboards.main_menu()
                    )
                except Exception as e:
                    logger.error(f"Error notifying user {task['user_id']} about stale task: {e}")
            
            await asyncio.sleep(300)  # Проверяем каждые 5 минут
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)  # В случае ошибки ждем минуту

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

# Функция запуска бота
async def main():
    try:
        # Подключаемся к БД
        await db.connect()
        await db.init_db()
        
        # Запускаем вебхук сервер
        await run_webhook_server()
        
        # Запускаем очистку зависших задач
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