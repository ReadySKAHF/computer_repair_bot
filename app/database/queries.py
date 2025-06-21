"""
Обновленный модуль для выполнения запросов к базе данных
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
    
    # === АДМИНСКИЕ МЕТОДЫ ДЛЯ ЗАКАЗОВ ===
    
    @handle_db_errors
    async def get_all_orders(self, limit: int = 50, offset: int = 0, status_filter: str = None) -> List[Dict[str, Any]]:
        """Получение всех заказов для админа"""
        async with get_db_connection(self.db_path) as db:
            where_clause = ""
            params = []
            
            if status_filter:
                where_clause = "WHERE o.status = ?"
                params.append(status_filter)
            
            query = f"""
                SELECT 
                    o.id, o.user_id, o.order_date, o.order_time, o.total_cost, o.status, o.created_at,
                    u.name as user_name, u.phone as user_phone,
                    m.name as master_name,
                    COALESCE(GROUP_CONCAT(s.name, ', '), 'Услуги не указаны') as services
                FROM orders o
                JOIN users u ON o.user_id = u.user_id
                JOIN masters m ON o.master_id = m.id
                LEFT JOIN order_services os ON o.id = os.order_id
                LEFT JOIN services s ON os.service_id = s.id
                {where_clause}
                GROUP BY o.id, o.user_id, o.order_date, o.order_time, o.total_cost, o.status, o.created_at, u.name, u.phone, m.name
                ORDER BY o.created_at DESC
                LIMIT ? OFFSET ?
            """
            
            params.extend([limit, offset])
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @handle_db_errors
    async def get_orders_count(self, status_filter: str = None) -> int:
        """Получение общего количества заказов"""
        async with get_db_connection(self.db_path) as db:
            where_clause = ""
            params = []
            
            if status_filter:
                where_clause = "WHERE status = ?"
                params.append(status_filter)
            
            query = f"SELECT COUNT(*) FROM orders {where_clause}"
            cursor = await db.execute(query, params)
            result = await cursor.fetchone()
            return result[0] if result else 0

    @handle_db_errors
    async def bulk_update_orders_status(self, status: str) -> bool:
        """Массовое обновление статуса всех заказов"""
        async with get_db_connection(self.db_path) as db:
            await db.execute("UPDATE orders SET status = ? WHERE status != 'completed'", (status,))
            await db.commit()
            logging.info(f"Все активные заказы переведены в статус {status}")
            return True

    @handle_db_errors
    async def update_multiple_orders_status(self, order_ids: List[int], status: str) -> bool:
        """Обновление статуса нескольких заказов"""
        if not order_ids:
            return False
        
        placeholders = ','.join('?' * len(order_ids))
        query = f"UPDATE orders SET status = ? WHERE id IN ({placeholders})"
        
        async with get_db_connection(self.db_path) as db:
            await db.execute(query, [status] + order_ids)
            await db.commit()
            logging.info(f"Обновлен статус {len(order_ids)} заказов на {status}")
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
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПОДДЕРЖКОЙ (АДМИНКА) ===

    @handle_db_errors
    async def get_support_requests_for_admin(self, status_filter: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Получение обращений в поддержку для админа"""
        async with get_db_connection(self.db_path) as db:
            where_clause = ""
            params = []
            
            if status_filter:
                where_clause = "WHERE sr.status = ?"
                params.append(status_filter)
            
            query = f"""
                SELECT 
                    sr.id, sr.user_id, sr.message, sr.admin_response, sr.status, sr.admin_id,
                    datetime(sr.created_at, 'localtime') as created_at,
                    datetime(sr.answered_at, 'localtime') as answered_at,
                    u.name as user_name, u.phone as user_phone,
                    admin.name as admin_name
                FROM support_requests sr
                JOIN users u ON sr.user_id = u.user_id
                LEFT JOIN users admin ON sr.admin_id = admin.user_id
                {where_clause}
                ORDER BY sr.created_at DESC
                LIMIT ?
            """
            
            params.append(limit)
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @handle_db_errors
    async def respond_to_support_request(self, request_id: int, admin_id: int, response: str) -> bool:
        """Ответ на обращение в поддержку"""
        async with get_db_connection(self.db_path) as db:
            await db.execute(
                """UPDATE support_requests 
                   SET admin_response = ?, status = 'answered', admin_id = ?, answered_at = CURRENT_TIMESTAMP 
                   WHERE id = ?""",
                (response, admin_id, request_id)
            )
            await db.commit()
            logging.info(f"Ответ админа {admin_id} на обращение {request_id}")
            return True

    @handle_db_errors
    async def get_user_support_requests_with_responses(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение обращений пользователя с ответами"""
        async with get_db_connection(self.db_path) as db:
            cursor = await db.execute("""
                SELECT 
                    id, message, admin_response, status,
                    datetime(created_at, 'localtime') as created_at,
                    datetime(answered_at, 'localtime') as answered_at
                FROM support_requests 
                WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    @handle_db_errors
    async def mark_support_request_as_read(self, request_id: int) -> bool:
        """Отметить обращение как прочитанное админом"""
        async with get_db_connection(self.db_path) as db:
            await db.execute(
                "UPDATE support_requests SET status = 'read' WHERE id = ? AND status = 'new'",
                (request_id,)
            )
            await db.commit()
            return True
    
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