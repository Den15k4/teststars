from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, LabeledPrice
from ..database.models import Database
from ..keyboards.markups import Keyboards
from ..config import config
from ..services.referral import ReferralSystem

router = Router()

@router.callback_query(F.data == "buy_credits")
async def show_payment_options(callback: CallbackQuery):
    await callback.message.edit_text(
        "💫 Выберите количество генераций:\n\n"
        "ℹ️ Чем больше пакет, тем выгоднее цена за генерацию!\n\n"
        "💳 После выбора пакета откроется оплата звёздами",
        reply_markup=Keyboards.payment_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "check_balance")
async def check_balance(callback: CallbackQuery, db: Database):
    user_id = callback.from_user.id
    credits = await db.check_credits(user_id)
    
    await callback.message.edit_text(
        f"💰 Ваш текущий баланс: {credits} кредитов\n\n"
        "1 кредит = 1 обработка изображения",
        reply_markup=Keyboards.payment_menu()
    )
    await callback.answer()

@router.callback_query(F.data.matches(r"buy_\d+_stars"))
async def process_buy(callback: CallbackQuery, db: Database):
    try:
        package_id = int(callback.data.split("_")[1])
        package = next(
            (p for p in config.PACKAGES if p["id"] == package_id),
            None
        )
        
        if not package:
            await callback.answer("Пакет не найден")
            return

        await callback.message.answer_invoice(
            title=f"Покупка {package['description']}",
            description=f"Купить {package['credits']} генераций",
            payload=f"credits_{package_id}",
            provider_token="",  # Для звезд оставляем пустым
            currency="XTR",
            prices=[
                LabeledPrice(
                    label=package['description'],
                    amount=package['credits']
                )
            ]
        )
        
        await callback.answer()

    except Exception as e:
        print(f"Error in process_buy: {e}")
        await callback.answer("Произошла ошибка при создании платежа")

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

            # Отправляем уведомление о бонусе рефереру
            if bonus_amount:
                referrer_id = await db.get_user_referrer(message.from_id)
                if referrer_id:
                    await message.bot.send_message(
                        referrer_id,
                        f"🎁 Вы получили реферальный бонус {bonus_amount:.2f} RUB "
                        f"от оплаты вашего реферала!"
                    )

            await message.answer(
                f"✅ Оплата успешно получена!\n"
                f"💫 На ваш счет зачислено {package['credits']} кредитов",
                reply_markup=Keyboards.after_payment()
            )

    except Exception as e:
        print(f"Error in successful_payment: {e}")
        await message.answer(
            "Произошла ошибка при обработке платежа",
            reply_markup=Keyboards.back_to_menu()
        )
