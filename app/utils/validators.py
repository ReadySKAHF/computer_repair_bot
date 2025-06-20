"""
Модуль валидации пользовательского ввода
"""
import re
from typing import Tuple


def validate_phone(phone: str) -> Tuple[bool, str]:
    """
    Проверка корректности номера телефона
    
    Args:
        phone: Номер телефона для проверки
        
    Returns:
        Tuple[bool, str]: (True/False, сообщение об ошибке)
    """
    if not phone or not phone.strip():
        return False, "Номер телефона не может быть пустым"
    
    # Паттерн для российских номеров
    pattern = r'^(\+7|8|7)?[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
    
    if not re.match(pattern, phone.strip()):
        return False, "Некорректный формат номера телефона"
    
    return True, ""


def validate_name(name: str) -> Tuple[bool, str]:
    """
    Проверка корректности имени
    
    Args:
        name: Имя для проверки
        
    Returns:
        Tuple[bool, str]: (True/False, сообщение об ошибке)
    """
    if not name or not name.strip():
        return False, "Имя не может быть пустым"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Имя должно содержать минимум 2 символа"
    
    if len(name) > 50:
        return False, "Имя не может быть длиннее 50 символов"
    
    # Только буквы, пробелы, дефисы
    if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-]+$', name):
        return False, "Имя может содержать только буквы, пробелы и дефисы"
    
    return True, ""


def validate_address(address: str) -> Tuple[bool, str]:
    """
    Проверка корректности адреса
    
    Args:
        address: Адрес для проверки
        
    Returns:
        Tuple[bool, str]: (True/False, сообщение об ошибке)
    """
    if not address or not address.strip():
        return False, "Адрес не может быть пустым"
    
    address = address.strip()
    
    if len(address) < 10:
        return False, "Адрес должен содержать минимум 10 символов"
    
    if len(address) > 200:
        return False, "Адрес не может быть длиннее 200 символов"
    
    return True, ""


def validate_review_comment(comment: str) -> Tuple[bool, str]:
    """
    Проверка корректности комментария отзыва
    
    Args:
        comment: Комментарий для проверки
        
    Returns:
        Tuple[bool, str]: (True/False, сообщение об ошибке)
    """
    if not comment or not comment.strip():
        return False, "Комментарий не может быть пустым"
    
    comment = comment.strip()
    
    if len(comment) < 5:
        return False, "Комментарий должен содержать минимум 5 символов"
    
    if len(comment) > 500:
        return False, "Комментарий не может быть длиннее 500 символов"
    
    return True, ""


def validate_support_message(message: str) -> Tuple[bool, str]:
    """
    Проверка корректности сообщения в поддержку
    
    Args:
        message: Сообщение для проверки
        
    Returns:
        Tuple[bool, str]: (True/False, сообщение об ошибке)
    """
    if not message or not message.strip():
        return False, "Сообщение не может быть пустым"
    
    message = message.strip()
    
    if len(message) < 10:
        return False, "Сообщение должно содержать минимум 10 символов"
    
    if len(message) > 1000:
        return False, "Сообщение не может быть длиннее 1000 символов"
    
    return True, ""


def validate_ai_problem(problem: str) -> Tuple[bool, str]:
    """
    Проверка корректности описания проблемы для ИИ
    
    Args:
        problem: Описание проблемы для проверки
        
    Returns:
        Tuple[bool, str]: (True/False, сообщение об ошибке)
    """
    if not problem or not problem.strip():
        return False, "Описание проблемы не может быть пустым"
    
    problem = problem.strip()
    
    if len(problem) < 10:
        return False, "Описание проблемы должно содержать минимум 10 символов"
    
    if len(problem) > 1000:
        return False, "Описание проблемы не может быть длиннее 1000 символов"
    
    return True, ""


def sanitize_input(text: str) -> str:
    """
    Очистка пользовательского ввода от потенциально опасных символов
    
    Args:
        text: Текст для очистки
        
    Returns:
        str: Очищенный текст
    """
    if not text:
        return ""
    
    # Удаляем лишние пробелы
    text = text.strip()
    
    # Удаляем потенциально опасные символы
    text = re.sub(r'[<>"\']', '', text)
    
    # Ограничиваем длину
    return text[:1000]


def validate_rating(rating: int) -> Tuple[bool, str]:
    """
    Проверка корректности оценки
    
    Args:
        rating: Оценка для проверки
        
    Returns:
        Tuple[bool, str]: (True/False, сообщение об ошибке)
    """
    if not isinstance(rating, int):
        return False, "Оценка должна быть числом"
    
    if rating < 1 or rating > 5:
        return False, "Оценка должна быть от 1 до 5"
    
    return True, ""


def format_phone_number(phone: str) -> str:
    """
    Форматирование номера телефона к единому виду
    
    Args:
        phone: Номер телефона
        
    Returns:
        str: Отформатированный номер
    """
    # Удаляем все символы кроме цифр
    digits = re.sub(r'\D', '', phone)
    
    # Если номер начинается с 8, заменяем на 7
    if digits.startswith('8') and len(digits) == 11:
        digits = '7' + digits[1:]
    
    # Если номер начинается с 7 и содержит 11 цифр
    if digits.startswith('7') and len(digits) == 11:
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    
    # Возвращаем как есть, если не удалось отформатировать
    return phone