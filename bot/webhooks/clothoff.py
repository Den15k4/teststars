from aiohttp import web
import logging
from bot.keyboards.markups import Keyboards
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)

class ClothOffWebhook:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.keyboards = Keyboards

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Обработчик вебхуков от ClothOff API"""
        try:
            # Получаем заголовки запроса и параметры
            headers = request.headers
            params = request.query
            logger.info(f"Webhook headers: {dict(headers)}")
            logger.info(f"Webhook params: {dict(params)}")

            # Читаем тело запроса
            body = await request.read()
            logger.info(f"Получен webhook, размер данных: {len(body)} bytes")
            logger.info(f"Content-Type: {request.content_type}")

            # Получаем id_gen из параметров
            id_gen = params.get('id_gen')
            if not id_gen:
                logger.error("id_gen не найден в параметрах")
                return web.Response(status=400, text="Missing id_gen")

            try:
                user_id = int(id_gen.split('_')[1])
                logger.info(f"Извлечен user_id: {user_id}")
            except (IndexError, ValueError) as e:
                logger.error(f"Ошибка при извлечении user_id: {e}")
                return web.Response(status=400, text="Invalid id_gen format")

            # Получаем пользователя
            user = await self.db.get_user(user_id)
            if not user:
                logger.error(f"Пользователь не найден: {user_id}")
                return web.Response(status=404, text="User not found")

            # Обрабатываем изображение
            if len(body) > 100000 or request.content_type.startswith('multipart/form-data'):
                logger.info("Обрабатываем как бинарные данные изображения")
                try:
                    # Создаем InputFile из байтов
                    input_file = BufferedInputFile(
                        file=body,
                        filename="result.jpg"
                    )

                    # Отправляем фото
                    await self.bot.send_photo(
                        chat_id=user_id,
                        photo=input_file,
                        caption="✨ Мы её раздели! Любуйся!\nЧтобы обработать новое фото, нажмите кнопку 💫 Раздеть подругу",
                        reply_markup=self.keyboards.main_menu()
                    )
                    
                    # Очищаем задачу
                    await self.db.clear_pending_task(user_id)
                    logger.info(f"Успешно отправлено обработанное изображение пользователю {user_id}")
                    
                    return web.Response(text='{"status":"success"}')
                except Exception as e:
                    logger.error(f"Ошибка при отправке фото: {e}", exc_info=True)
                    await self.db.return_credit(user_id)
                    await self.db.clear_pending_task(user_id)
                    await self.bot.send_message(
                        user_id,
                        "❌ Произошла ошибка при обработке результата. Попробуйте еще раз.",
                        reply_markup=self.keyboards.main_menu()
                    )
                    raise

            logger.error("Неподдерживаемый тип данных")
            return web.Response(status=400, text="Unsupported data type")

        except Exception as e:
            logger.error(f"Критическая ошибка в обработчике webhook: {e}", exc_info=True)
            return web.Response(status=500, text=str(e))