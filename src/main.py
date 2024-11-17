import asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Загружаем переменные окружения
load_dotenv()

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплатить 20 ⭐", callback_data="buy_stars")
    
    await message.answer(
        "👋 Привет! Я тестовый бот для оплаты через Telegram Stars.\n"
        "⭐️ Нажмите кнопку ниже, чтобы поддержать!",
        reply_markup=builder.as_markup()
    )

# Хэндлер на нажатие кнопки
@dp.callback_query(lambda c: c.data == "buy_stars")
async def process_buy_stars(callback_query: types.CallbackQuery):
    await callback_query.answer()
    
    # Создаем объект с ценами
    prices = [types.LabeledPrice(label="XTR", amount=20)]
    
    await callback_query.message.answer_invoice(
        title="Поддержка канала",
        description="Поддержать канал на 20 звёзд!",
        payload="channel_support",
        provider_token="",  # Для Telegram Stars оставляем пустым
        currency="XTR",
        prices=prices
    )

# Обработчик пре-чекаута
@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

# Обработчик успешного платежа
@dp.message()
async def process_successful_payment(message: types.Message):
    if message.successful_payment:
        await message.answer(
            "🌟 Спасибо за вашу поддержку! 🌟"
        )

# Функция запуска бота
async def main():
    try:
        # Запускаем бота
        await dp.start_polling(bot)
    finally:
        # Закрываем сессию бота
        await bot.session.close()

if __name__ == '__main__':
    # Запускаем бота
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
