from aiohttp import web
import logging
from typing import Dict, Any
from ..database.models import Database
from ..keyboards.markups import Keyboards

logger = logging.getLogger(__name__)

class ClothOffWebhook:
    def __init__(self, bot, db: Database):
        self.bot = bot
        self.db = db

    async def handle_webhook(self, request: web.Request) -> web.Response:
        """Обработчик вебхуков от ClothOff API"""
        try:
            # Получаем данные
            data = await request.json()
            logger.info(f"Received webhook from ClothOff: {data}")

            # Извлекаем user_id из id_gen
            user_id = int(data['id_gen'].split('_')[1])
            
            # Получаем пользователя
            user = await self.db.get_user(user_id)
            if not user:
                raise Exception(f"User not found for task {data['id_gen']}")

            # Обработка ошибок
            if data.get('status') == '500' or data.get('img_message') or data.get('img_message_2'):
                error_msg = data.get('img_message') or data.get('img_message_2') or 'Unknown error'
                
                # Особая обработка ошибки возраста
                if 'Age is too young' in error_msg:
                    await self.bot.send_message(
                        user_id,
                        "🔞 На изображении обнаружен человек младше 18 лет.\n"
                        "Обработка таких изображений запрещена.",
                        reply_markup=Keyboards.main_menu()
                    )
                else:
                    await self.bot.send_message(
                        user_id,
                        f"❌ Не удалось обработать изображение:\n{error_msg}",
                        reply_markup=Keyboards.main_menu()
                    )

                # Возвращаем кредит
                await self.db.return_credit(user_id)
                await self.db.clear_pending_task(user_id)

            # Обработка успешного результата
            else:
                image_data = None
                if data.get('result'):
                    image_data = data['result']
                elif request.has_body and await request.read():
                    image_data = await request.read()

                if image_data:
                    await self.bot.send_photo(
                        user_id,
                        photo=image_data,
                        caption=(
                            "✨ Мы её раздели! Любуйся!\n"
                            "Чтобы обработать новое фото, нажмите кнопку 💫 Начать обработку"
                        ),
                        reply_markup=Keyboards.main_menu()
                    )
                    await self.db.clear_pending_task(user_id)
                else:
                    raise Exception("No image data in webhook response")

            return web.Response(
                text='{"status":"success"}',
                content_type='application/json'
            )

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return web.Response(
                status=500,
                text='{"status":"error","message":"Internal server error"}',
                content_type='application/json'
            )
