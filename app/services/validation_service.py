"""
Сервис валидации данных
"""
from typing import Tuple, Any
from ..utils.validators import (
    validate_phone, validate_name, validate_address,
    validate_review_comment, validate_support_message,
    validate_ai_problem, validate_rating, sanitize_input, format_phone_number
)
from ..utils.constants import ERROR_MESSAGES


class ValidationService:
    """Сервис для валидации пользовательских данных"""
    
    @staticmethod
    def validate_user_registration_data(name: str, phone: str, address: str) -> Tuple[bool, str, dict]:
        """
        Валидация данных регистрации пользователя
        
        Args:
            name: Имя пользователя
            phone: Телефон пользователя
            address: Адрес пользователя
            
        Returns:
            Tuple[bool, str, dict]: (успех, сообщение об ошибке, очищенные данные)
        """
        # Очищаем входные данные
        name = sanitize_input(name)
        phone = sanitize_input(phone)
        address = sanitize_input(address)
        
        # Валидация имени
        is_valid, error_msg = validate_name(name)
        if not is_valid:
            return False, ERROR_MESSAGES['INVALID_NAME'], {}
        
        # Валидация телефона
        is_valid, error_msg = validate_phone(phone)
        if not is_valid:
            return False, ERROR_MESSAGES['INVALID_PHONE'], {}
        
        # Валидация адреса
        is_valid, error_msg = validate_address(address)
        if not is_valid:
            return False, ERROR_MESSAGES['INVALID_ADDRESS'], {}
        
        # Возвращаем очищенные данные
        cleaned_data = {
            'name': name.strip(),
            'phone': format_phone_number(phone),
            'address': address.strip()
        }
        
        return True, "", cleaned_data
    
    @staticmethod
    def validate_profile_update_data(field: str, value: str) -> Tuple[bool, str, str]:
        """
        Валидация данных обновления профиля
        
        Args:
            field: Поле для обновления (name, phone, address)
            value: Новое значение
            
        Returns:
            Tuple[bool, str, str]: (успех, сообщение об ошибке, очищенное значение)
        """
        # Очищаем входные данные
        value = sanitize_input(value)
        
        if field == 'name':
            is_valid, error_msg = validate_name(value)
            if not is_valid:
                return False, ERROR_MESSAGES['INVALID_NAME'], ""
            return True, "", value.strip()
            
        elif field == 'phone':
            is_valid, error_msg = validate_phone(value)
            if not is_valid:
                return False, ERROR_MESSAGES['INVALID_PHONE'], ""
            return True, "", format_phone_number(value)
            
        elif field == 'address':
            is_valid, error_msg = validate_address(value)
            if not is_valid:
                return False, ERROR_MESSAGES['INVALID_ADDRESS'], ""
            return True, "", value.strip()
        
        return False, "Недопустимое поле для обновления", ""
    
    @staticmethod
    def validate_review_data(rating: int, comment: str) -> Tuple[bool, str, dict]:
        """
        Валидация данных отзыва
        
        Args:
            rating: Оценка (1-5)
            comment: Комментарий
            
        Returns:
            Tuple[bool, str, dict]: (успех, сообщение об ошибке, очищенные данные)
        """
        # Валидация рейтинга
        is_valid, error_msg = validate_rating(rating)
        if not is_valid:
            return False, f"❌ Некорректная оценка: {error_msg}", {}
        
        # Очищаем и валидируем комментарий
        comment = sanitize_input(comment)
        is_valid, error_msg = validate_review_comment(comment)
        if not is_valid:
            return False, ERROR_MESSAGES['INVALID_REVIEW'], {}
        
        cleaned_data = {
            'rating': rating,
            'comment': comment.strip()
        }
        
        return True, "", cleaned_data
    
    @staticmethod
    def validate_support_request_data(message: str) -> Tuple[bool, str, str]:
        """
        Валидация данных обращения в поддержку
        
        Args:
            message: Сообщение в поддержку
            
        Returns:
            Tuple[bool, str, str]: (успех, сообщение об ошибке, очищенное сообщение)
        """
        # Очищаем входные данные
        message = sanitize_input(message)
        
        # Валидация сообщения
        is_valid, error_msg = validate_support_message(message)
        if not is_valid:
            return False, ERROR_MESSAGES['INVALID_SUPPORT_MESSAGE'], ""
        
        return True, "", message.strip()
    
    @staticmethod
    def validate_ai_problem_data(problem: str) -> Tuple[bool, str, str]:
        """
        Валидация данных проблемы для ИИ
        
        Args:
            problem: Описание проблемы
            
        Returns:
            Tuple[bool, str, str]: (успех, сообщение об ошибке, очищенное описание)
        """
        # Очищаем входные данные
        problem = sanitize_input(problem)
        
        # Валидация описания проблемы
        is_valid, error_msg = validate_ai_problem(problem)
        if not is_valid:
            return False, ERROR_MESSAGES['INVALID_AI_PROBLEM'], ""
        
        return True, "", problem.strip()
    
    @staticmethod
    def validate_service_ids(service_ids: list, max_services: int = 10) -> Tuple[bool, str, list]:
        """
        Валидация списка ID услуг
        
        Args:
            service_ids: Список ID услуг
            max_services: Максимальное количество услуг
            
        Returns:
            Tuple[bool, str, list]: (успех, сообщение об ошибке, очищенный список)
        """
        if not service_ids:
            return False, "Не выбрано ни одной услуги", []
        
        if len(service_ids) > max_services:
            return False, f"Максимальное количество услуг: {max_services}", []
        
        # Проверяем, что все ID - числа
        try:
            cleaned_ids = [int(sid) for sid in service_ids if isinstance(sid, (int, str)) and str(sid).isdigit()]
        except (ValueError, TypeError):
            return False, "Некорректные ID услуг", []
        
        if len(cleaned_ids) != len(service_ids):
            return False, "Некорректные ID услуг", []
        
        return True, "", cleaned_ids
    
    @staticmethod
    def validate_date_time(date_str: str, time_str: str) -> Tuple[bool, str, dict]:
        """
        Валидация даты и времени заказа
        
        Args:
            date_str: Дата в формате YYYY-MM-DD
            time_str: Время в формате HH:MM
            
        Returns:
            Tuple[bool, str, dict]: (успех, сообщение об ошибке, проверенные данные)
        """
        from datetime import datetime, timedelta
        
        try:
            # Проверяем формат даты
            order_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            today = datetime.now().date()
            
            # Проверяем, что дата не в прошлом
            if order_date < today:
                return False, "Нельзя выбрать дату в прошлом", {}
            
            # Проверяем, что дата не слишком далеко в будущем (например, не более 30 дней)
            max_date = today + timedelta(days=30)
            if order_date > max_date:
                return False, "Дата слишком далеко в будущем", {}
            
            # Проверяем формат времени
            order_time = datetime.strptime(time_str, '%H:%M').time()
            
            validated_data = {
                'date': date_str,
                'time': time_str,
                'date_obj': order_date,
                'time_obj': order_time
            }
            
            return True, "", validated_data
            
        except ValueError as e:
            return False, "Некорректный формат даты или времени", {}
    
    @staticmethod
    def validate_order_data(user_id: int, master_id: int, address: str, 
                           date_str: str, time_str: str, service_ids: list) -> Tuple[bool, str, dict]:
        """
        Комплексная валидация данных заказа
        
        Args:
            user_id: ID пользователя
            master_id: ID мастера
            address: Адрес
            date_str: Дата заказа
            time_str: Время заказа
            service_ids: Список ID услуг
            
        Returns:
            Tuple[bool, str, dict]: (успех, сообщение об ошибке, проверенные данные)
        """
        # Проверяем user_id
        if not isinstance(user_id, int) or user_id <= 0:
            return False, "Некорректный ID пользователя", {}
        
        # Проверяем master_id
        if not isinstance(master_id, int) or master_id <= 0:
            return False, "Некорректный ID мастера", {}
        
        # Валидируем адрес
        address = sanitize_input(address)
        is_valid, error_msg = validate_address(address)
        if not is_valid:
            return False, ERROR_MESSAGES['INVALID_ADDRESS'], {}
        
        # Валидируем дату и время
        is_valid, error_msg, datetime_data = ValidationService.validate_date_time(date_str, time_str)
        if not is_valid:
            return False, error_msg, {}
        
        # Валидируем список услуг
        is_valid, error_msg, cleaned_service_ids = ValidationService.validate_service_ids(service_ids)
        if not is_valid:
            return False, error_msg, {}
        
        validated_data = {
            'user_id': user_id,
            'master_id': master_id,
            'address': address.strip(),
            'order_date': datetime_data['date'],
            'order_time': datetime_data['time'],
            'service_ids': cleaned_service_ids
        }
        
        return True, "", validated_data
    
    @staticmethod
    def validate_message_length(message: str, max_length: int = 4000) -> Tuple[bool, str]:
        """
        Валидация длины сообщения
        
        Args:
            message: Сообщение для проверки
            max_length: Максимальная длина
            
        Returns:
            Tuple[bool, str]: (успех, сообщение об ошибке)
        """
        if not message:
            return False, "Сообщение не может быть пустым"
        
        if len(message) > max_length:
            return False, f"Сообщение не может быть длиннее {max_length} символов"
        
        return True, ""