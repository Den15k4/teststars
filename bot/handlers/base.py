import logging
from aiogram import Dispatcher, types, F
from aiogram.filters import Command
from bot.keyboards.markups import Keyboards

logger = logging.getLogger(__name__)

async def cmd_start(message: types.Message, db):
    """Обработчик команды /start"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username

        # Добавляем пользователя в БД
        await db.add_user(user_id, username)
        
        await message.answer(
            "Добро пожаловать! 👋\n\n"
            "Я помогу вам раздеть любую даму!🔞\n\n"
            "Для начала работы приобретите кредиты 💸\n\n"
            "Выберите действие:",
            reply_markup=Keyboards.main_menu()
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

async def back_to_menu(callback: types.CallbackQuery):
    """Обработчик возврата в главное меню"""
    try:
        await callback.answer()
        await callback.message.edit_text(
            "Выберите действие:",
            reply_markup=Keyboards.main_menu()
        )
    except Exception as e:
        logger.error(f"Error in back_to_menu: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)

async def check_balance(callback: types.CallbackQuery, db):
    """Обработчик проверки баланса"""
    try:
        user_id = callback.from_user.id
        credits = await db.check_credits(user_id)

        await callback.answer()
        await callback.message.edit_text(
            f"💰 Ваш текущий баланс: {credits} кредитов\n\n"
            "1 кредит = 1 обработка изображения",
            reply_markup=Keyboards.back_to_menu()
        )
    except Exception as e:
        logger.error(f"Error in check_balance: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)

async def setup_base_handlers(dp: Dispatcher, db) -> None:
    """Регистрация базовых обработчиков"""
    dp.message.register(cmd_start, Command("start"))
    dp.callback_query.register(back_to_menu, F.data == "back_to_menu")
    dp.callback_query.register(check_balance, F.data == "check_balance")