from dataclasses import dataclass
from os import getenv
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # Bot settings
    BOT_TOKEN: str = getenv('BOT_TOKEN', '')
    DATABASE_URL: str = getenv('DATABASE_URL', '')
    CLOTHOFF_API_KEY: str = getenv('CLOTHOFF_API_KEY', '')
    WEBHOOK_URL: str = getenv('WEBHOOK_URL', 'https://teststars-production.up.railway.app')  # Дефолтное значение
    CHANNEL_ID: str = getenv('CHANNEL_ID', '')

    # Формируем полный URL для webhook'а ClothOff
    @property
    def clothoff_webhook_url(self) -> str:
        base_url = self.WEBHOOK_URL.rstrip('/')
        return f"{base_url}/clothoff/webhook"

    # Credit packages
    PACKAGES = [
        {
            "id": 1,
            "credits": 4,
            "price": 500,
            "description": "4 генерации (125₽/шт)"
        },
        {
            "id": 2,
            "credits": 8,
            "price": 700,
            "description": "8 генераций (87.5₽/шт)"
        },
        {
            "id": 3,
            "credits": 16,
            "price": 1120,
            "description": "16 генераций (70₽/шт)"
        },
        {
            "id": 4,
            "credits": 50,
            "price": 2500,
            "description": "50 генераций (50₽/шт)"
        }
    ]

    # API URLs
    CLOTHOFF_API_URL: str = 'https://public-api.clothoff.net'

    def __post_init__(self):
        # Проверяем только критически важные переменные
        required_vars = {
            'BOT_TOKEN': self.BOT_TOKEN,
            'DATABASE_URL': self.DATABASE_URL,
            'CLOTHOFF_API_KEY': self.CLOTHOFF_API_KEY
        }
        
        missing = [name for name, value in required_vars.items() if not value]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

        # Логируем значения переменных окружения (без секретов)
        print(f"Loaded config with WEBHOOK_URL: {self.WEBHOOK_URL}")
        print(f"ClothOff webhook URL: {self.clothoff_webhook_url}")

config = Config()