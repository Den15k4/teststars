from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from bot.config import config

class Keyboards:
    @staticmethod
    def main_menu():
        """Главное меню"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="💫 Раздеть подругу", callback_data="start_processing"),
            InlineKeyboardButton(text="💳 Купить кредиты", callback_data="buy_credits")
        )
        builder.row(
            InlineKeyboardButton(text="💰 Баланс", callback_data="check_balance"),
            InlineKeyboardButton(text="👥 Реферальная программа", callback_data="referral_program")
        )
        return builder.as_markup()

    @staticmethod
    def payment_menu():
        """Меню выбора пакета кредитов"""
        builder = InlineKeyboardBuilder()
        
        for package in config.PACKAGES:
            builder.row(InlineKeyboardButton(
                text=f"{package['description']}",
                callback_data=f"buy_{package['id']}_stars"
            ))
            
        builder.row(InlineKeyboardButton(
            text="↩️ Назад",
            callback_data="back_to_menu"
        ))
        return builder.as_markup()

    @staticmethod
    def processing_cancel():
        """Кнопка отмены при обработке"""
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="❌ Отмена",
            callback_data="back_to_menu"
        ))
        return builder.as_markup()

    @staticmethod
    def back_keyboard():
        """Кнопка возврата к главному меню"""
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="↩️ Назад",
            callback_data="back_to_menu"
        ))
        return builder.as_markup()