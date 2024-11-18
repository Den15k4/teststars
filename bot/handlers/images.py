import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from bot.database.models import Database
from bot.keyboards.markups import Keyboards
from bot.services.clothoff import ClothOffAPI
from bot.config import config
import logging

router = Router()
clothoff_api = ClothOffAPI()
logger = logging.getLogger(__name__)

@router.callback_query(F.data == "start_processing")
async def start_processing(callback: CallbackQuery, db: Database):
    try:
        user_id = callback.from_user.id
        
        # Проверяем кредиты
        credits = await db.check_credits(user_id)
        if credits <= 0:
            await callback.answer("У вас недостаточно кредитов!")
            try:
                await callback.message.edit_text(
                    "❌ У вас нет кредитов\n\n"
                    "Пожалуйста, пополните баланс для начала работы.",
                    reply_markup=Keyboards.payment_menu()
                )
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
            return

        # Проверяем активные задачи с учетом таймаута
        has_active_task, task_id, age_seconds = await db.check_active_task(user_id)
        if has_active_task:
            minutes_left = 30 - int(age_seconds / 60) if age_seconds else 30
            await callback.answer("У вас уже есть активная задача!")
            try:
                await callback.message.edit_text(
                    f"⚠️ У вас уже есть активная задача в обработке.\n"
                    f"Пожалуйста, дождитесь её завершения или попробуйте через {minutes_left} минут.",
                    reply_markup=Keyboards.main_menu()
                )
            except TelegramBadRequest as e:
                if "message is not modified" not in str(e):
                    raise
            return

        try:
            await callback.message.edit_text(
                "📸 Отправьте мне фотографию для обработки\n\n"
                "⚠️ Важные правила:\n"
                "1. Изображение должно содержать только людей старше 18 лет\n"
                "2. Убедитесь, что на фото чётко все детали, которые вы хотите видеть\n"
                "3. Изображение должно быть хорошего качества",
                reply_markup=Keyboards.processing_cancel()
            )
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise

        await callback.answer()

    except Exception as e:
        logger.error(f"Error in start_processing: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)

@router.message(F.photo)
async def handle_photo(message: Message, db: Database):
    user_id = message.from_user.id
    processing_msg = None

    try:
        # Проверяем кредиты
        credits = await db.check_credits(user_id)
        if credits <= 0:
            await message.reply(
                "❌ У вас нет кредитов\n\n"
                "Пожалуйста, пополните баланс для начала работы.",
                reply_markup=Keyboards.payment_menu()
            )
            return

        # Проверяем активные задачи
        has_active_task, task_id, age_seconds = await db.check_active_task(user_id)
        
        if has_active_task:
            minutes_left = 30 - int(age_seconds / 60) if age_seconds else 30
            await message.reply(
                f"⚠️ У вас уже есть активная задача в обработке.\n"
                f"Пожалуйста, дождитесь её завершения или попробуйте через {minutes_left} минут.",
                reply_markup=Keyboards.main_menu()
            )
            return

        # Отправляем сообщение о начале обработки
        processing_msg = await message.reply("⏳ Начинаю раздевать...")

        # Получаем файл
        photo = message.photo[-1]
        file = await message.bot.get_file(photo.file_id)
        
        # Скачиваем изображение
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f'https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file.file_path}'
            ) as response:
                image_data = await response.read()

        # Проверяем изображение
        is_valid, error_msg = await clothoff_api.verify_image(image_data)
        if not is_valid:
            raise ValueError(error_msg)

        # Перед отправкой на обработку еще раз проверяем активные задачи
        has_active_task, _, _ = await db.check_active_task(user_id)
        if has_active_task:
            raise ValueError("ACTIVE_TASK_EXISTS")

        # Отправляем на обработку
        result = await clothoff_api.process_image(image_data, user_id)

        # Списываем кредит и обновляем задачу
        await db.use_credit(user_id)
        await db.update_pending_task(user_id, result['id_gen'])

        await message.reply(
            "✅ Изображение принято в обработку:\n\n"
            f"⏱ Время в очереди: {result['queue_time']} сек\n"
            f"📊 Позиция в очереди: {result['queue_num']}\n"
            f"🔄 ID задачи: {result['id_gen']}\n\n"
            "🔍 Результат будет отправлен, когда обработка завершится.\n"
            "⏳ Если результат не придет в течение 30 минут, задача будет отменена автоматически.",
            reply_markup=Keyboards.main_menu()
        )

    except ValueError as e:
        error_msg = str(e)
        if error_msg == "ACTIVE_TASK_EXISTS":
            await message.reply(
                "⚠️ У вас уже есть активная задача в обработке.\n"
                "Пожалуйста, дождитесь её завершения.",
                reply_markup=Keyboards.main_menu()
            )
        else:
            await message.reply(
                f"❌ {error_msg}",
                reply_markup=Keyboards.main_menu()
            )

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        error_msg = "❌ Произошла ошибка при обработке изображения."
        
        if 'INSUFFICIENT_BALANCE' in str(e):
            error_msg = (
                "⚠️ Сервис временно недоступен\n\n"
                "К сожалению, у сервиса закончился баланс API. "
                "Пожалуйста, попробуйте позже или свяжитесь с администратором бота.\n\n"
                "Ваши кредиты сохранены и будут доступны позже."
            )

        await message.reply(error_msg, reply_markup=Keyboards.main_menu())
        
        # Возвращаем кредит в случае ошибки
        if credits > 0:
            await db.return_credit(user_id)

    finally:
        if processing_msg:
            try:
                await processing_msg.delete()
            except Exception as e:
                logger.error(f"Error deleting processing message: {e}")