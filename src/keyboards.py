from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

def get_start_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплатить 20 ⭐", callback_data="buy_stars")
    return builder.as_markup()
