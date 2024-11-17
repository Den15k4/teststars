import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiohttp import web
import json

from config import config
from database.models import Database
from keyboards.markups import Keyboards
from handlers import payments, referral, images
from services.referral import ReferralSystem
from webhooks.clothoff import ClothOffWebhook

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

# Подключаем роутеры
dp.include_router(payments.router)
dp.include_router(referral.router)
dp.include_router(images.router)

# Создаём приложение для вебхуков
app = web.Application()
clothoff_webhook = ClothOffWebhook(bot, db)

# Базовые хэндлеры
@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    # Добавляем пользователя в БД
    await db.add_user(user_id, username)

    # Обрабатываем реферальный параметр
    args = message.get_args()
    if args.startswith('ref'):
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

# Обработчик кнопки "Назад"
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=Keyboards.main_menu()
    )

# Маршруты для вебхуков
app.router.add_post('/webhook', clothoff_webhook.handle_webhook)

async def run_webhook_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()

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
