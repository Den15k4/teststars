from aiogram import Router, F
from aiogram.types import CallbackQuery
from bot.database.models import Database
from bot.keyboards.markups import Keyboards
from bot.services.referral import ReferralSystem

router = Router()

@router.callback_query(F.data == "referral_program")
async def show_referral_program(callback: CallbackQuery, db: Database):
    try:
        user_id = callback.from_user.id
        bot_username = (await callback.bot.get_me()).username
        referral_link = f"https://t.me/{bot_username}?start=ref{user_id}"
        
        referral_system = ReferralSystem(db)
        stats = await referral_system.get_referral_stats(user_id)
        
        await callback.message.edit_text(
            "👥 Реферальная программа\n\n"
            f"🔗 Ваша реферальная ссылка:\n"
            f"{referral_link}\n\n"
            f"📊 Статистика:\n"
            f"👤 Рефералов: {stats['total_referrals']}\n"
            f"💰 Заработано: {stats['referral_earnings']:.2f} RUB\n\n"
            "💡 Получайте 50% от каждого платежа ваших рефералов!",
            reply_markup=Keyboards.back_keyboard()
        )
        
        await callback.answer()

    except Exception as e:
        print(f"Error in show_referral_program: {e}")
        await callback.answer(
            "Произошла ошибка при загрузке реферальной программы",
            show_alert=True
        )

@router.callback_query(F.data == "refresh_referrals")
async def refresh_referral_stats(callback: CallbackQuery, db: Database):
    try:
        # Повторно вызываем показ реферальной программы
        await show_referral_program(callback, db)
        await callback.answer("Статистика обновлена!")
        
    except Exception as e:
        print(f"Error in refresh_referral_stats: {e}")
        await callback.answer(
            "Произошла ошибка при обновлении статистики",
            show_alert=True
        )