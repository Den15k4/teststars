import logging
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile
from bot.keyboards.markups import Keyboards

logger = logging.getLogger(__name__)
router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, db):
    """Обработчик команды /start"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username

        logger.info(f"Starting command received from user {user_id} ({username})")

        # Добавляем пользователя в БД
        await db.add_user(user_id, username)

        # Проверяем реферальный параметр
        if message.text and ' ' in message.text:
            args = message.text.split()[1]
            if args.startswith('ref'):
                try:
                    referrer_id = int(args[3:])
                    # Обработка реферала будет добавлена позже
                    logger.info(f"Referral parameter detected: {referrer_id}")
                except ValueError:
                    logger.error("Invalid referral parameter")

        await message.answer(
            "Добро пожаловать! 👋\n\n"
            "Я помогу вам раздеть любую даму!🔞\n\n"
            "Для начала работы приобретите кредиты 💸\n\n"
            "Выберите действие:",
            reply_markup=Keyboards.main_menu()
        )
        logger.info(f"Welcome message sent to user {user_id}")

    except Exception as e:
        logger.error(f"Error in start command handler: {e}")
        await message.answer("Произошла ошибка при запуске бота. Попробуйте позже.")

@router.callback_query(F.data == "back_to_menu")
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

@router.callback_query(F.data == "check_balance")
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