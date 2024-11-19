from aiogram import Dispatcher
from .base import setup_base_handlers
from .images import setup_image_handlers

async def setup_handlers(dp: Dispatcher, db) -> None:
    """Регистрация всех обработчиков"""
    await setup_base_handlers(dp, db)
    await setup_image_handlers(dp, db)