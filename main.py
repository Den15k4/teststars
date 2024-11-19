import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot.config import config
from bot.database.models import Database
from bot.webhooks.clothoff import ClothOffWebhook
from bot.handlers import setup_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=config.BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
db = Database(config.DATABASE_URL)

# Создаём приложение
app = web.Application()

# Инициализируем webhooks
clothoff_webhook = ClothOffWebhook(bot, db)

async def on_startup():
    """Действия при запуске бота"""
    await db.connect()
    await db.init_db()
    await setup_handlers(dp, db)
    logger.info("Бот запущен")

async def on_shutdown():
    """Действия при остановке бота"""
    await db.close()
    await bot.session.close()
    logger.info("Бот остановлен")

# Настраиваем маршруты
app.router.add_post('/clothoff/webhook', clothoff_webhook.handle_webhook)
app.router.add_get('/health', lambda _: web.Response(text='OK'))

# Настраиваем webhook handler для Telegram
webhook_handler = SimpleRequestHandler(
    dispatcher=dp,
    bot=bot,
)
webhook_handler.register(app, path='/telegram-webhook')

# Регистрируем хэндлеры событий
app.on_startup.append(lambda app: asyncio.create_task(on_startup()))
app.on_shutdown.append(lambda app: asyncio.create_task(on_shutdown()))

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8080)