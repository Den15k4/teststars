from dataclasses import dataclass
from os import getenv
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

@dataclass
class _Config:
    """Конфигурация бота"""
    # Bot settings
    BOT_TOKEN: str = getenv('BOT_TOKEN', '')
    DATABASE_URL: str = getenv('DATABASE_URL', '')
    CLOTHOFF_API_KEY: str = getenv('CLOTHOFF_API_KEY', '')
    WEBHOOK_URL: str = getenv('WEBHOOK_URL', 'https://teststars-production.up.railway.app')
    CHANNEL_ID: str = getenv('CHANNEL_ID', '')

    # API URLs
    CLOTHOFF_API_URL: str = 'https://public-api.clothoff.net'
    
    def __post_init__(self):
        # Проверяем обязательные переменные окружения
        required_vars = {
            'BOT_TOKEN': self.BOT_TOKEN,
            'DATABASE_URL': self.DATABASE_URL,
            'CLOTHOFF_API_KEY': self.CLOTHOFF_API_KEY,
            'WEBHOOK_URL': self.WEBHOOK_URL
        }
        
        missing = [name for name, value in required_vars.items() if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Нормализуем URL
        self.WEBHOOK_URL = self.WEBHOOK_URL.rstrip('/')

        print(f"Loaded config with WEBHOOK_URL: {self.WEBHOOK_URL}")
        print(f"ClothOff webhook URL: {self.clothoff_webhook_url}")

    @property
    def clothoff_webhook_url(self) -> str:
        """Формирование URL для webhook'а ClothOff"""
        return f"{self.WEBHOOK_URL}/clothoff/webhook"

# Создаем единственный экземпляр конфигурации
config = _Config()