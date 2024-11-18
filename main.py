import asyncio
import logging
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
from bot.handlers import payments, referral, images
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

# Подключаем роутеры
dp.include_router(payments.router)
dp.include_router(referral.router)
dp.include_router(images.router)

# Создаём приложение для вебхуков с увеличенным максимальным размером тела запроса
app = web.Application(client_max_size=50 * 1024 * 1024)  # 50 MB
clothoff_webhook = ClothOffWebhook(bot, db)

# Маршруты
@web.middleware
async def error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except Exception as ex:
        logger.error(f"Error in middleware: {ex}", exc_info=True)
        return web.Response(status=500, text=str(ex))

app.middlewares.append(error_middleware)

# Обработчик проверки состояния
async def health_check(request: web.Request) -> web.Response:
    return web.Response(text='OK')

# Добавляем роуты
app.router.add_post('/clothoff/webhook', clothoff_webhook.handle_webhook)
app.router.add_get('/health', health_check)

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

async def run_webhook_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info(f"Started webhook server at port 8080")

# Функция запуска бота
async def main():
    # Подключаемся к БД
    await db.connect()
    await db.init_db()
    
    # Запускаем вебхук сервер
    await run_webhook_server()
    
    logger.info("Запуск бота...")
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен!")