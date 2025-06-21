"""
Модуль конфигурации бота
"""
import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class BotConfig:
    """Конфигурация бота"""
    bot_token: str
    gemini_api_key: str
    db_path: str = "repair_bot.db"
    log_level: str = "INFO"
    max_services_per_order: int = 10
    max_message_length: int = 1000
    rate_limit_messages: int = 30
    rate_limit_window: int = 60
    admin_ids: List[int] = None
    
    def __post_init__(self):
        if self.admin_ids is None:
            self.admin_ids = []
    
    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь админом"""
        return user_id in self.admin_ids


class ConfigLoader:
    """Загрузчик конфигурации с валидацией"""
    
    @staticmethod
    def load_from_file(config_path: str = "config.txt") -> BotConfig:
        """Загрузка конфигурации из файла"""
        config_data = {}
        
        try:
            if not Path(config_path).exists():
                raise FileNotFoundError(f"Файл конфигурации {config_path} не найден")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        try:
                            key, value = line.split('=', 1)
                            config_data[key.strip()] = value.strip()
                        except ValueError:
                            logging.warning(f"Некорректная строка {line_num} в {config_path}: {line}")
            
            # Валидация обязательных параметров
            required_keys = ['BOT_TOKEN', 'GEMINI_API_KEY']
            missing_keys = []
            
            for key in required_keys:
                if key not in config_data or not config_data[key] or config_data[key] in ['YOUR_BOT_TOKEN_HERE', 'YOUR_GEMINI_API_KEY_HERE']:
                    missing_keys.append(key)
            
            if missing_keys:
                raise ValueError(f"Не настроены обязательные параметры: {', '.join(missing_keys)}")
            
            # Создаем объект конфигурации
            return BotConfig(
                bot_token=config_data['BOT_TOKEN'],
                gemini_api_key=config_data['GEMINI_API_KEY'],
                db_path=config_data.get('DB_PATH', 'repair_bot.db'),
                log_level=config_data.get('LOG_LEVEL', 'INFO'),
                max_services_per_order=int(config_data.get('MAX_SERVICES_PER_ORDER', 10)),
                max_message_length=int(config_data.get('MAX_MESSAGE_LENGTH', 1000)),
                rate_limit_messages=int(config_data.get('RATE_LIMIT_MESSAGES', 30)),
                rate_limit_window=int(config_data.get('RATE_LIMIT_WINDOW', 60)),
                admin_ids=[int(x.strip()) for x in config_data.get('ADMIN_IDS', '').split(',') if x.strip().isdigit()]
            )
            
        except FileNotFoundError:
            ConfigLoader._create_example_config(config_path)
            raise FileNotFoundError(
                f"Файл {config_path} не найден! Создан образец конфигурации. "
                "Заполните его и перезапустите бота."
            )
        except Exception as e:
            logging.error(f"Ошибка загрузки конфигурации: {e}")
            raise
    
    @staticmethod
    def _create_example_config(config_path: str):
        """Создание примера конфигурации"""
        example_config = """# Конфигурация бота для ремонта компьютеров
# Получить токен бота: https://t.me/BotFather
BOT_TOKEN=7913442149:AAFwBeMEd9kz3dFbDylO-e-fhcNO6XzM51Q

# Получить API ключ Gemini: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=AIzaSyDnt1hWgcID2HWW7_ccllAWwhOpL5Mo6aE

# Дополнительные настройки (необязательно)
DB_PATH=repair_bot.db
LOG_LEVEL=INFO
MAX_SERVICES_PER_ORDER=10
MAX_MESSAGE_LENGTH=1000
RATE_LIMIT_MESSAGES=30
RATE_LIMIT_WINDOW=60

# ID администраторов (через запятую) - ваши Telegram ID
ADMIN_IDS=716639474,1003589165
"""
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(example_config)


def setup_logging(config: BotConfig):
    """Настройка логирования"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Настройка уровня логирования
    level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # Настройка для файла и консоли
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.FileHandler('bot.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('repair_bot')


def validate_config(config: BotConfig) -> bool:
    """Валидация конфигурации"""
    errors = []
    
    if not config.bot_token or len(config.bot_token) < 40:
        errors.append("Некорректный токен бота")
    
    if not config.gemini_api_key or len(config.gemini_api_key) < 30:
        errors.append("Некорректный API ключ Gemini")
    
    if config.max_services_per_order <= 0 or config.max_services_per_order > 50:
        errors.append("max_services_per_order должно быть от 1 до 50")
    
    if config.max_message_length <= 0 or config.max_message_length > 4000:
        errors.append("max_message_length должно быть от 1 до 4000")
    
    if errors:
        for error in errors:
            logging.error(f"Ошибка конфигурации: {error}")
        return False
    
    return True