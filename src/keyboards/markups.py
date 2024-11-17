from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from ..config import config

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
    def after_payment():
        """Клавиатура после успешной оплаты"""
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="💫 Начать обработку", callback_data="start_processing"),
            InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_menu")
        )
        return builder.as_markup()

    @staticmethod
    def referral_menu(bot_username: str, user_id: int):
        """Меню реферальной программы"""
        referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="♻️ Обновить статистику",
            callback_data="refresh_referrals"
        ))
        builder.row(InlineKeyboardButton(
            text="↩️ В главное меню",
            callback_data="back_to_menu"
        ))
        return builder.as_markup(), referral_link

    @staticmethod
    def back_to_menu():
        """Кнопка возврата в главное меню"""
        builder = InlineKeyboardBuilder()
        builder.row(InlineKeyboardButton(
            text="↩️ В главное меню",
            callback_data="back_to_menu"
        ))
        return builder.as_markup()
