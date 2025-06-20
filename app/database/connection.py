"""
Модуль для работы с базой данных
"""
import aiosqlite
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
from functools import wraps


def handle_db_errors(func):
    """Декоратор для обработки ошибок БД"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except aiosqlite.Error as e:
            logging.error(f"Ошибка базы данных в {func.__name__}: {e}")
            return None
        except Exception as e:
            logging.error(f"Неожиданная ошибка в {func.__name__}: {e}")
            return None
    return wrapper


@asynccontextmanager
async def get_db_connection(db_path: str = "repair_bot.db"):
    """Контекстный менеджер для безопасной работы с БД"""
    conn = None
    try:
        conn = await aiosqlite.connect(db_path)
        conn.row_factory = aiosqlite.Row  # Для удобного доступа к колонкам
        yield conn
    except Exception as e:
        logging.error(f"Ошибка соединения с БД: {e}")
        raise
    finally:
        if conn:
            await conn.close()


class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self, db_path: str = "repair_bot.db"):
        self.db_path = db_path
    
    async def init_database(self):
        """Инициализация базы данных"""
        async with get_db_connection(self.db_path) as db:
            await self._create_tables(db)
            await self._create_indexes(db)
            await db.commit()
            logging.info("База данных инициализирована")
    
    async def _create_tables(self, db: aiosqlite.Connection):
        """Создание таблиц"""
        # Таблица пользователей
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица услуг
        await db.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                duration_minutes INTEGER NOT NULL,
                description TEXT NOT NULL,
                image_url TEXT
            )
        ''')
        
        # Таблица мастеров
        await db.execute('''
            CREATE TABLE IF NOT EXISTS masters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                experience_years INTEGER NOT NULL,
                rating REAL DEFAULT 5.0
            )
        ''')
        
        # Таблица заказов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                master_id INTEGER NOT NULL,
                address TEXT NOT NULL,
                order_date DATE NOT NULL,
                order_time TIME NOT NULL,
                total_cost INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (master_id) REFERENCES masters (id)
            )
        ''')
        
        # Таблица заказанных услуг
        await db.execute('''
            CREATE TABLE IF NOT EXISTS order_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (service_id) REFERENCES services (id)
            )
        ''')
        
        # Таблица отзывов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        # Таблица обращений в поддержку
        await db.execute('''
            CREATE TABLE IF NOT EXISTS support_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
    
    async def _create_indexes(self, db: aiosqlite.Connection):
        """Создание индексов для производительности"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_reviews_order_id ON reviews(order_id)",
            "CREATE INDEX IF NOT EXISTS idx_order_services_order_id ON order_services(order_id)",
            "CREATE INDEX IF NOT EXISTS idx_order_services_service_id ON order_services(service_id)",
            "CREATE INDEX IF NOT EXISTS idx_support_user_id ON support_requests(user_id)"
        ]
        
        for index_sql in indexes:
            await db.execute(index_sql)
    
    async def populate_test_data(self):
        """Заполнение базы данных тестовыми данными"""
        async with get_db_connection(self.db_path) as db:
            # Проверяем, есть ли уже данные
            cursor = await db.execute("SELECT COUNT(*) FROM services")
            count = await cursor.fetchone()
            
            if count[0] == 0:
                await self._populate_services(db)
                await self._populate_masters(db)
                await self._populate_test_reviews(db)
                await db.commit()
                logging.info("Тестовые данные добавлены")
    
    async def _populate_services(self, db: aiosqlite.Connection):
        """Добавление услуг"""
        services = [
            ("Диагностика компьютера", 500, 30, "Полная диагностика всех компонентов системы", None),
            ("Чистка от пыли", 800, 45, "Профессиональная чистка системного блока от пыли", None),
            ("Замена термопасты", 1200, 60, "Замена термопасты на процессоре и видеокарте", None),
            ("Установка Windows", 1500, 90, "Установка операционной системы Windows с драйверами", None),
            ("Восстановление данных", 3000, 120, "Восстановление утерянных файлов и данных", None),
            ("Ремонт блока питания", 2500, 180, "Диагностика и ремонт блока питания", None),
            ("Замена жесткого диска", 2000, 75, "Замена HDD на SSD или установка нового диска", None),
            ("Настройка сети", 1800, 60, "Настройка домашней сети и интернет-соединения", None),
            ("Удаление вирусов", 1000, 45, "Полная очистка системы от вредоносного ПО", None),
            ("Ремонт материнской платы", 4000, 240, "Диагностика и ремонт материнской платы", None),
            ("Установка ПО", 800, 30, "Установка необходимых программ", None),
            ("Настройка BIOS", 1200, 45, "Настройка параметров BIOS/UEFI", None),
            ("Ремонт видеокарты", 3500, 180, "Диагностика и ремонт видеокарты", None),
            ("Замена оперативной памяти", 1500, 30, "Установка и настройка новой оперативной памяти", None),
            ("Настройка игр", 1000, 60, "Оптимизация настроек для игр", None)
        ]
        
        await db.executemany(
            "INSERT INTO services (name, price, duration_minutes, description, image_url) VALUES (?, ?, ?, ?, ?)",
            services
        )
    
    async def _populate_masters(self, db: aiosqlite.Connection):
        """Добавление мастеров"""
        masters = [
            ("Алексей Петров", 5, 4.8),
            ("Мария Сидорова", 3, 4.9),
            ("Дмитрий Иванов", 7, 4.7),
            ("Елена Козлова", 4, 4.6),
            ("Сергей Смирнов", 6, 4.9)
        ]
        
        await db.executemany(
            "INSERT INTO masters (name, experience_years, rating) VALUES (?, ?, ?)",
            masters
        )
    
    async def _populate_test_reviews(self, db: aiosqlite.Connection):
        """Добавление тестовых отзывов"""
        # Сначала создадим тестовых пользователей для отзывов
        test_users = [
            (123456789, "Александр И.", "+7900123****", "ул. Примерная, 1"),
            (123456790, "Мария С.", "+7900234****", "ул. Тестовая, 2"),
            (123456791, "Дмитрий К.", "+7900345****", "ул. Образцовая, 3"),
            (123456792, "Елена П.", "+7900456****", "ул. Показательная, 4"),
            (123456793, "Сергей В.", "+7900567****", "ул. Демонстрационная, 5"),
            (123456794, "Анна Л.", "+7900678****", "ул. Иллюстративная, 6"),
            (123456795, "Павел Р.", "+7900789****", "ул. Модельная, 7"),
            (123456796, "Ольга М.", "+7900890****", "ул. Типовая, 8"),
            (123456797, "Игорь Ф.", "+7900901****", "ул. Стандартная, 9"),
            (123456798, "Татьяна Б.", "+7900012****", "ул. Шаблонная, 10")
        ]
        
        await db.executemany(
            "INSERT OR IGNORE INTO users (user_id, name, phone, address) VALUES (?, ?, ?, ?)",
            test_users
        )
        
        # Создаем тестовые заказы для отзывов
        test_orders = []
        for i, (user_id, _, _, _) in enumerate(test_users, 1):
            test_orders.append((i, user_id, 1, "Тестовый адрес", "2024-12-01", "14:00", 1500, "completed"))
        
        await db.executemany(
            "INSERT OR IGNORE INTO orders (id, user_id, master_id, address, order_date, order_time, total_cost, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            test_orders
        )

        # Добавляем тестовые отзывы
        reviews = [
            (123456789, 1, 5, "Отличная работа! Мастер быстро диагностировал проблему и все исправил."),
            (123456790, 2, 4, "Хорошее обслуживание, но пришлось немного подождать."),
            (123456791, 3, 5, "Профессиональный подход, все объяснили понятно."),
            (123456792, 4, 5, "Компьютер работает как новый! Спасибо!"),
            (123456793, 5, 4, "Качественная работа за разумные деньги."),
            (123456794, 6, 5, "Быстро и качественно! Рекомендую!"),
            (123456795, 7, 4, "Мастер вежливый и аккуратный."),
            (123456796, 8, 5, "Проблема решена полностью, никаких нареканий."),
            (123456797, 9, 5, "Отличный сервис! Буду обращаться еще."),
            (123456798, 10, 4, "Все сделано профессионально и в срок.")
        ]
        
        await db.executemany(
            "INSERT OR IGNORE INTO reviews (user_id, order_id, rating, comment) VALUES (?, ?, ?, ?)",
            reviews
        )
    
    @handle_db_errors
    async def check_db_health(self) -> bool:
        """Проверка состояния базы данных"""
        async with get_db_connection(self.db_path) as db:
            tables = ['users', 'services', 'masters', 'orders', 'reviews']
            for table in tables:
                cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
                count = await cursor.fetchone()
                logging.info(f"Таблица {table}: {count[0] if count else 0} записей")
            return True
    
    async def backup_database(self, backup_path: str):
        """Создание резервной копии базы данных"""
        try:
            async with aiosqlite.connect(self.db_path) as source:
                async with aiosqlite.connect(backup_path) as backup:
                    await source.backup(backup)
            logging.info(f"Резервная копия создана: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Ошибка создания резервной копии: {e}")
            return False