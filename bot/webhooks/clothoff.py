from aiohttp import web
import logging
import json
import base64
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
            # Читаем тело запроса
            body = await request.read()
            logger.info(f"Получен webhook, размер данных: {len(body)} bytes")

            if len(body) > 50 * 1024 * 1024:  # 50 MB
                logger.error(f"Размер данных превышает лимит: {len(body)} bytes")
                raise web.HTTPRequestEntityTooLarge(
                    max_size=50 * 1024 * 1024,
                    actual_size=len(body)
                )

            try:
                # Пробуем декодировать JSON
                if request.content_type == 'application/json':
                    data = await request.json()
                else:
                    # Если content-type не json, пробуем сами декодировать
                    try:
                        data = json.loads(body)
                    except json.JSONDecodeError:
                        # Если не получилось декодировать JSON, считаем что это бинарные данные
                        data = {'result': body}
                
                logger.info(f"Тип полученных данных: {type(data)}")
                logger.info(f"Ключи в данных: {data.keys() if isinstance(data, dict) else 'binary data'}")
            except Exception as e:
                logger.error(f"Ошибка при декодировании данных: {e}")
                data = {'result': body}

            # Извлекаем user_id из id_gen
            try:
                user_id = int(data['id_gen'].split('_')[1])
                logger.info(f"Извлечен user_id: {user_id}")
            except (KeyError, IndexError, ValueError) as e:
                logger.error(f"Ошибка при извлечении user_id: {e}")
                return web.Response(status=400, text="Invalid id_gen format")

            # Получаем пользователя
            user = await self.db.get_user(user_id)
            if not user:
                logger.error(f"Пользователь не найден: {user_id}")
                return web.Response(status=404, text="User not found")

            # Обработка ошибок
            if data.get('status') == '500' or data.get('img_message') or data.get('img_message_2'):
                error_msg = data.get('img_message') or data.get('img_message_2') or 'Unknown error'
                logger.error(f"Ошибка API: {error_msg}")
                
                if 'Age is too young' in error_msg:
                    message_text = ("🔞 На изображении обнаружен человек младше 18 лет.\n"
                                  "Обработка таких изображений запрещена.")
                else:
                    message_text = f"❌ Не удалось обработать изображение:\n{error_msg}"

                await self.bot.send_message(
                    user_id,
                    message_text,
                    reply_markup=self.keyboards.main_menu()
                )
                
                # Возвращаем кредит и очищаем задачу
                await self.db.return_credit(user_id)
                await self.db.clear_pending_task(user_id)
                return web.Response(text='{"status":"error_handled"}')

            # Обработка успешного результата
            try:
                image_data = None
                
                # Пробуем разные варианты получения изображения
                if isinstance(data, dict):
                    if 'result' in data:
                        if isinstance(data['result'], str):
                            if data['result'].startswith('data:image'):
                                # Если это base64
                                image_data = base64.b64decode(data['result'].split(',')[1])
                            else:
                                # Если это просто строка с base64
                                try:
                                    image_data = base64.b64decode(data['result'])
                                except:
                                    pass
                        else:
                            # Если это бинарные данные
                            image_data = data['result']
                    elif 'image' in data:
                        image_data = base64.b64decode(data['image']) if isinstance(data['image'], str) else data['image']
                else:
                    # Если пришли прямые бинарные данные
                    image_data = body

                if not image_data:
                    raise ValueError("Не удалось получить данные изображения")

                # Создаем BytesIO из данных
                photo = BytesIO(image_data)
                photo.seek(0)
                photo.name = 'result.jpg'

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
                logger.error(f"Ошибка при обработке результата: {e}", exc_info=True)
                await self.bot.send_message(
                    user_id,
                    "❌ Произошла ошибка при обработке результата. Попробуйте еще раз.",
                    reply_markup=self.keyboards.main_menu()
                )
                # Возвращаем кредит и очищаем задачу
                await self.db.return_credit(user_id)
                await self.db.clear_pending_task(user_id)
                return web.Response(status=500, text=str(e))

        except Exception as e:
            logger.error(f"Критическая ошибка в обработчике webhook: {e}", exc_info=True)
            return web.Response(status=500, text=str(e))