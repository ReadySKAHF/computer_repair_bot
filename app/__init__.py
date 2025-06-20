"""
Telegram Bot для сервиса ремонта компьютеров

Модульный бот с ИИ консультантом, системой заказов и отзывов.
Использует aiogram 3.x, SQLite, Google Gemini AI.

Основные модули:
- handlers: обработчики сообщений и callback'ов
- database: работа с базой данных
- services: бизнес-логика приложения
- keyboards: клавиатуры для интерфейса
- utils: вспомогательные функции и константы

Автор: Клецков А. П.
"""

__version__ = "1.0.0"
__author__ = "Computer Repair Bot Team"
__description__ = "Telegram Bot для сервиса ремонта компьютеров"

# Экспортируем основные классы для удобства импорта
from .config import ConfigLoader, BotConfig
from .database.connection import DatabaseManager
from .database.queries import DatabaseQueries
from .services.ai_service import AIConsultationService
from .services.validation_service import ValidationService
from .services.order_service import OrderService

__all__ = [
    "ConfigLoader", 
    "BotConfig",
    "DatabaseManager",
    "DatabaseQueries", 
    "AIConsultationService",
    "ValidationService",
    "OrderService"
]