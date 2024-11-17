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
    WEBHOOK_URL: str = getenv('WEBHOOK_URL', '')
    CHANNEL_ID: str = getenv('CHANNEL_ID', '')

    # Credit packages
    PACKAGES = [
        {
            "id": 1,
            "credits": 4,
            "price": 500,  # 500 рублей
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
        if not all([self.BOT_TOKEN, self.DATABASE_URL, self.CLOTHOFF_API_KEY]):
            raise ValueError("Missing required environment variables!")

config = Config()
