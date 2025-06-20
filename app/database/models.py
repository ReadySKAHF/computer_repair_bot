"""
Модели данных для базы данных
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class OrderStatus(Enum):
    """Статусы заказов"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class User:
    """Модель пользователя"""
    user_id: int
    name: str
    phone: str
    address: str
    created_at: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Создание объекта из словаря"""
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'])
            else:
                created_at = data['created_at']
        
        return cls(
            user_id=data['user_id'],
            name=data['name'],
            phone=data['phone'],
            address=data['address'],
            created_at=created_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'user_id': self.user_id,
            'name': self.name,
            'phone': self.phone,
            'address': self.address,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_display_name(self) -> str:
        """Получение отображаемого имени"""
        return self.name
    
    def get_masked_phone(self) -> str:
        """Получение замаскированного телефона"""
        if len(self.phone) >= 4:
            return self.phone[:-4] + "****"
        return "****"


@dataclass
class Service:
    """Модель услуги"""
    id: int
    name: str
    price: int
    duration_minutes: int
    description: str
    image_url: Optional[str] = None
    is_active: bool = True
    category_id: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Service':
        """Создание объекта из словаря"""
        return cls(
            id=data['id'],
            name=data['name'],
            price=data['price'],
            duration_minutes=data['duration_minutes'],
            description=data['description'],
            image_url=data.get('image_url'),
            is_active=data.get('is_active', True),
            category_id=data.get('category_id')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'duration_minutes': self.duration_minutes,
            'description': self.description,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'category_id': self.category_id
        }
    
    def get_formatted_price(self) -> str:
        """Получение отформатированной цены"""
        return f"{self.price}₽"
    
    def get_formatted_duration(self) -> str:
        """Получение отформатированного времени"""
        if self.duration_minutes < 60:
            return f"{self.duration_minutes} мин"
        
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        
        if minutes == 0:
            return f"{hours} ч"
        else:
            return f"{hours} ч {minutes} мин"
    
    def is_expensive(self) -> bool:
        """Проверка, является ли услуга дорогой"""
        return self.price > 2000
    
    def is_quick(self) -> bool:
        """Проверка, является ли услуга быстрой"""
        return self.duration_minutes <= 30


@dataclass
class Master:
    """Модель мастера"""
    id: int
    name: str
    experience_years: int
    rating: float
    specialization: Optional[str] = None
    is_active: bool = True
    phone: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Master':
        """Создание объекта из словаря"""
        return cls(
            id=data['id'],
            name=data['name'],
            experience_years=data['experience_years'],
            rating=data['rating'],
            specialization=data.get('specialization'),
            is_active=data.get('is_active', True),
            phone=data.get('phone')
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'experience_years': self.experience_years,
            'rating': self.rating,
            'specialization': self.specialization,
            'is_active': self.is_active,
            'phone': self.phone
        }
    
    def get_experience_text(self) -> str:
        """Получение текста опыта работы"""
        years = self.experience_years
        if years == 1:
            return "1 год"
        elif 2 <= years <= 4:
            return f"{years} года"
        else:
            return f"{years} лет"
    
    def get_rating_stars(self) -> str:
        """Получение рейтинга в виде звезд"""
        full_stars = int(self.rating)
        return "⭐" * full_stars
    
    def is_experienced(self) -> bool:
        """Проверка, является ли мастер опытным"""
        return self.experience_years >= 5
    
    def is_top_rated(self) -> bool:
        """Проверка, является ли мастер высокорейтинговым"""
        return self.rating >= 4.8


@dataclass
class Order:
    """Модель заказа"""
    id: int
    user_id: int
    master_id: int
    address: str
    order_date: str
    order_time: str
    total_cost: int
    status: OrderStatus
    created_at: Optional[datetime] = None
    services: Optional[List[Service]] = None
    master: Optional[Master] = None
    user: Optional[User] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Order':
        """Создание объекта из словаря"""
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'])
            else:
                created_at = data['created_at']
        
        # Обрабатываем статус
        status = data.get('status', 'pending')
        if isinstance(status, str):
            try:
                status = OrderStatus(status)
            except ValueError:
                status = OrderStatus.PENDING
        
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            master_id=data['master_id'],
            address=data['address'],
            order_date=data['order_date'],
            order_time=data['order_time'],
            total_cost=data['total_cost'],
            status=status,
            created_at=created_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'master_id': self.master_id,
            'address': self.address,
            'order_date': self.order_date,
            'order_time': self.order_time,
            'total_cost': self.total_cost,
            'status': self.status.value if isinstance(self.status, OrderStatus) else self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_status_emoji(self) -> str:
        """Получение эмодзи статуса"""
        status_emojis = {
            OrderStatus.PENDING: "⏳",
            OrderStatus.CONFIRMED: "✅",
            OrderStatus.IN_PROGRESS: "🔧",
            OrderStatus.COMPLETED: "✅",
            OrderStatus.CANCELLED: "❌"
        }
        return status_emojis.get(self.status, "❓")
    
    def get_status_text(self) -> str:
        """Получение текста статуса"""
        status_texts = {
            OrderStatus.PENDING: "Ожидает подтверждения",
            OrderStatus.CONFIRMED: "Подтвержден",
            OrderStatus.IN_PROGRESS: "В работе",
            OrderStatus.COMPLETED: "Выполнен",
            OrderStatus.CANCELLED: "Отменен"
        }
        return status_texts.get(self.status, "Неизвестно")
    
    def get_formatted_cost(self) -> str:
        """Получение отформатированной стоимости"""
        return f"{self.total_cost}₽"
    
    def get_formatted_datetime(self) -> str:
        """Получение отформатированных даты и времени"""
        return f"{self.order_date} в {self.order_time}"
    
    def can_be_cancelled(self) -> bool:
        """Проверка возможности отмены"""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]
    
    def can_be_reviewed(self) -> bool:
        """Проверка возможности оставить отзыв"""
        return self.status == OrderStatus.COMPLETED
    
    def is_active(self) -> bool:
        """Проверка активности заказа"""
        return self.status in [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.IN_PROGRESS]
    
    def get_total_duration(self) -> int:
        """Получение общего времени выполнения"""
        if self.services:
            return sum(service.duration_minutes for service in self.services)
        return 0


@dataclass
class Review:
    """Модель отзыва"""
    id: int
    user_id: int
    order_id: int
    rating: int
    comment: str
    created_at: Optional[datetime] = None
    user: Optional[User] = None
    order: Optional[Order] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Review':
        """Создание объекта из словаря"""
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'])
            else:
                created_at = data['created_at']
        
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            order_id=data['order_id'],
            rating=data['rating'],
            comment=data['comment'],
            created_at=created_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'order_id': self.order_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_stars(self) -> str:
        """Получение рейтинга в виде звезд"""
        return "⭐" * self.rating
    
    def get_short_comment(self, max_length: int = 100) -> str:
        """Получение сокращенного комментария"""
        if len(self.comment) <= max_length:
            return self.comment
        return self.comment[:max_length-3] + "..."
    
    def is_positive(self) -> bool:
        """Проверка позитивности отзыва"""
        return self.rating >= 4
    
    def is_excellent(self) -> bool:
        """Проверка отличности отзыва"""
        return self.rating == 5


@dataclass
class SupportRequest:
    """Модель обращения в поддержку"""
    id: int
    user_id: int
    message: str
    status: str = "new"
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    user: Optional[User] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SupportRequest':
        """Создание объекта из словаря"""
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'])
            else:
                created_at = data['created_at']
        
        resolved_at = None
        if data.get('resolved_at'):
            if isinstance(data['resolved_at'], str):
                resolved_at = datetime.fromisoformat(data['resolved_at'])
            else:
                resolved_at = data['resolved_at']
        
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            message=data['message'],
            status=data.get('status', 'new'),
            created_at=created_at,
            resolved_at=resolved_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def get_short_message(self, max_length: int = 50) -> str:
        """Получение сокращенного сообщения"""
        if len(self.message) <= max_length:
            return self.message
        return self.message[:max_length-3] + "..."
    
    def is_resolved(self) -> bool:
        """Проверка разрешения обращения"""
        return self.status == "resolved"
    
    def is_urgent(self) -> bool:
        """Проверка срочности обращения"""
        # Простая логика: если в сообщении есть слова "срочно", "критично" и т.д.
        urgent_keywords = ["срочно", "критично", "немедленно", "важно", "проблема"]
        return any(keyword in self.message.lower() for keyword in urgent_keywords)


@dataclass
class Statistics:
    """Модель статистики"""
    total_users: int = 0
    active_users_24h: int = 0
    orders_today: int = 0
    orders_total: int = 0
    orders_completed: int = 0
    orders_cancelled: int = 0
    total_revenue: int = 0
    average_rating: float = 0.0
    total_reviews: int = 0
    support_requests_today: int = 0
    support_requests_total: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Statistics':
        """Создание объекта из словаря"""
        return cls(
            total_users=data.get('total_users', 0),
            active_users_24h=data.get('active_users_24h', 0),
            orders_today=data.get('orders_today', 0),
            orders_total=data.get('orders_total', 0),
            orders_completed=data.get('orders_completed', 0),
            orders_cancelled=data.get('orders_cancelled', 0),
            total_revenue=data.get('total_revenue', 0),
            average_rating=data.get('average_rating', 0.0),
            total_reviews=data.get('total_reviews', 0),
            support_requests_today=data.get('support_requests_today', 0),
            support_requests_total=data.get('support_requests_total', 0)
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'total_users': self.total_users,
            'active_users_24h': self.active_users_24h,
            'orders_today': self.orders_today,
            'orders_total': self.orders_total,
            'orders_completed': self.orders_completed,
            'orders_cancelled': self.orders_cancelled,
            'total_revenue': self.total_revenue,
            'average_rating': self.average_rating,
            'total_reviews': self.total_reviews,
            'support_requests_today': self.support_requests_today,
            'support_requests_total': self.support_requests_total
        }
    
    def get_completion_rate(self) -> float:
        """Получение процента выполненных заказов"""
        if self.orders_total == 0:
            return 0.0
        return (self.orders_completed / self.orders_total) * 100
    
    def get_cancellation_rate(self) -> float:
        """Получение процента отмененных заказов"""
        if self.orders_total == 0:
            return 0.0
        return (self.orders_cancelled / self.orders_total) * 100
    
    def get_formatted_revenue(self) -> str:
        """Получение отформатированной выручки"""
        if self.total_revenue >= 1000000:
            return f"{self.total_revenue / 1000000:.1f}М₽"
        elif self.total_revenue >= 1000:
            return f"{self.total_revenue / 1000:.0f}К₽"
        else:
            return f"{self.total_revenue}₽"


# Утилитарные функции для работы с моделями

def convert_dict_to_model(data: Dict[str, Any], model_class):
    """Универсальная функция конвертации словаря в модель"""
    if hasattr(model_class, 'from_dict'):
        return model_class.from_dict(data)
    else:
        raise ValueError(f"Класс {model_class.__name__} не поддерживает from_dict")


def convert_models_to_dicts(models: List[Any]) -> List[Dict[str, Any]]:
    """Конвертация списка моделей в список словарей"""
    return [model.to_dict() for model in models if hasattr(model, 'to_dict')]


def filter_active_services(services: List[Service]) -> List[Service]:
    """Фильтрация активных услуг"""
    return [service for service in services if service.is_active]


def filter_active_masters(masters: List[Master]) -> List[Master]:
    """Фильтрация активных мастеров"""
    return [master for master in masters if master.is_active]


def get_orders_by_status(orders: List[Order], status: OrderStatus) -> List[Order]:
    """Получение заказов по статусу"""
    return [order for order in orders if order.status == status]


def calculate_average_rating(reviews: List[Review]) -> float:
    """Расчет среднего рейтинга"""
    if not reviews:
        return 0.0
    
    total_rating = sum(review.rating for review in reviews)
    return total_rating / len(reviews)


def get_top_services_by_orders(orders: List[Order]) -> Dict[str, int]:
    """Получение топ услуг по количеству заказов"""
    service_counts = {}
    
    for order in orders:
        if order.services:
            for service in order.services:
                service_name = service.name
                service_counts[service_name] = service_counts.get(service_name, 0) + 1
    
    # Сортируем по убыванию
    return dict(sorted(service_counts.items(), key=lambda x: x[1], reverse=True))