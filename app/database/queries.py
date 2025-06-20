"""
Модуль для выполнения запросов к базе данных
"""
import logging
from typing import Optional, List, Dict, Any, Tuple
from .connection import get_db_connection, handle_db_errors


class DatabaseQueries:
    """Класс для выполнения запросов к базе данных"""
    
    def __init__(self, db_path: str = "repair_bot.db"):
        self.db_path = db_path
    
    # === ПОЛЬЗОВАТЕЛИ ===
    
    @handle_db_errors
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение пользователя по ID"""
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute(
                "SELECT user_id, name, phone, address, created_at FROM users WHERE user_id = ?", 
                (user_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    @handle_db_errors
    async def create_user(self, user_id: int, name: str, phone: str, address: str) -> bool:
        """Создание нового пользователя"""
        async with get_db_connection(self.db_path) as db:
            # Проверяем, не существует ли уже пользователь
            cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if await cursor.fetchone():
                logging.warning(f"Попытка создать существующего пользователя {user_id}")
                return False
            
            await db.execute(
                "INSERT INTO users (user_id, name, phone, address) VALUES (?, ?, ?, ?)",
                (user_id, name, phone, address)
            )
            await db.commit()
            logging.info(f"Создан новый пользователь {user_id}")
            return True
    
    @handle_db_errors
    async def update_user_field(self, user_id: int, field: str, value: str) -> bool:
        """Обновление поля пользователя"""
        allowed_fields = ['name', 'phone', 'address']
        if field not in allowed_fields:
            logging.error(f"Попытка обновить недопустимое поле: {field}")
            return False
        
        async with get_db_connection(self.db_path) as db:
            await db.execute(
                f"UPDATE users SET {field} = ? WHERE user_id = ?", 
                (value, user_id)
            )
            await db.commit()
            logging.info(f"Обновлено поле {field} для пользователя {user_id}")
            return True
    
    # === УСЛУГИ ===
    
    @handle_db_errors
    async def get_services(self, page: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение услуг с пагинацией"""
        offset = page * limit
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id, name, price, duration_minutes, description, image_url FROM services LIMIT ? OFFSET ?", 
                (limit, offset)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    @handle_db_errors
    async def get_services_count(self) -> int:
        """Получение общего количества услуг"""
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM services")
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    @handle_db_errors
    async def get_service_by_id(self, service_id: int) -> Optional[Dict[str, Any]]:
        """Получение услуги по ID"""
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id, name, price, duration_minutes, description, image_url FROM services WHERE id = ?", 
                (service_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    # === МАСТЕРА ===
    
    @handle_db_errors
    async def get_masters(self, page: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение мастеров с пагинацией"""
        offset = page * limit
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id, name, experience_years, rating FROM masters LIMIT ? OFFSET ?", 
                (limit, offset)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    @handle_db_errors
    async def get_masters_count(self) -> int:
        """Получение общего количества мастеров"""
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM masters")
            result = await cursor.fetchone()
            return result[0] if result else 0
    
    @handle_db_errors
    async def get_master_by_id(self, master_id: int) -> Optional[Dict[str, Any]]:
        """Получение мастера по ID"""
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute(
                "SELECT id, name, experience_years, rating FROM masters WHERE id = ?", 
                (master_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    # === ЗАКАЗЫ ===
    
    @handle_db_errors
    async def create_order(self, user_id: int, master_id: int, address: str, 
                          order_date: str, order_time: str, total_cost: int, 
                          service_ids: List[int]) -> Optional[int]:
        """Создание заказа с транзакцией"""
        async with get_db_connection(self.db_path) as db:
            async with db.execute("BEGIN TRANSACTION"):
                try:
                    # Создаем заказ
                    cursor = await db.execute("""
                        INSERT INTO orders (user_id, master_id, address, order_date, order_time, total_cost)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, master_id, address, order_date, order_time, total_cost))
                    
                    order_id = cursor.lastrowid
                    
                    # Добавляем услуги к заказу
                    for service_id in service_ids:
                        # Проверяем существование услуги
                        service_check = await db.execute(
                            "SELECT id FROM services WHERE id = ?", (service_id,)
                        )
                        if not await service_check.fetchone():
                            raise ValueError(f"Услуга с ID {service_id} не существует")
                        
                        await db.execute(
                            "INSERT INTO order_services (order_id, service_id) VALUES (?, ?)",
                            (order_id, service_id)
                        )
                    
                    await db.commit()
                    logging.info(f"Создан заказ {order_id} для пользователя {user_id}")
                    return order_id
                    
                except Exception as e:
                    await db.rollback()
                    logging.error(f"Ошибка создания заказа: {e}")
                    raise
    
    @handle_db_errors
    async def get_user_orders(self, user_id: int, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Получение заказов пользователя с поддержкой пагинации
        
        Args:
            user_id: ID пользователя
            limit: Количество заказов для получения
            offset: Смещение для пагинации
        """
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute("""
                SELECT 
                    o.id, o.order_date, o.order_time, o.total_cost, o.status,
                    m.name as master_name,
                    COALESCE(GROUP_CONCAT(s.name, ', '), 'Услуги не указаны') as services
                FROM orders o
                JOIN masters m ON o.master_id = m.id
                LEFT JOIN order_services os ON o.id = os.order_id
                LEFT JOIN services s ON os.service_id = s.id
                WHERE o.user_id = ?
                GROUP BY o.id, o.order_date, o.order_time, o.total_cost, o.status, m.name
                ORDER BY o.created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    @handle_db_errors
    async def get_order_by_id(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Получение заказа по ID"""
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute("""
                SELECT 
                    o.id, o.user_id, o.master_id, o.address, o.order_date, o.order_time, 
                    o.total_cost, o.status, o.created_at,
                    m.name as master_name,
                    GROUP_CONCAT(s.name, ', ') as services
                FROM orders o
                JOIN masters m ON o.master_id = m.id
                LEFT JOIN order_services os ON o.id = os.order_id
                LEFT JOIN services s ON os.service_id = s.id
                WHERE o.id = ?
                GROUP BY o.id
            """, (order_id,))
            
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    @handle_db_errors
    async def update_order_status(self, order_id: int, status: str) -> bool:
        """Обновление статуса заказа"""
        allowed_statuses = ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled']
        if status not in allowed_statuses:
            logging.error(f"Недопустимый статус заказа: {status}")
            return False
        
        async with get_db_connection(self.db_path) as db:
            await db.execute(
                "UPDATE orders SET status = ? WHERE id = ?", 
                (status, order_id)
            )
            await db.commit()
            logging.info(f"Статус заказа {order_id} изменен на {status}")
            return True
    
    # === ОТЗЫВЫ ===
    
    @handle_db_errors
    async def get_recent_reviews(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение последних отзывов"""
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute("""
                SELECT 
                    r.rating, r.comment, 
                    datetime(r.created_at, 'localtime') as created_at,
                    u.name 
                FROM reviews r
                JOIN users u ON r.user_id = u.user_id
                ORDER BY r.created_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    @handle_db_errors
    async def create_review(self, user_id: int, order_id: int, rating: int, comment: str) -> bool:
        """Создание отзыва"""
        async with get_db_connection(self.db_path) as db:
            # Проверяем, что заказ существует и принадлежит пользователю
            cursor = await db.execute(
                "SELECT id FROM orders WHERE id = ? AND user_id = ?", 
                (order_id, user_id)
            )
            if not await cursor.fetchone():
                logging.error(f"Заказ {order_id} не найден для пользователя {user_id}")
                return False
            
            # Проверяем, что отзыв еще не создан
            cursor = await db.execute(
                "SELECT id FROM reviews WHERE user_id = ? AND order_id = ?",
                (user_id, order_id)
            )
            if await cursor.fetchone():
                logging.warning(f"Отзыв уже существует для заказа {order_id}")
                return False
            
            await db.execute(
                "INSERT INTO reviews (user_id, order_id, rating, comment) VALUES (?, ?, ?, ?)",
                (user_id, order_id, rating, comment)
            )
            await db.commit()
            logging.info(f"Создан отзыв для заказа {order_id}")
            return True
    
    @handle_db_errors
    async def check_review_exists(self, user_id: int, order_id: int) -> bool:
        """Проверка существования отзыва"""
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM reviews WHERE user_id = ? AND order_id = ?",
                (user_id, order_id)
            )
            result = await cursor.fetchone()
            return result[0] > 0 if result else False
    
    # === ПОДДЕРЖКА ===
    
    @handle_db_errors
    async def save_support_request(self, user_id: int, message: str) -> bool:
        """Сохранение обращения в поддержку"""
        async with get_db_connection(self.db_path) as db:
            await db.execute(
                "INSERT INTO support_requests (user_id, message) VALUES (?, ?)",
                (user_id, message)
            )
            await db.commit()
            logging.info(f"Сохранено обращение в поддержку от пользователя {user_id}")
            return True
    
    @handle_db_errors
    async def get_support_requests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение обращений в поддержку"""
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute("""
                SELECT 
                    sr.id, sr.user_id, sr.message,
                    datetime(sr.created_at, 'localtime') as created_at,
                    u.name as user_name, u.phone as user_phone
                FROM support_requests sr
                JOIN users u ON sr.user_id = u.user_id
                ORDER BY sr.created_at DESC
                LIMIT ?
            """, (limit,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # === СТАТИСТИКА ===
    
    @handle_db_errors
    async def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики бота"""
        async with get_db_connection(self.db_path) as db:
            stats = {}
            
            # Общее количество пользователей
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            stats['total_users'] = (await cursor.fetchone())[0]
            
            # Количество заказов
            cursor = await db.execute("SELECT COUNT(*) FROM orders")
            stats['total_orders'] = (await cursor.fetchone())[0]
            
            # Заказы сегодня
            cursor = await db.execute("""
                SELECT COUNT(*) FROM orders 
                WHERE DATE(created_at) = DATE('now')
            """)
            stats['orders_today'] = (await cursor.fetchone())[0]
            
            # Средний рейтинг
            cursor = await db.execute("SELECT AVG(rating) FROM reviews")
            avg_rating = await cursor.fetchone()
            stats['average_rating'] = round(avg_rating[0], 2) if avg_rating[0] else 0
            
            # Количество отзывов
            cursor = await db.execute("SELECT COUNT(*) FROM reviews")
            stats['total_reviews'] = (await cursor.fetchone())[0]
            
            # Обращения в поддержку сегодня
            cursor = await db.execute("""
                SELECT COUNT(*) FROM support_requests 
                WHERE DATE(created_at) = DATE('now')
            """)
            stats['support_requests_today'] = (await cursor.fetchone())[0]
            
            return stats