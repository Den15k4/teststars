import aiohttp
import logging
from typing import Dict, Any
import time
from bot.config import config

logger = logging.getLogger(__name__)

class ClothOffAPI:
    def __init__(self):
        self.api_key = config.CLOTHOFF_API_KEY
        self.base_url = config.CLOTHOFF_API_URL
        self.webhook_url = config.clothoff_webhook_url
        logger.info(f"Initialized ClothOffAPI with webhook URL: {self.webhook_url}")

    async def process_image(self, image_data: bytes, user_id: int) -> Dict[str, Any]:
        """Отправка изображения на обработку"""
        try:
            id_gen = f"user_{user_id}_{int(time.time())}"
            
            # Добавляем id_gen в webhook URL
            webhook_url = f"{self.webhook_url}?id_gen={id_gen}"
            
            # Формируем данные для отправки
            form_data = aiohttp.FormData()
            form_data.add_field('cloth', 'naked')
            form_data.add_field(
                'image',
                image_data,
                filename='image.jpg',
                content_type='image/jpeg'
            )
            form_data.add_field('id_gen', id_gen)
            form_data.add_field('webhook', webhook_url)

            logger.info(f"Sending request to ClothOff API with webhook: {webhook_url}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.base_url}/undress',
                    data=form_data,
                    headers={
                        'x-api-key': self.api_key,
                        'accept': 'application/json'
                    }
                ) as response:
                    response_data = await response.json()
                    logger.info(f"ClothOff API response: {response_data}")

                    if response.status != 200:
                        error_msg = response_data.get('error', 'Unknown error')
                        if error_msg == 'Insufficient balance':
                            raise ValueError('INSUFFICIENT_BALANCE')
                        raise ValueError(f'API Error: {error_msg}')

                    return {
                        'queue_time': response_data.get('queue_time', 0),
                        'queue_num': response_data.get('queue_num', 0),
                        'api_balance': response_data.get('api_balance', 0),
                        'id_gen': id_gen
                    }

        except Exception as e:
            logger.error(f"Error in process_image: {e}")
            raise