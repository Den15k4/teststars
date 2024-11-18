from aiohttp import web
import logging

logger = logging.getLogger(__name__)

class ClothOffWebhook:
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Обработчик вебхуков от ClothOff API"""
        try:
            # Читаем тело запроса как bytes
            body = await request.read()
            logger.info(f"Received webhook, body size: {len(body)} bytes")

            if len(body) > 50 * 1024 * 1024:  # 50 MB
                raise web.HTTPRequestEntityTooLarge(
                    max_size=50 * 1024 * 1024,
                    actual_size=len(body)
                )

            # Если это JSON
            if request.content_type == 'application/json':
                data = await request.json()
                logger.info(f"Webhook data: {data}")

                # Извлекаем user_id из id_gen
                user_id = int(data['id_gen'].split('_')[1])
                
                # Получаем пользователя
                user = await self.db.get_user(user_id)
                if not user:
                    raise ValueError(f"User not found for task {data['id_gen']}")

                # Обработка ошибок
                if data.get('status') == '500' or data.get('img_message') or data.get('img_message_2'):
                    error_msg = data.get('img_message') or data.get('img_message_2') or 'Unknown error'
                    
                    # Особая обработка ошибки возраста
                    if 'Age is too young' in error_msg:
                        await self.bot.send_message(
                            user_id,
                            "🔞 На изображении обнаружен человек младше 18 лет.\n"
                            "Обработка таких изображений запрещена.",
                            reply_markup=self.keyboards.main_menu()
                        )
                    else:
                        await self.bot.send_message(
                            user_id,
                            f"❌ Не удалось обработать изображение:\n{error_msg}",
                            reply_markup=self.keyboards.main_menu()
                        )

                    # Возвращаем кредит
                    await self.db.return_credit(user_id)
                    await self.db.clear_pending_task(user_id)

                # Обработка успешного результата
                else:
                    image_data = data.get('result', body)
                    if image_data:
                        await self.bot.send_photo(
                            user_id,
                            photo=image_data,
                            caption=(
                                "✨ Мы её раздели! Любуйся!\n"
                                "Чтобы обработать новое фото, нажмите кнопку 💫 Начать обработку"
                            ),
                            reply_markup=self.keyboards.main_menu()
                        )
                        await self.db.clear_pending_task(user_id)
                    else:
                        raise ValueError("No image data in webhook response")

            return web.Response(text='{"status":"success"}')

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return web.Response(status=500, text=str(e))