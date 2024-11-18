from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from bot.database.models import Database
from bot.keyboards.markups import Keyboards
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    try:
        await callback.answer()
        await callback.message.edit_text(
            "Выберите действие:",
            reply_markup=Keyboards.main_menu()
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error in back_to_menu: {e}")
    except Exception as e:
        logger.error(f"Error in back_to_menu: {e}")

@router.callback_query(F.data == "check_balance")
async def check_balance(callback: CallbackQuery, db: Database):
    try:
        await callback.answer()
        credits = await db.check_credits(callback.from_user.id)
        await callback.message.edit_text(
            f"💰 Ваш текущий баланс: {credits} кредитов\n\n"
            "1 кредит = 1 обработка изображения",
            reply_markup=Keyboards.payment_menu()
        )
    except Exception as e:
        logger.error(f"Error in check_balance: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже", show_alert=True)

@router.callback_query(F.data == "buy_credits")
async def show_payment_options(callback: CallbackQuery):
    try:
        await callback.answer()
        await callback.message.edit_text(
            "💫 Выберите количество генераций:\n\n"
            "ℹ️ Чем больше пакет, тем выгоднее цена за генерацию!\n\n"
            "💳 После выбора пакета откроется оплата звёздами",
            reply_markup=Keyboards.payment_menu()
        )
    except Exception as e:
        logger.error(f"Error in show_payment_options: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже", show_alert=True)