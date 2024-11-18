from aiohttp import web
import logging
import json
from bot.keyboards.markups import Keyboards
from io import BytesIO

logger = logging.getLogger(__name__)

class ClothOffWebhook:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.keyboards = Keyboards

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Обработчик вебхуков от ClothOff API"""
        try:
            # Получаем заголовки запроса
            headers = request.headers
            logger.info(f"Webhook headers: {dict(headers)}")
            
            # Получаем query параметры
            params = request.query
            logger.info(f"Webhook params: {dict(params)}")
            
            # Читаем тело запроса
            body = await request.read()
            logger.info(f"Получен webhook, размер данных: {len(body)} bytes")
            logger.info(f"Content-Type: {request.content_type}")

            # Проверяем размер
            if len(body) > 50 * 1024 * 1024:  # 50 MB
                logger.error(f"Размер данных превышает лимит: {len(body)} bytes")
                raise web.HTTPRequestEntityTooLarge(
                    max_size=50 * 1024 * 1024,
                    actual_size=len(body)
                )

            # Пытаемся получить id_gen из query параметров или заголовков
            id_gen = params.get('id_gen') or headers.get('X-Task-ID')
            
            if not id_gen:
                logger.error("id_gen не найден в параметрах или заголовках")
                # Проверяем начало файла на наличие JPEG или PNG сигнатуры
                if body.startswith(b'\x89PNG') or body.startswith(b'\xff\xd8\xff'):
                    # Это похоже на изображение, пробуем получить id_gen из последнего успешного запроса
                    # TODO: реализовать кэширование последнего id_gen
                    logger.info("Получены бинарные данные изображения")
                    return web.Response(text='{"status":"success"}')
                return web.Response(status=400, text="Missing id_gen")

            try:
                user_id = int(id_gen.split('_')[1])
                logger.info(f"Извлечен user_id: {user_id}")
            except (IndexError, ValueError) as e:
                logger.error(f"Ошибка при извлечении user_id из {id_gen}: {e}")
                return web.Response(status=400, text="Invalid id_gen format")

            # Получаем пользователя
            user = await self.db.get_user(user_id)
            if not user:
                logger.error(f"Пользователь не найден: {user_id}")
                return web.Response(status=404, text="User not found")

            # Если content-type указывает на изображение или размер данных большой,
            # считаем что это бинарные данные изображения
            if (request.content_type and 'image' in request.content_type.lower()) or len(body) > 100000:
                logger.info("Обрабатываем как бинарные данные изображения")
                # Создаем BytesIO из данных
                photo = BytesIO(body)
                photo.name = 'result.jpg'

                try:
                    # Отправляем фото
                    await self.bot.send_photo(
                        chat_id=user_id,
                        photo=photo,
                        caption="✨ Мы её раздели! Любуйся!\nЧтобы обработать новое фото, нажмите кнопку 💫 Раздеть подругу",
                        reply_markup=self.keyboards.main_menu()
                    )
                    
                    # Очищаем задачу
                    await self.db.clear_pending_task(user_id)
                    logger.info(f"Успешно отправлено обработанное изображение пользователю {user_id}")
                    
                    return web.Response(text='{"status":"success"}')
                except Exception as e:
                    logger.error(f"Ошибка при отправке фото: {e}")
                    # Возвращаем кредит
                    await self.db.return_credit(user_id)
                    await self.db.clear_pending_task(user_id)
                    await self.bot.send_message(
                        user_id,
                        "❌ Произошла ошибка при обработке результата. Попробуйте еще раз.",
                        reply_markup=self.keyboards.main_menu()
                    )
                    raise

            # Если это не бинарные данные, пробуем обработать как JSON
            try:
                data = json.loads(body)
                # Обработка ошибок API
                if data.get('status') == '500' or data.get('img_message') or data.get('img_message_2'):
                    error_msg = data.get('img_message') or data.get('img_message_2') or 'Unknown error'
                    logger.error(f"Ошибка API: {error_msg}")
                    
                    message_text = "❌ Не удалось обработать изображение:\n" + error_msg
                    if 'Age is too young' in error_msg:
                        message_text = ("🔞 На изображении обнаружен человек младше 18 лет.\n"
                                      "Обработка таких изображений запрещена.")

                    await self.bot.send_message(
                        user_id,
                        message_text,
                        reply_markup=self.keyboards.main_menu()
                    )
                    
                    # Возвращаем кредит
                    await self.db.return_credit(user_id)
                    await self.db.clear_pending_task(user_id)
                    
                return web.Response(text='{"status":"handled"}')

            except json.JSONDecodeError:
                logger.error("Не удалось распарсить JSON и не похоже на изображение")
                return web.Response(status=400, text="Invalid data format")

        except Exception as e:
            logger.error(f"Критическая ошибка в обработчике webhook: {e}", exc_info=True)
            return web.Response(status=500, text=str(e))