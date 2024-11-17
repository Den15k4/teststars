import aiohttp
import logging
from typing import Dict, Any, Optional
import time
from bot.config import config

logger = logging.getLogger(__name__)

class ClothOffAPI:
    def __init__(self):
        self.api_key = config.CLOTHOFF_API_KEY
        self.base_url = config.CLOTHOFF_API_URL
        self.webhook_url = f"{config.WEBHOOK_URL}/webhook"

    async def process_image(self, image_data: bytes, user_id: int) -> Dict[str, Any]:
        """Отправка изображения на обработку"""
        try:
            # Формируем данные для отправки
            form_data = aiohttp.FormData()
            form_data.add_field('cloth', 'naked')
            form_data.add_field(
                'image',
                image_data,
                filename='image.jpg',
                content_type='image/jpeg'
            )
            
            id_gen = f"user_{user_id}_{int(time.time())}"
            form_data.add_field('id_gen', id_gen)
            form_data.add_field('webhook', self.webhook_url)

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/undress',
                    data=form_data,
                    headers={
                        'x-api-key': self.api_key,
                        'accept': 'application/json'
                    }
                ) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        error_msg = error_data.get('error', 'Unknown error')
                        if error_msg == 'Insufficient balance':
                            raise ValueError('INSUFFICIENT_BALANCE')
                        raise ValueError(f'API Error: {error_msg}')

                    data = await response.json()
                    return {
                        'queue_time': data.get('queue_time', 0),
                        'queue_num': data.get('queue_num', 0),
                        'api_balance': data.get('api_balance', 0),
                        'id_gen': id_gen
                    }

        except Exception as e:
            logger.error(f"Error in process_image: {e}")
            raise

    async def check_age(self, image_data: bytes) -> bool:
        """Проверка возрастных ограничений"""
        try:
            form_data = aiohttp.FormData()
            form_data.add_field(
                'image',
                image_data,
                filename='check.jpg',
                content_type='image/jpeg'
            )

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/check_age',
                    data=form_data,
                    headers={
                        'x-api-key': self.api_key,
                        'accept': 'application/json'
                    }
                ) as response:
                    if response.status != 200:
                        return True  # В случае ошибки пропускаем проверку

                    data = await response.json()
                    age = data.get('age', 0)
                    return age >= 18

        except Exception as e:
            logger.error(f"Error in check_age: {e}")
            return True  # В случае ошибки пропускаем проверку