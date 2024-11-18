from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice
from aiogram.exceptions import TelegramBadRequest
from bot.database.models import Database
from bot.keyboards.markups import Keyboards
from bot.config import config
from bot.services.referral import ReferralSystem
import logging

router = Router()
logger = logging.getLogger(__name__)

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
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            logger.error(f"Error in show_payment_options: {e}")
    except Exception as e:
        logger.error(f"Error in show_payment_options: {e}")
        await callback.answer("Произошла ошибка, попробуйте позже", show_alert=True)

@router.callback_query(F.data == "check_balance")
async def check_balance(callback: CallbackQuery, db: Database):
    try:
        credits = await db.check_credits(callback.from_user.id)
        await callback.message.edit_text(
            f"💰 Ваш текущий баланс: {credits} кредитов\n\n"
            "1 кредит = 1 обработка изображения",
            reply_markup=Keyboards.payment_menu()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in check_balance: {e}")
        await callback.answer("Произошла ошибка при проверке баланса", show_alert=True)

@router.callback_query(F.data.matches(r"buy_\d+_stars"))
async def process_buy(callback: CallbackQuery, db: Database):
    try:
        package_id = int(callback.data.split("_")[1])
        package = next(
            (p for p in config.PACKAGES if p["id"] == package_id),
            None
        )
        
        if not package:
            await callback.answer("Пакет не найден", show_alert=True)
            return

        # Создаем URL для оплаты звездами напрямую
        bot_username = (await callback.bot.get_me()).username
        payment_url = f"https://t.me/{bot_username}/star/{package['credits']}"

        await callback.message.edit_text(
            f"💫 Покупка {package['description']}\n\n"
            f"Стоимость: {package['credits']} звезд\n"
            "После оплаты кредиты будут начислены автоматически",
            reply_markup={
                'inline_keyboard': [
                    [{'text': f"⭐️ Оплатить {package['credits']} звезд", 'url': payment_url}],
                    [{'text': "↩️ Назад", 'callback_data': "back_to_menu"}]
                ]
            }
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error in process_buy: {e}")
        await callback.answer(
            "Произошла ошибка при создании платежа. Попробуйте позже.",
            show_alert=True
        )

@router.message(F.successful_payment)
async def successful_payment(message: Message, db: Database):
    try:
        # Получаем ID пакета из payload
        package_id = int(message.successful_payment.invoice_payload.split("_")[1])
        package = next(
            (p for p in config.PACKAGES if p["id"] == package_id),
            None
        )

        if package:
            # Начисляем кредиты
            await db.update_credits(message.from_id, package['credits'])

            # Обрабатываем реферальный платеж
            referral_system = ReferralSystem(db)
            bonus_amount = await referral_system.process_referral_payment(
                message.from_id,
                package['price']
            )

            if bonus_amount and referral_system:
                referrer_id = await db.get_user_referrer(message.from_id)
                if referrer_id:
                    await message.bot.send_message(
                        referrer_id,
                        f"🎁 Вы получили реферальный бонус {bonus_amount:.2f} RUB "
                        f"от оплаты вашего реферала!"
                    )

            await message.answer(
                f"✅ Оплата успешно получена!\n"
                f"💫 На ваш счет зачислено {package['credits']} кредитов\n\n"
                f"Хотите начать обработку прямо сейчас?",
                reply_markup={
                    'inline_keyboard': [
                        [
                            {'text': '💫 Начать обработку', 'callback_data': 'start_processing'},
                            {'text': '↩️ В главное меню', 'callback_data': 'back_to_menu'}
                        ]
                    ]
                }
            )

    except Exception as e:
        logger.error(f"Error in successful_payment: {e}")
        await message.answer(
            "❌ Произошла ошибка при обработке платежа.\n"
            "Пожалуйста, свяжитесь с администратором бота.",
            reply_markup=Keyboards.back_keyboard()
        )
    try:
        # Получаем ID пакета из payload
        package_id = int(message.successful_payment.invoice_payload.split("_")[1])
        package = next(
            (p for p in config.PACKAGES if p["id"] == package_id),
            None
        )

        if package:
            # Начисляем кредиты
            await db.update_credits(message.from_id, package['credits'])

            # Обрабатываем реферальный платеж
            referral_system = ReferralSystem(db)
            bonus_amount = await referral_system.process_referral_payment(
                message.from_id,
                package['price']
            )

            # Уведомляем реферера о бонусе
            if bonus_amount:
                referrer_id = await db.get_user_referrer(message.from_id)
                if referrer_id:
                    await message.bot.send_message(
                        referrer_id,
                        f"🎁 Вы получили реферальный бонус {bonus_amount:.2f} RUB "
                        f"от оплаты вашего реферала!"
                    )

            # Уведомляем пользователя об успешной покупке
            success_text = (
                f"✅ Оплата успешно получена!\n"
                f"💫 На ваш счет зачислено {package['credits']} кредитов\n\n"
                f"Хотите начать обработку прямо сейчас?"
            )
            
            # Клавиатура с кнопками быстрого действия
            quick_action_keyboard = {
                'inline_keyboard': [
                    [
                        {'text': '💫 Начать обработку', 'callback_data': 'start_processing'},
                        {'text': '↩️ В главное меню', 'callback_data': 'back_to_menu'}
                    ]
                ]
            }

            await message.answer(
                success_text,
                reply_markup=quick_action_keyboard
            )

    except Exception as e:
        logger.error(f"Error in successful_payment: {e}")
        error_text = (
            "❌ Произошла ошибка при обработке платежа.\n"
            "Пожалуйста, свяжитесь с администратором бота."
        )
        await message.answer(
            error_text,
            reply_markup=Keyboards.back_keyboard()
        )

@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query):
    try:
        await pre_checkout_query.answer(ok=True)
    except Exception as e:
        logger.error(f"Error in pre_checkout: {e}")
        await pre_checkout_query.answer(
            ok=False,
            error_message="Произошла ошибка при проверке платежа. Попробуйте позже."
        )