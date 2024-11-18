import aiohttp
import logging
from typing import Dict, Any, Tuple
import time
import asyncio
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
            
            # Формируем webhook URL с id_gen как query параметром
            webhook_url = f"{self.webhook_url}?id_gen={id_gen}"
            logger.info(f"Using webhook URL with id_gen: {webhook_url}")

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

            # Отправляем запрос с повторными попытками
            max_retries = 3
            retry_delay = 1  # секунды

            for attempt in range(max_retries):
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f'{self.base_url}/undress',
                            data=form_data,
                            headers={
                                'x-api-key': self.api_key,
                                'accept': 'application/json'
                            },
                            timeout=30  # таймаут 30 секунд
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
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt == max_retries - 1:  # если это последняя попытка
                        raise ValueError(f"Network error after {max_retries} attempts: {e}")
                    logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                    await asyncio.sleep(retry_delay)

        except Exception as e:
            logger.error(f"Error in process_image: {e}")
            raise

    async def verify_image(self, image_data: bytes) -> Tuple[bool, str]:
        """Проверка изображения перед отправкой на обработку"""
        try:
            # Проверяем размер
            if len(image_data) > 10 * 1024 * 1024:  # 10 MB
                return False, "Размер изображения слишком большой. Максимум 10 MB."

            # Проверяем формат (простая проверка заголовков файла)
            if not (image_data.startswith(b'\xff\xd8\xff') or  # JPEG
                   image_data.startswith(b'\x89PNG\r\n\x1a\n')):  # PNG
                return False, "Неподдерживаемый формат изображения. Используйте JPEG или PNG."

            return True, ""

        except Exception as e:
            logger.error(f"Error in verify_image: {e}")
            return False, "Ошибка при проверке изображения."