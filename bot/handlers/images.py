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

        # Проверяем активные задачи
        user = await db.get_user(user_id)
        if user.get('pending_task_id'):
            await callback.answer("У вас уже есть активная задача!")
            try:
                await callback.message.edit_text(
                    "⚠️ У вас уже есть активная задача в обработке.\n"
                    "Пожалуйста, дождитесь её завершения.",
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
        user = await db.get_user(user_id)
        if user.get('pending_task_id'):
            await message.reply(
                "⚠️ У вас уже есть активная задача в обработке.\n"
                "Пожалуйста, дождитесь её завершения.",
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

        # Проверяем возраст
        if not await clothoff_api.check_age(image_data):
            raise ValueError("AGE_RESTRICTION")

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
            "🔍 Результат будет отправлен, когда обработка завершится.",
            reply_markup=Keyboards.main_menu()
        )

    except ValueError as e:
        error_msg = str(e)
        if error_msg == "AGE_RESTRICTION":
            await message.reply(
                "🔞 Обработка запрещена:\n\n"
                "Изображение не прошло проверку возрастных ограничений. "
                "Пожалуйста, убедитесь, что на фото только люди старше 18 лет.",
                reply_markup=Keyboards.main_menu()
            )
        else:
            raise

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