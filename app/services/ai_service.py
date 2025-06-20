"""
Сервис для работы с ИИ консультациями
"""
import logging
import re
from typing import List, Dict, Tuple, Optional
import google.generativeai as genai
from ..utils.constants import AI_PROBLEM_PATTERNS


class AIConsultationService:
    """Сервис для ИИ консультаций"""
    
    def __init__(self, api_key: str):
        """Инициализация сервиса"""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.is_available = True
            logging.info("ИИ сервис инициализирован успешно")
        except Exception as e:
            logging.error(f"Ошибка инициализации ИИ сервиса: {e}")
            self.is_available = False
            self.model = None
    
    def _analyze_problem_keywords(self, problem_text: str) -> Tuple[str, List[int], str]:
        """Анализ проблемы по ключевым словам"""
        problem_lower = problem_text.lower()
        
        # Подсчитываем совпадения для каждой категории
        category_scores = {}
        for category, data in AI_PROBLEM_PATTERNS.items():
            score = sum(1 for keyword in data['keywords'] if keyword in problem_lower)
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return 'general', [1, 2, 9], 'Рекомендуется базовая диагностика системы.'
        
        # Выбираем категорию с наибольшим количеством совпадений
        best_category = max(category_scores.keys(), key=lambda k: category_scores[k])
        pattern_data = AI_PROBLEM_PATTERNS[best_category]
        
        return best_category, pattern_data['services'], pattern_data['description']
    
    def _create_ai_prompt(self, problem_text: str, services_list: str) -> str:
        """Создание промпта для ИИ"""
        return f"""Ты - профессиональный консультант сервиса по ремонту компьютеров. 

ТВОЯ РОЛЬ:
- Проанализируй проблему клиента и дай профессиональную оценку
- Рекомендуй ТОЛЬКО услуги из предоставленного списка
- Объясни, как каждая рекомендуемая услуга поможет решить проблему
- Укажи ID услуг в формате [ID: X] после каждой рекомендации

ДОСТУПНЫЕ УСЛУГИ:
{services_list}

ФОРМАТ ОТВЕТА:
1. Краткий анализ проблемы (2-3 предложения)
2. Список рекомендуемых услуг с объяснением
3. Примерная последовательность выполнения (если важно)

ВАЖНЫЕ ПРАВИЛА:
- Используй только услуги из списка выше
- Будь конкретным и профессиональным
- Объясни техническую сторону простым языком
- Не рекомендуй больше 5 услуг за раз
- Обязательно укажи [ID: X] для каждой рекомендуемой услуги

Проблема клиента: {problem_text}"""
    
    async def get_ai_recommendation(self, problem_text: str, all_services: List[Dict]) -> Dict:
        """Получение рекомендации от ИИ"""
        if not self.is_available or not self.model:
            return {
                'success': False,
                'ai_response': None,
                'recommended_services': [],
                'error': 'ИИ сервис недоступен'
            }
        
        try:
            # Формируем список услуг для промпта
            services_list = ""
            for service in all_services:
                if isinstance(service, dict):
                    # Новый формат (dict)
                    service_id = service['id']
                    name = service['name']
                    price = service['price']
                    duration = service['duration_minutes']
                    description = service['description']
                else:
                    # Старый формат (tuple)
                    service_id, name, price, duration, description = service[:5]
                
                services_list += f"ID: {service_id}, {name}, {price}₽, {duration} мин - {description}\n"
            
            # Создаем и отправляем промпт
            prompt = self._create_ai_prompt(problem_text, services_list)
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("Пустой ответ от ИИ")
            
            # Извлекаем ID услуг из ответа
            service_ids = re.findall(r'\[ID:\s*(\d+)\]', response.text)
            recommended_services = [int(sid) for sid in service_ids if sid.isdigit()]
            
            # Ограничиваем количество рекомендаций
            recommended_services = recommended_services[:5]
            
            logging.info(f"ИИ рекомендовал услуги: {recommended_services}")
            
            return {
                'success': True,
                'ai_response': response.text,
                'recommended_services': recommended_services,
                'error': None
            }
            
        except Exception as e:
            logging.error(f"Ошибка ИИ консультации: {e}")
            return {
                'success': False,
                'ai_response': None,
                'recommended_services': [],
                'error': str(e)
            }
    
    def get_fallback_recommendation(self, problem_text: str) -> Dict:
        """Резервные рекомендации на основе ключевых слов"""
        category, services, description = self._analyze_problem_keywords(problem_text)
        
        # Формируем ответ в стиле ИИ с ID услуг
        ai_response = f"{description} Рекомендуемые услуги:\n"
        for service_id in services:
            ai_response += f"[ID: {service_id}] "
        
        return {
            'success': True,
            'ai_response': ai_response,
            'recommended_services': services,
            'error': None,
            'fallback': True
        }
    
    async def process_consultation(self, problem_text: str, all_services: List[Dict]) -> Dict:
        """Основной метод обработки консультации"""
        # Валидация входных данных
        if not problem_text or len(problem_text.strip()) < 10:
            return {
                'success': False,
                'error': 'Описание проблемы слишком короткое. Опишите проблему подробнее (минимум 10 символов).',
                'ai_response': None,
                'recommended_services': []
            }
        
        if len(problem_text) > 1000:
            problem_text = problem_text[:1000]  # Ограничиваем длину
        
        # Попытка получить ИИ рекомендацию
        ai_result = await self.get_ai_recommendation(problem_text, all_services)
        
        # Если ИИ не сработал или не дал услуги, используем резервную логику
        if not ai_result['success'] or not ai_result['recommended_services']:
            fallback_result = self.get_fallback_recommendation(problem_text)
            
            # Если был ответ ИИ, но без услуг, комбинируем
            if ai_result['success'] and ai_result['ai_response']:
                fallback_result['ai_response'] = ai_result['ai_response'] + "\n\n" + fallback_result['ai_response']
            
            return fallback_result
        
        return ai_result
    
    def validate_recommended_services(self, service_ids: List[int], available_services: List[Dict]) -> List[int]:
        """Валидация рекомендованных услуг"""
        if not service_ids:
            return []
        
        # Получаем список доступных ID
        if available_services and isinstance(available_services[0], dict):
            available_ids = {service['id'] for service in available_services}
        else:
            available_ids = {service[0] for service in available_services}  # tuple format
        
        # Фильтруем только существующие услуги
        valid_services = [sid for sid in service_ids if sid in available_ids]
        
        if len(valid_services) != len(service_ids):
            invalid_ids = set(service_ids) - set(valid_services)
            logging.warning(f"Найдены несуществующие услуги: {invalid_ids}")
        
        return valid_services
    
    def get_service_info(self, service_id: int, available_services: List[Dict]) -> Optional[Dict]:
        """Получение информации об услуге по ID"""
        for service in available_services:
            if isinstance(service, dict):
                if service['id'] == service_id:
                    return service
            else:
                if service[0] == service_id:  # tuple format
                    return {
                        'id': service[0],
                        'name': service[1],
                        'price': service[2],
                        'duration_minutes': service[3],
                        'description': service[4]
                    }
        return None
    
    def calculate_total_cost(self, service_ids: List[int], available_services: List[Dict]) -> int:
        """Расчет общей стоимости услуг"""
        total_cost = 0
        for service_id in service_ids:
            service_info = self.get_service_info(service_id, available_services)
            if service_info:
                total_cost += service_info['price']
        return total_cost
    
    def format_services_info(self, service_ids: List[int], available_services: List[Dict]) -> str:
        """Форматирование информации об услугах"""
        services_text = ""
        total_cost = 0
        
        for service_id in service_ids:
            service_info = self.get_service_info(service_id, available_services)
            if service_info:
                services_text += f"• **{service_info['name']}** - {service_info['price']}₽ ({service_info['duration_minutes']} мин)\n"
                total_cost += service_info['price']
        
        return services_text, total_cost
    
    def check_service_availability(self) -> bool:
        """Проверка доступности ИИ сервиса"""
        if not self.is_available:
            return False
        
        try:
            # Простая проверка доступности API
            test_response = self.model.generate_content("Test")
            return True
        except Exception as e:
            logging.error(f"ИИ сервис недоступен: {e}")
            return False