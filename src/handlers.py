from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

async def handle_payment(message: types.Message):
    prices = [types.LabeledPrice(label="XTR", amount=20)]
    
    await message.answer_invoice(
        title="Поддержка канала",
        description="Поддержать канал на 20 звёзд!",
        payload="channel_support",
        provider_token="",  # Для Telegram Stars оставляем пустым
        currency="XTR",
        prices=prices
    )
