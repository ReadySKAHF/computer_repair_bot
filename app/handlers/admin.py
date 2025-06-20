"""
Обработчики админ-панели
"""
import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..database.queries import DatabaseQueries
from ..config import BotConfig
from ..keyboards.main_menu import get_main_menu_keyboard


# Создаем роутер для админки
admin_router = Router()


def is_admin(user_id: int, config: BotConfig) -> bool:
    """Проверка, является ли пользователь админом"""
    return user_id in config.admin_ids


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура админ-панели"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders"),
            InlineKeyboardButton(text="💬 Поддержка", callback_data="admin_support")
        ],
        [
            InlineKeyboardButton(text="🤖 ИИ сервис", callback_data="admin_ai"),
            InlineKeyboardButton(text="🔧 Настройки", callback_data="admin_settings")
        ],
        [
            InlineKeyboardButton(text="📥 Бэкап БД", callback_data="admin_backup"),
            InlineKeyboardButton(text="🔄 Перезагрузка", callback_data="admin_reload")
        ],
        [
            InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")
        ]
    ])
    return keyboard


@admin_router.message(Command("admin"))
async def show_admin_panel(message: Message, state: FSMContext, db_queries: DatabaseQueries):
    """Показ админ-панели"""
    # ЗАМЕНИТЕ НА ВАШИ TELEGRAM ID
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if message.from_user.id not in admin_ids:
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        # Получаем базовую статистику
        stats = await db_queries.get_statistics()
        
        text = "🔧 **Админ-панель**\n\n"
        text += f"**Краткая статистика:**\n"
        text += f"👥 Пользователей: {stats.get('total_users', 0)}\n"
        text += f"📋 Заказов: {stats.get('total_orders', 0)}\n"
        text += f"⭐ Средний рейтинг: {stats.get('average_rating', 0)}\n"
        text += f"💬 Обращений сегодня: {stats.get('support_requests_today', 0)}\n\n"
        text += "Выберите раздел для управления:"
        
        keyboard = get_admin_main_keyboard()
        await message.answer(text, reply_markup=keyboard, parse_mode='Markdown')
        await state.clear()
    
    except Exception as e:
        logging.error(f"Ошибка в show_admin_panel: {e}")
        await message.answer("❌ Ошибка при загрузке админ-панели")


@admin_router.callback_query(F.data == "admin_stats")
async def show_admin_statistics(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Показ детальной статистики"""
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        stats = await db_queries.get_statistics()
        
        # Получаем дополнительную статистику по заказам
        # Создаем временный метод для получения всех заказов
        status_counts = {
            'pending': 0,
            'confirmed': 0,
            'in_progress': 0,
            'completed': 0,
            'cancelled': 0
        }
        total_revenue = 0
        
        # Пытаемся получить статистику из существующих методов
        try:
            # Получаем заказы разных пользователей для статистики
            sample_orders = []
            for user_id in range(1, 100):  # Простой способ собрать заказы
                user_orders = await db_queries.get_user_orders(user_id, 50)
                if user_orders:
                    sample_orders.extend(user_orders)
            
            for order in sample_orders:
                status = order.get('status', 'unknown')
                if status in status_counts:
                    status_counts[status] += 1
                
                if status == 'completed':
                    total_revenue += order.get('total_cost', 0)
        
        except Exception:
            # Если не удалось собрать статистику, показываем базовую
            pass
        
        text = "📊 **Детальная статистика**\n\n"
        text += f"**Пользователи:**\n"
        text += f"• Всего зарегистрировано: {stats.get('total_users', 0)}\n\n"
        
        text += f"**Заказы:**\n"
        text += f"• Всего: {stats.get('total_orders', 0)}\n"
        text += f"• Сегодня: {stats.get('orders_today', 0)}\n"
        
        status_names = {
            'pending': 'Ожидают',
            'confirmed': 'Подтверждены',
            'in_progress': 'В работе',
            'completed': 'Выполнены',
            'cancelled': 'Отменены'
        }
        
        for status, count in status_counts.items():
            if count > 0:
                status_name = status_names.get(status, status)
                text += f"• {status_name}: {count}\n"
        
        text += f"\n**Финансы:**\n"
        text += f"• Общая выручка: {total_revenue}₽\n"
        
        text += f"\n**Отзывы:**\n"
        text += f"• Всего отзывов: {stats.get('total_reviews', 0)}\n"
        text += f"• Средний рейтинг: {stats.get('average_rating', 0)}\n"
        
        text += f"\n**Поддержка:**\n"
        text += f"• Обращений сегодня: {stats.get('support_requests_today', 0)}\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_admin_statistics: {e}")
        await callback.answer("❌ Ошибка при загрузке статистики")


@admin_router.callback_query(F.data == "admin_orders")
async def show_admin_orders(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Управление заказами"""
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        text = "📋 **Управление заказами**\n\n"
        text += "**Доступные команды:**\n\n"
        text += "`/admin_complete <ID>` - завершить заказ\n"
        text += "`/admin_cancel <ID>` - отменить заказ\n"
        text += "`/admin_orders` - показать ваши заказы\n\n"
        text += "**Пример использования:**\n"
        text += "`/admin_complete 15` - завершить заказ №15\n\n"
        text += "Для просмотра ваших заказов используйте команду `/admin_orders`"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика заказов", callback_data="admin_orders_stats")],
            [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_admin_orders: {e}")
        await callback.answer("❌ Ошибка при загрузке заказов")


@admin_router.callback_query(F.data == "admin_users")
async def show_admin_users(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Управление пользователями"""
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        stats = await db_queries.get_statistics()
        
        text = "👥 **Управление пользователями**\n\n"
        text += f"**Общая информация:**\n"
        text += f"• Всего пользователей: {stats.get('total_users', 0)}\n"
        text += f"• Активных сегодня: подсчет в разработке\n"
        text += f"• Новых за неделю: подсчет в разработке\n\n"
        
        text += f"**Доступные действия:**\n"
        text += f"• Просмотр статистики пользователей\n"
        text += f"• Мониторинг активности\n"
        text += f"• Управление правами доступа\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика активности", callback_data="admin_user_stats")],
            [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_admin_users: {e}")
        await callback.answer("❌ Ошибка при загрузке пользователей")


@admin_router.callback_query(F.data == "admin_support")
async def show_admin_support(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Управление поддержкой"""
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        support_requests = await db_queries.get_support_requests(10)
        
        text = "💬 **Обращения в поддержку**\n\n"
        
        if not support_requests:
            text += "Обращений пока нет.\n"
        else:
            text += f"**Последние {len(support_requests)} обращений:**\n\n"
            
            for request in support_requests:
                user_name = request['user_name']
                message_preview = request['message'][:50] + "..." if len(request['message']) > 50 else request['message']
                created_at = request['created_at'][:16] if request['created_at'] else ""
                
                text += f"**{user_name}** _{created_at}_\n"
                text += f"{message_preview}\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_support")],
            [InlineKeyboardButton(text="📊 Статистика поддержки", callback_data="admin_support_stats")],
            [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_admin_support: {e}")
        await callback.answer("❌ Ошибка при загрузке обращений")


@admin_router.callback_query(F.data == "admin_ai")
async def show_admin_ai(callback: CallbackQuery, ai_service):
    """Управление ИИ сервисом"""
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        # Проверяем статус ИИ сервиса
        is_available = ai_service.check_service_availability() if ai_service else False
        
        text = "🤖 **Управление ИИ сервисом**\n\n"
        text += f"**Статус сервиса:** {'🟢 Доступен' if is_available else '🔴 Недоступен'}\n"
        text += f"**Модель:** Gemini 1.5 Flash\n"
        text += f"**Резервная логика:** Включена\n\n"
        
        if is_available:
            text += "✅ ИИ консультант работает нормально\n"
            text += "Пользователи получают полные рекомендации от ИИ"
        else:
            text += "❌ Проблемы с ИИ сервисом\n"
            text += "Пользователи получают рекомендации на основе ключевых слов"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Проверить статус", callback_data="admin_ai_check")],
            [InlineKeyboardButton(text="📊 Статистика ИИ", callback_data="admin_ai_stats")],
            [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_admin_ai: {e}")
        await callback.answer("❌ Ошибка при загрузке статуса ИИ")


@admin_router.callback_query(F.data == "admin_backup")
async def create_backup(callback: CallbackQuery):
    """Создание резервной копии"""
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        from ..database.connection import DatabaseManager
        
        # Создаем бэкап
        db_manager = DatabaseManager()
        backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        success = await db_manager.backup_database(backup_path)
        
        if success:
            text = f"✅ **Резервная копия создана**\n\n"
            text += f"Файл: `{backup_path}`\n"
            text += f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        else:
            text = "❌ **Ошибка создания резервной копии**\n\n"
            text += "Проверьте логи для получения подробностей."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Создать еще один", callback_data="admin_backup")],
            [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в create_backup: {e}")
        await callback.answer("❌ Ошибка при создании резервной копии")


@admin_router.callback_query(F.data == "admin_main")
async def back_to_admin_main(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Возврат к главной админ-панели"""
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        stats = await db_queries.get_statistics()
        
        text = "🔧 **Админ-панель**\n\n"
        text += f"**Краткая статистика:**\n"
        text += f"👥 Пользователей: {stats.get('total_users', 0)}\n"
        text += f"📋 Заказов: {stats.get('total_orders', 0)}\n"
        text += f"⭐ Средний рейтинг: {stats.get('average_rating', 0)}\n"
        text += f"💬 Обращений сегодня: {stats.get('support_requests_today', 0)}\n\n"
        text += "Выберите раздел для управления:"
        
        keyboard = get_admin_main_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в back_to_admin_main: {e}")
        await callback.answer("❌ Ошибка при загрузке админ-панели")


# === АДМИНСКИЕ КОМАНДЫ ===

@admin_router.message(Command("admin_complete"))
async def admin_complete_order(message: Message, db_queries: DatabaseQueries):
    """Админская команда завершения заказа"""
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if message.from_user.id not in admin_ids:
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.answer(
                "**Использование:** `/admin_complete <order_id>`\n\n"
                "**Пример:** `/admin_complete 15`",
                parse_mode='Markdown'
            )
            return
        
        order_id = int(command_parts[1])
        success = await db_queries.update_order_status(order_id, 'completed')
        
        if success:
            await message.answer(f"✅ Заказ №{order_id} переведен в статус 'completed'")
        else:
            await message.answer(f"❌ Ошибка обновления заказа №{order_id}")
    
    except ValueError:
        await message.answer("❌ Некорректный ID заказа. Используйте число.")
    except Exception as e:
        logging.error(f"Ошибка в admin_complete_order: {e}")
        await message.answer(f"❌ Ошибка: {e}")


@admin_router.message(Command("admin_cancel"))
async def admin_cancel_order(message: Message, db_queries: DatabaseQueries):
    """Админская команда отмены заказа"""
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if message.from_user.id not in admin_ids:
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.answer(
                "**Использование:** `/admin_cancel <order_id>`\n\n"
                "**Пример:** `/admin_cancel 15`",
                parse_mode='Markdown'
            )
            return
        
        order_id = int(command_parts[1])
        success = await db_queries.update_order_status(order_id, 'cancelled')
        
        if success:
            await message.answer(f"✅ Заказ №{order_id} отменен")
        else:
            await message.answer(f"❌ Ошибка отмены заказа №{order_id}")
    
    except ValueError:
        await message.answer("❌ Некорректный ID заказа. Используйте число.")
    except Exception as e:
        logging.error(f"Ошибка в admin_cancel_order: {e}")
        await message.answer(f"❌ Ошибка: {e}")


@admin_router.message(Command("admin_orders"))
async def show_admin_user_orders(message: Message, db_queries: DatabaseQueries):
    """Показ заказов админа для тестирования"""
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if message.from_user.id not in admin_ids:
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        # Получаем заказы админа
        orders = await db_queries.get_user_orders(message.from_user.id, 10)
        
        if not orders:
            await message.answer(
                "📋 **Ваши заказы**\n\n"
                "У вас нет заказов.\n\n"
                "Создайте тестовый заказ через:\n"
                "🛠️ Сделать заказ → выберите услуги → оформите заказ"
            )
            return
        
        text = "📋 **Ваши заказы для управления:**\n\n"
        
        for order in orders:
            order_id = order['id']
            status = order['status']
            date = order['order_date']
            cost = order['total_cost']
            
            status_emoji = {
                'pending': '⏳',
                'confirmed': '✅', 
                'in_progress': '🔧',
                'completed': '✅',
                'cancelled': '❌'
            }.get(status, '❓')
            
            text += f"{status_emoji} **Заказ №{order_id}**\n"
            text += f"├ Статус: {status}\n"
            text += f"├ Дата: {date}\n"
            text += f"└ Стоимость: {cost}₽\n\n"
        
        text += "**Команды для управления:**\n"
        text += f"`/admin_complete {orders[0]['id']}` - завершить заказ №{orders[0]['id']}\n"
        text += f"`/admin_cancel {orders[0]['id']}` - отменить заказ №{orders[0]['id']}"
        
        await message.answer(text, parse_mode='Markdown')
    
    except Exception as e:
        logging.error(f"Ошибка в show_admin_user_orders: {e}")
        await message.answer("❌ Ошибка при загрузке заказов")


@admin_router.message(Command("get_id"))
async def get_user_id(message: Message):
    """Команда для получения своего Telegram ID"""
    await message.answer(
        f"🆔 **Ваш Telegram ID:** `{message.from_user.id}`\n\n"
        f"**Информация:**\n"
        f"• Имя: {message.from_user.first_name or 'Не указано'}\n"
        f"• Username: @{message.from_user.username or 'Не указан'}\n"
        f"• ID: `{message.from_user.id}`\n\n"
        f"💡 **Для настройки админки:**\n"
        f"Замените в коде `admin_ids = [123456789, 987654321]`\n"
        f"на `admin_ids = [{message.from_user.id}]`",
        parse_mode='Markdown'
    )


@admin_router.message(Command("admin_help"))
async def show_admin_help(message: Message):
    """Справка по админским командам"""
    admin_ids = [123456789, 987654321]  # ← ВСТАВЬТЕ СВОИ ID СЮДА
    
    if message.from_user.id not in admin_ids:
        await message.answer("❌ Доступ запрещен")
        return
    
    text = "🔧 **Справка по админским командам**\n\n"
    text += "**Основные команды:**\n"
    text += "`/admin` - главная админ-панель\n"
    text += "`/get_id` - узнать свой Telegram ID\n"
    text += "`/admin_help` - эта справка\n\n"
    
    text += "**Управление заказами:**\n"
    text += "`/admin_orders` - показать ваши заказы\n"
    text += "`/admin_complete <ID>` - завершить заказ\n"
    text += "`/admin_cancel <ID>` - отменить заказ\n\n"
    
    text += "**Примеры использования:**\n"
    text += "`/admin_complete 15` - завершить заказ №15\n"
    text += "`/admin_cancel 20` - отменить заказ №20\n\n"
    
    text += "**Админ-панель включает:**\n"
    text += "• 📊 Статистику бота\n"
    text += "• 👥 Управление пользователями\n"
    text += "• 💬 Обращения в поддержку\n"
    text += "• 🤖 Статус ИИ сервиса\n"
    text += "• 📥 Создание бэкапов БД"
    
    await message.answer(text, parse_mode='Markdown')