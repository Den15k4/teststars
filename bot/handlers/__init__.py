from aiogram import Dispatcher
from .base import router as base_router
from .images import router as images_router
import logging

logger = logging.getLogger(__name__)

async def setup_handlers(dp: Dispatcher, db) -> None:
    """Регистрация всех обработчиков"""
    try:
        # Регистрация middleware для передачи db
        from aiogram import BaseMiddleware
        from typing import Any, Awaitable, Callable, Dict
        from aiogram.types import TelegramObject

        class DatabaseMiddleware(BaseMiddleware):
            def __init__(self, database):
                self.database = database
                super().__init__()

            async def __call__(
                self,
                handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                event: TelegramObject,
                data: Dict[str, Any]
            ) -> Any:
                data["db"] = self.database
                return await handler(event, data)

        # Регистрируем middleware
        dp.update.middleware.register(DatabaseMiddleware(db))
        logger.info("Database middleware registered")

        # Регистрируем роутеры
        dp.include_router(base_router)
        dp.include_router(images_router)
        logger.info("Routers registered")

    except Exception as e:
        logger.error(f"Error in setup_handlers: {e}")
        raise