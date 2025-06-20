"""
Сервис для работы с заказами
"""
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from ..database.queries import DatabaseQueries
from ..utils.constants import ORDER_STATUSES, ORDER_STATUS_EMOJI


class OrderService:
    """Сервис для управления заказами"""
    
    def __init__(self, db_queries: DatabaseQueries):
        self.db_queries = db_queries
    
    async def create_order_with_validation(self, user_id: int, service_ids: List[int], 
                                         order_date: str, order_time: str, 
                                         address: str) -> Dict:
        """
        Создание заказа с полной валидацией
        
        Returns:
            Dict: {'success': bool, 'order_id': int, 'message': str, 'details': dict}
        """
        try:
            # Проверяем существование пользователя
            user = await self.db_queries.get_user(user_id)
            if not user:
                return {
                    'success': False,
                    'order_id': None,
                    'message': 'Пользователь не найден',
                    'details': {}
                }
            
            # Валидируем услуги
            services_validation = await self._validate_services(service_ids)
            if not services_validation['valid']:
                return {
                    'success': False,
                    'order_id': None,
                    'message': services_validation['message'],
                    'details': {}
                }
            
            # Валидируем дату и время
            datetime_validation = self._validate_datetime(order_date, order_time)
            if not datetime_validation['valid']:
                return {
                    'success': False,
                    'order_id': None,
                    'message': datetime_validation['message'],
                    'details': {}
                }
            
            # Выбираем мастера
            master = await self._assign_master()
            if not master:
                return {
                    'success': False,
                    'order_id': None,
                    'message': 'Нет доступных мастеров',
                    'details': {}
                }
            
            # Вычисляем стоимость
            total_cost = services_validation['total_cost']
            
            # Создаем заказ
            order_id = await self.db_queries.create_order(
                user_id=user_id,
                master_id=master['id'],
                address=address,
                order_date=order_date,
                order_time=order_time,
                total_cost=total_cost,
                service_ids=service_ids
            )
            
            if order_id:
                return {
                    'success': True,
                    'order_id': order_id,
                    'message': 'Заказ успешно создан',
                    'details': {
                        'master_name': master['name'],
                        'master_rating': master['rating'],
                        'total_cost': total_cost,
                        'services_count': len(service_ids),
                        'estimated_duration': services_validation['total_duration']
                    }
                }
            else:
                return {
                    'success': False,
                    'order_id': None,
                    'message': 'Ошибка создания заказа в базе данных',
                    'details': {}
                }
        
        except Exception as e:
            logging.error(f"Ошибка в create_order_with_validation: {e}")
            return {
                'success': False,
                'order_id': None,
                'message': 'Внутренняя ошибка сервера',
                'details': {}
            }
    
    async def _validate_services(self, service_ids: List[int]) -> Dict:
        """Валидация списка услуг"""
        if not service_ids:
            return {
                'valid': False,
                'message': 'Не выбрано ни одной услуги',
                'total_cost': 0,
                'total_duration': 0
            }
        
        if len(service_ids) > 10:  # Максимум 10 услуг
            return {
                'valid': False,
                'message': 'Максимальное количество услуг: 10',
                'total_cost': 0,
                'total_duration': 0
            }
        
        total_cost = 0
        total_duration = 0
        valid_services = []
        
        for service_id in service_ids:
            service = await self.db_queries.get_service_by_id(service_id)
            if not service:
                return {
                    'valid': False,
                    'message': f'Услуга с ID {service_id} не найдена',
                    'total_cost': 0,
                    'total_duration': 0
                }
            
            valid_services.append(service)
            total_cost += service['price']
            total_duration += service['duration_minutes']
        
        return {
            'valid': True,
            'message': 'Услуги валидны',
            'total_cost': total_cost,
            'total_duration': total_duration,
            'services': valid_services
        }
    
    def _validate_datetime(self, order_date: str, order_time: str) -> Dict:
        """Валидация даты и времени заказа"""
        try:
            # Парсим дату и время
            order_datetime = datetime.strptime(f"{order_date} {order_time}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            
            # Проверяем, что дата не в прошлом
            if order_datetime < now:
                return {
                    'valid': False,
                    'message': 'Нельзя выбрать дату и время в прошлом'
                }
            
            # Проверяем, что дата не слишком далеко в будущем (30 дней)
            max_date = now + timedelta(days=30)
            if order_datetime > max_date:
                return {
                    'valid': False,
                    'message': 'Нельзя создать заказ более чем на 30 дней вперед'
                }
            
            # Проверяем рабочие часы (10:00 - 22:00)
            if order_datetime.hour < 10 or order_datetime.hour >= 22:
                return {
                    'valid': False,
                    'message': 'Рабочие часы: с 10:00 до 22:00'
                }
            
            return {
                'valid': True,
                'message': 'Дата и время валидны',
                'datetime': order_datetime
            }
        
        except ValueError:
            return {
                'valid': False,
                'message': 'Некорректный формат даты или времени'
            }
    
    async def _assign_master(self) -> Optional[Dict]:
        """Назначение мастера для заказа"""
        masters = await self.db_queries.get_masters()
        
        if not masters:
            return None
        
        # Простая логика: выбираем случайного мастера
        # В будущем можно усложнить (по загруженности, рейтингу, специализации)
        return random.choice(masters)
    
    async def get_order_summary(self, order_id: int, user_id: int) -> Optional[Dict]:
        """Получение детального резюме заказа"""
        try:
            order = await self.db_queries.get_order_by_id(order_id)
            
            if not order or order['user_id'] != user_id:
                return None
            
            # Получаем услуги заказа
            services = []
            service_ids = []  # Нужно получить из order_services таблицы
            
            # Формируем резюме
            summary = {
                'order_id': order['id'],
                'status': order['status'],
                'status_text': ORDER_STATUSES.get(order['status'], order['status']),
                'status_emoji': ORDER_STATUS_EMOJI.get(order['status'], '❓'),
                'date': order['order_date'],
                'time': order['order_time'],
                'address': order['address'],
                'master_name': order['master_name'],
                'total_cost': order['total_cost'],
                'services': order['services'],
                'created_at': order['created_at'],
                'can_cancel': order['status'] in ['pending', 'confirmed'],
                'can_review': order['status'] == 'completed'
            }
            
            return summary
        
        except Exception as e:
            logging.error(f"Ошибка в get_order_summary: {e}")
            return None
    
    async def cancel_order(self, order_id: int, user_id: int) -> Dict:
        """Отмена заказа пользователем"""
        try:
            order = await self.db_queries.get_order_by_id(order_id)
            
            if not order:
                return {
                    'success': False,
                    'message': 'Заказ не найден'
                }
            
            if order['user_id'] != user_id:
                return {
                    'success': False,
                    'message': 'Доступ запрещен'
                }
            
            if order['status'] not in ['pending', 'confirmed']:
                return {
                    'success': False,
                    'message': 'Этот заказ нельзя отменить'
                }
            
            # Обновляем статус
            success = await self.db_queries.update_order_status(order_id, 'cancelled')
            
            if success:
                return {
                    'success': True,
                    'message': 'Заказ успешно отменен'
                }
            else:
                return {
                    'success': False,
                    'message': 'Ошибка при отмене заказа'
                }
        
        except Exception as e:
            logging.error(f"Ошибка в cancel_order: {e}")
            return {
                'success': False,
                'message': 'Внутренняя ошибка сервера'
            }
    
    async def get_user_orders_summary(self, user_id: int) -> Dict:
        """Получение сводки заказов пользователя"""
        try:
            orders = await self.db_queries.get_user_orders(user_id)
            
            if not orders:
                return {
                    'total_orders': 0,
                    'pending_orders': 0,
                    'completed_orders': 0,
                    'total_spent': 0,
                    'orders': []
                }
            
            # Подсчитываем статистику
            total_orders = len(orders)
            pending_orders = len([o for o in orders if o['status'] in ['pending', 'confirmed', 'in_progress']])
            completed_orders = len([o for o in orders if o['status'] == 'completed'])
            total_spent = sum(o['total_cost'] for o in orders if o['status'] == 'completed')
            
            return {
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'completed_orders': completed_orders,
                'total_spent': total_spent,
                'orders': orders
            }
        
        except Exception as e:
            logging.error(f"Ошибка в get_user_orders_summary: {e}")
            return {
                'total_orders': 0,
                'pending_orders': 0,
                'completed_orders': 0,
                'total_spent': 0,
                'orders': []
            }
    
    async def estimate_order_cost(self, service_ids: List[int]) -> Dict:
        """Оценка стоимости заказа до создания"""
        try:
            validation = await self._validate_services(service_ids)
            
            if not validation['valid']:
                return {
                    'success': False,
                    'message': validation['message'],
                    'total_cost': 0,
                    'total_duration': 0
                }
            
            return {
                'success': True,
                'message': 'Оценка выполнена',
                'total_cost': validation['total_cost'],
                'total_duration': validation['total_duration'],
                'services_count': len(service_ids),
                'estimated_time_text': self._format_duration(validation['total_duration'])
            }
        
        except Exception as e:
            logging.error(f"Ошибка в estimate_order_cost: {e}")
            return {
                'success': False,
                'message': 'Ошибка оценки стоимости',
                'total_cost': 0,
                'total_duration': 0
            }
    
    def _format_duration(self, minutes: int) -> str:
        """Форматирование времени выполнения"""
        if minutes < 60:
            return f"{minutes} мин"
        
        hours = minutes // 60
        remaining_minutes = minutes % 60
        
        if remaining_minutes == 0:
            return f"{hours} ч"
        else:
            return f"{hours} ч {remaining_minutes} мин"
    
    async def get_available_time_slots(self, date: str) -> List[str]:
        """Получение доступных временных слотов на дату"""
        try:
            # В будущем можно проверять занятость мастеров
            # Пока возвращаем все стандартные слоты
            from ..utils.constants import TIME_SLOTS
            
            # Если это сегодня, убираем прошедшие слоты
            order_date = datetime.strptime(date, "%Y-%m-%d").date()
            today = datetime.now().date()
            
            if order_date == today:
                current_time = datetime.now().time()
                available_slots = []
                
                for slot in TIME_SLOTS:
                    slot_time = datetime.strptime(slot, "%H:%M").time()
                    if slot_time > current_time:
                        available_slots.append(slot)
                
                return available_slots
            else:
                return TIME_SLOTS.copy()
        
        except Exception as e:
            logging.error(f"Ошибка в get_available_time_slots: {e}")
            from ..utils.constants import TIME_SLOTS
            return TIME_SLOTS.copy()
    
    async def repeat_order(self, original_order_id: int, user_id: int) -> Dict:
        """Повторение заказа"""
        try:
            original_order = await self.db_queries.get_order_by_id(original_order_id)
            
            if not original_order or original_order['user_id'] != user_id:
                return {
                    'success': False,
                    'message': 'Исходный заказ не найден'
                }
            
            # Получаем услуги из исходного заказа
            # Здесь нужно получить service_ids из order_services таблицы
            # Пока используем заглушку
            service_ids = [1, 2]  # TODO: получить реальные service_ids
            
            return {
                'success': True,
                'message': 'Данные для повтора заказа подготовлены',
                'service_ids': service_ids,
                'original_address': original_order['address'],
                'estimated_cost': original_order['total_cost']
            }
        
        except Exception as e:
            logging.error(f"Ошибка в repeat_order: {e}")
            return {
                'success': False,
                'message': 'Ошибка при подготовке повтора заказа'
            }