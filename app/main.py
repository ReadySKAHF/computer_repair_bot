"""
Основной файл запуска бота (обновленная версия)
"""
import asyncio
import logging
import sys
from typing import Any, Dict

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext

# Импорты модулей приложения
from .config import ConfigLoader, setup_logging, validate_config, BotConfig
from .database.connection import DatabaseManager
from .database.queries import DatabaseQueries
from .services.ai_service import AIConsultationService
from .keyboards.main_menu import get_main_menu_keyboard, get_main_menu_inline_keyboard
from .utils.constants import CALLBACK_DATA


class RepairBot:
    """Основной класс бота"""
    
    def __init__(self, config_path: str = "config.txt"):
        """Инициализация бота"""
        # Загружаем конфигурацию
        self.config = ConfigLoader.load_from_file(config_path)
        
        # Валидируем конфигурацию
        if not validate_config(self.config):
            raise ValueError("Некорректная конфигурация")
        
        # Настраиваем логирование
        self.logger = setup_logging(self.config)
        
        # Инициализируем компоненты
        self.bot = Bot(token=self.config.bot_token)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        
        # Инициализируем сервисы
        self.db_manager = DatabaseManager(self.config.db_path)
        self.db_queries = DatabaseQueries(self.config.db_path)
        self.ai_service = AIConsultationService(self.config.gemini_api_key)
        
        # Инициализируем бизнес-сервисы после создания db_queries
        from .services.order_service import OrderService
        self.order_service = None  # Будет инициализирован в setup_middleware
        
        self.logger.info("✅ Компоненты бота инициализированы")
    
    async def setup_database(self):
        """Настройка базы данных"""
        try:
            await self.db_manager.init_database()
            await self.db_manager.populate_test_data()
            
            # Проверяем здоровье БД
            health_check = await self.db_manager.check_db_health()
            if health_check:
                self.logger.info("✅ База данных готова к работе")
            else:
                raise Exception("Проблемы с базой данных")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка настройки базы данных: {e}")
            raise
    
    def setup_routers(self):
        """Настройка роутеров"""
        try:
            # Импортируем роутеры напрямую (зависимости поступают через middleware)
            from .handlers.registration import registration_router
            from .handlers.orders import orders_router
            from .handlers.services import services_router
            from .handlers.profile import profile_router
            from .handlers.reviews import reviews_router
            from .handlers.ai_consultation import ai_router
            from .handlers.support import support_router
            from .handlers.admin import admin_router
            
            # Добавляем роутеры в диспетчер (порядок важен!)
            self.dp.include_router(registration_router)
            self.dp.include_router(admin_router)
            self.dp.include_router(orders_router)
            self.dp.include_router(services_router)
            self.dp.include_router(profile_router)
            self.dp.include_router(reviews_router)
            self.dp.include_router(ai_router)
            self.dp.include_router(support_router)
            
            # Обработчик для make_order callback
            @self.dp.callback_query(F.data == "make_order")
            async def handle_make_order_callback(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries, user):
                """Обработчик кнопки 'Сделать заказ' из inline клавиатур"""
                if not user:
                    await callback.answer("❌ Для создания заказа необходимо зарегистрироваться!")
                    return
                
                try:
                    # Удаляем текущее сообщение
                    await callback.message.delete()
                    
                    # Отправляем новое сообщение с ReplyKeyboardMarkup  
                    await callback.message.answer(
                        "🛠️ **Создание заказа**\n\nИспользуйте кнопку «🛠️ Сделать заказ» в главном меню для создания заказа.",
                        reply_markup=get_main_menu_keyboard(),
                        parse_mode='Markdown'
                    )
                    await callback.answer()
                except Exception as e:
                    logging.error(f"Ошибка в handle_make_order_callback: {e}")
                    await callback.answer("Используйте кнопку '🛠️ Сделать заказ' в главном меню")
            
            # Админские команды для тестирования
            @self.dp.message(F.text.startswith("/admin"))
            async def handle_admin_commands(message: Message, db_queries: DatabaseQueries, config: BotConfig):
                """Админские команды для тестирования"""
                if not config.is_admin(message.from_user.id):
                    await message.answer("❌ Доступ запрещен")
                    return
                
                try:
                    command_parts = message.text.split()
                    command = command_parts[0]
                    
                    if command == "/admin_complete":
                        # Команда: /admin_complete 12 (завершить заказ №12)
                        if len(command_parts) < 2:
                            await message.answer("Использование: /admin_complete <order_id>")
                            return
                        
                        order_id = int(command_parts[1])
                        success = await db_queries.update_order_status(order_id, 'completed')
                        
                        if success:
                            await message.answer(f"✅ Заказ №{order_id} переведен в статус 'completed'")
                        else:
                            await message.answer(f"❌ Ошибка обновления заказа №{order_id}")
                    
                    elif command == "/admin_orders":
                        # Показать все заказы пользователя
                        orders = await db_queries.get_user_orders(message.from_user.id, 10)
                        
                        if not orders:
                            await message.answer("У вас нет заказов")
                            return
                        
                        text = "📋 **Ваши заказы:**\n\n"
                        for order in orders:
                            order_id = order['id']
                            status = order['status']
                            date = order['order_date']
                            text += f"№{order_id} - {status} ({date})\n"
                        
                        text += f"\n💡 Для завершения заказа используйте:\n`/admin_complete {orders[0]['id']}`"
                        
                        await message.answer(text, parse_mode='Markdown')
                    
                    elif command == "/admin_help":
                        await message.answer(
                            "🔧 **Админские команды:**\n\n"
                            "`/admin_orders` - показать ваши заказы\n"
                            "`/admin_complete <id>` - завершить заказ\n"
                            "`/admin_help` - эта справка\n\n"
                            "**Пример:** `/admin_complete 12`",
                            parse_mode='Markdown'
                        )
                    
                    else:
                        await message.answer("❓ Неизвестная команда. Используйте `/admin_help`")
                
                except Exception as e:
                    logging.error(f"Ошибка в admin командах: {e}")
                    await message.answer(f"❌ Ошибка: {e}")
            
            # Создаем роутер для общих обработчиков (должен быть последним)
            general_router = Router()
            
            # Добавляем общие обработчики в отдельный роутер
            general_router.message.register(self.handle_unknown_message)
            general_router.callback_query.register(self.handle_main_menu_callback, F.data == CALLBACK_DATA['MAIN_MENU'])
            general_router.callback_query.register(self.handle_unknown_callback)
            
            # Добавляем общий роутер последним (низкий приоритет)
            self.dp.include_router(general_router)
            
            self.logger.info("✅ Роутеры настроены")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка настройки роутеров: {e}")
            raise
    
    def setup_middleware(self):
        """Настройка middleware"""
        try:
            # Инициализируем order_service здесь, когда db_queries уже готов
            from .services.order_service import OrderService
            self.order_service = OrderService(self.db_queries)
            
            # Middleware для передачи зависимостей
            async def inject_dependencies(handler, event, data: Dict[str, Any]):
                data['db_queries'] = self.db_queries
                data['ai_service'] = self.ai_service
                data['order_service'] = self.order_service
                data['config'] = self.config  # Добавляем конфиг
                
                # Добавляем информацию о пользователе для всех обработчиков
                if hasattr(event, 'from_user') and event.from_user:
                    user = await self.db_queries.get_user(event.from_user.id)
                    data['user'] = user
                    data['is_registered'] = user is not None
                    data['is_admin'] = self.config.is_admin(event.from_user.id)  # Добавляем проверку админа
                
                return await handler(event, data)
            
            # Регистрируем middleware
            self.dp.message.middleware(inject_dependencies)
            self.dp.callback_query.middleware(inject_dependencies)
            
            self.logger.info("✅ Middleware настроены")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка настройки middleware: {e}")
            raise
    
    async def handle_main_menu_callback(self, callback: CallbackQuery, state, **kwargs):
        """Обработчик возврата в главное меню"""
        await state.clear()
        
        # Удаляем текущее inline сообщение
        try:
            await callback.message.delete()
        except:
            pass
        
        # Отправляем новое сообщение с ReplyKeyboardMarkup
        await callback.message.answer(
            "🏠 **Главное меню**\n\nВыберите нужную опцию:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        await callback.answer()
    
    async def handle_unknown_message(self, message: Message):
        """Обработчик неизвестных сообщений"""
        self.logger.warning(f"Неизвестное сообщение от {message.from_user.id}: {message.text}")
        
        await message.answer(
            "🤔 Не понимаю, что вы имеете в виду.\n\n"
            "Используйте кнопки меню для навигации или команду /start для начала работы.",
            reply_markup=get_main_menu_keyboard()
        )
    
    async def handle_unknown_callback(self, callback: CallbackQuery):
        """Обработчик неизвестных callback'ов"""
        self.logger.warning(f"Неизвестный callback от {callback.from_user.id}: {callback.data}")
        
        await callback.answer("Неизвестная команда. Используйте главное меню.")
        
        # Удаляем текущее сообщение и отправляем главное меню
        try:
            await callback.message.delete()
        except:
            pass
        
        await callback.message.answer(
            "🏠 **Главное меню**\n\nВыберите нужную опцию:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    async def setup_error_handlers(self):
        """Настройка обработчиков ошибок"""
        @self.dp.error()
        async def error_handler(event, exception):
            """Глобальный обработчик ошибок"""
            self.logger.error(f"Критическая ошибка: {exception}", exc_info=True)
            
            # Пытаемся уведомить пользователя
            try:
                if hasattr(event, 'message') and event.message:
                    await event.message.answer(
                        "😔 Произошла неожиданная ошибка.\n"
                        "Попробуйте еще раз или обратитесь в поддержку.",
                        reply_markup=get_main_menu_keyboard()
                    )
                elif hasattr(event, 'callback_query') and event.callback_query:
                    await event.callback_query.message.answer(
                        "😔 Произошла неожиданная ошибка.\n"
                        "Попробуйте еще раз или обратитесь в поддержку.",
                        reply_markup=get_main_menu_keyboard()
                    )
            except:
                pass  # Если не можем отправить сообщение, просто логируем
            
            return True  # Помечаем ошибку как обработанную
    
    async def on_startup(self):
        """Действия при запуске бота"""
        try:
            self.logger.info("🚀 Запуск бота...")
            
            # Настраиваем базу данных
            await self.setup_database()
            
            # ВАЖНО: Сначала middleware, потом роутеры!
            self.setup_middleware()
            
            # Теперь роутеры (они получат правильные зависимости)
            self.setup_routers()
            
            # Настраиваем обработчики ошибок
            await self.setup_error_handlers()
            
            # Проверяем ИИ сервис
            if self.ai_service.is_available:
                self.logger.info("✅ ИИ сервис доступен")
            else:
                self.logger.warning("⚠️ ИИ сервис недоступен, будет использоваться резервная логика")
            
            # Получаем информацию о боте
            bot_info = await self.bot.get_me()
            self.logger.info(f"✅ Бот @{bot_info.username} успешно запущен!")
            self.logger.info(f"📊 Конфигурация: {self.config.log_level} уровень логирования")
            self.logger.info(f"💾 База данных: {self.config.db_path}")
            self.logger.info(f"👤 Админы: {self.config.admin_ids}")
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка при запуске: {e}")
            raise
    
    async def on_shutdown(self):
        """Действия при остановке бота"""
        try:
            self.logger.info("🛑 Остановка бота...")
            
            # Создаем резервную копию БД
            backup_path = f"backup_{self.config.db_path}"
            await self.db_manager.backup_database(backup_path)
            
            # Закрываем сессию бота
            await self.bot.session.close()
            
            self.logger.info("✅ Бот успешно остановлен")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка при остановке бота: {e}")
    
    async def run(self):
        """Запуск бота"""
        try:
            # Выполняем действия при запуске
            await self.on_startup()
            
            # Запускаем polling
            await self.dp.start_polling(
                self.bot,
                on_startup=None,  # Уже выполнили
                on_shutdown=self.on_shutdown
            )
            
        except KeyboardInterrupt:
            self.logger.info("👋 Получен сигнал остановки")
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка работы: {e}")
            raise
        finally:
            await self.on_shutdown()


async def main():
    """Главная функция"""
    try:
        # Создаем и запускаем бота
        bot = RepairBot()
        await bot.run()
        
    except Exception as e:
        logging.error(f"❌ Критическая ошибка приложения: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Запускаем бота
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)