"""
Обработчики админ-панели (обновленная версия)
"""
import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from ..database.queries import DatabaseQueries
from ..config import BotConfig
from ..keyboards.main_menu import get_main_menu_keyboard


# Создаем роутер для админки
admin_router = Router()


# Состояния для ответа на поддержку
class AdminSupportStates(StatesGroup):
    responding_to_request = State()


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Главная клавиатура админ-панели"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="📋 Все заказы", callback_data="admin_all_orders"),
            InlineKeyboardButton(text="💬 Поддержка", callback_data="admin_support_management")
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
async def show_admin_panel(message: Message, state: FSMContext, db_queries: DatabaseQueries, config: BotConfig):
    """Показ админ-панели"""
    if not config.is_admin(message.from_user.id):
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
async def show_admin_statistics(callback: CallbackQuery, db_queries: DatabaseQueries, config: BotConfig):
    """Показ детальной статистики"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        stats = await db_queries.get_statistics()
        
        # Получаем дополнительную статистику по заказам
        status_counts = {
            'pending': await db_queries.get_orders_count('pending'),
            'confirmed': await db_queries.get_orders_count('confirmed'),
            'in_progress': await db_queries.get_orders_count('in_progress'),
            'completed': await db_queries.get_orders_count('completed'),
            'cancelled': await db_queries.get_orders_count('cancelled')
        }
        
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


# === УПРАВЛЕНИЕ ЗАКАЗАМИ ===

@admin_router.callback_query(F.data == "admin_all_orders")
async def show_all_orders_management(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries, config: BotConfig):
    """Управление всеми заказами"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        # Получаем статистику по заказам
        total_orders = await db_queries.get_orders_count()
        pending_orders = await db_queries.get_orders_count('pending')
        completed_orders = await db_queries.get_orders_count('completed')
        
        # Получаем последние заказы
        recent_orders = await db_queries.get_all_orders(10)
        
        text = "📋 **Управление всеми заказами**\n\n"
        text += f"**Статистика:**\n"
        text += f"• Всего заказов: {total_orders}\n"
        text += f"• Ожидают: {pending_orders}\n"
        text += f"• Выполнено: {completed_orders}\n\n"
        
        text += f"**Последние заказы:**\n"
        for order in recent_orders[:5]:
            status_emoji = {"pending": "⏳", "confirmed": "✅", "in_progress": "🔧", "completed": "✅", "cancelled": "❌"}.get(order['status'], "❓")
            text += f"{status_emoji} №{order['id']} - {order['user_name']} ({order['status']})\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Список заказов", callback_data="admin_orders_list"),
                InlineKeyboardButton(text="🔄 По статусам", callback_data="admin_orders_by_status")
            ],
            [
                InlineKeyboardButton(text="✅ Завершить все", callback_data="admin_complete_all_orders"),
                InlineKeyboardButton(text="❌ Отменить все", callback_data="admin_cancel_all_orders")
            ],
            [
                InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_main")
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_all_orders_management: {e}")
        await callback.answer("❌ Ошибка при загрузке заказов")


@admin_router.callback_query(F.data == "admin_orders_list")
async def show_orders_list(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries, config: BotConfig):
    """Показ списка всех заказов"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        orders = await db_queries.get_all_orders(20)
        
        if not orders:
            text = "📋 **Все заказы**\n\nЗаказов пока нет."
        else:
            text = f"📋 **Все заказы** (показано {len(orders)})\n\n"
            
            for order in orders:
                status_emoji = {
                    "pending": "⏳", "confirmed": "✅", "in_progress": "🔧", 
                    "completed": "✅", "cancelled": "❌"
                }.get(order['status'], "❓")
                
                text += f"{status_emoji} **№{order['id']}** - {order['user_name']}\n"
                text += f"├ Статус: {order['status']}\n"
                text += f"├ Дата: {order['order_date']} в {order['order_time']}\n"
                text += f"├ Стоимость: {order['total_cost']}₽\n"
                text += f"└ Услуги: {order['services'][:50]}...\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⏳ Ожидающие", callback_data="admin_filter_pending"),
                InlineKeyboardButton(text="🔧 В работе", callback_data="admin_filter_progress")
            ],
            [
                InlineKeyboardButton(text="✅ Завершить все активные", callback_data="admin_complete_all_orders")
            ],
            [
                InlineKeyboardButton(text="🔙 Управление заказами", callback_data="admin_all_orders")
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_orders_list: {e}")
        await callback.answer("❌ Ошибка при загрузке списка заказов")


@admin_router.callback_query(F.data == "admin_complete_all_orders")
async def complete_all_orders(callback: CallbackQuery, db_queries: DatabaseQueries, config: BotConfig):
    """Завершение всех активных заказов"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, завершить все", callback_data="confirm_complete_all"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="admin_all_orders")
        ]
    ])
    
    await callback.message.edit_text(
        "⚠️ **Подтверждение массового завершения**\n\n"
        "Вы уверены, что хотите завершить ВСЕ активные заказы?\n"
        "Это действие нельзя отменить!",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    await callback.answer()


@admin_router.callback_query(F.data == "confirm_complete_all")
async def confirm_complete_all_orders(callback: CallbackQuery, db_queries: DatabaseQueries, config: BotConfig):
    """Подтверждение завершения всех заказов"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        success = await db_queries.bulk_update_orders_status('completed')
        
        if success:
            text = "✅ **Массовое завершение выполнено**\n\nВсе активные заказы переведены в статус 'completed'"
        else:
            text = "❌ **Ошибка массового завершения**\n\nНе удалось обновить статусы заказов"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Проверить заказы", callback_data="admin_orders_list")],
            [InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_main")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
        
        logging.info(f"Админ {callback.from_user.id} завершил все активные заказы")
    
    except Exception as e:
        logging.error(f"Ошибка в confirm_complete_all_orders: {e}")
        await callback.answer("❌ Ошибка при завершении заказов")


# === УПРАВЛЕНИЕ ПОДДЕРЖКОЙ ===

@admin_router.callback_query(F.data == "admin_support_management")
async def show_support_management(callback: CallbackQuery, db_queries: DatabaseQueries, config: BotConfig):
    """Управление обращениями в поддержку"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        # Получаем статистику обращений
        all_requests = await db_queries.get_support_requests_for_admin()
        new_requests = await db_queries.get_support_requests_for_admin('new')
        answered_requests = await db_queries.get_support_requests_for_admin('answered')
        
        text = "💬 **Управление поддержкой**\n\n"
        text += f"**Статистика:**\n"
        text += f"• Всего обращений: {len(all_requests) if all_requests else 0}\n"
        text += f"• Новых: {len(new_requests) if new_requests else 0}\n"
        text += f"• Отвеченных: {len(answered_requests) if answered_requests else 0}\n\n"
        
        if new_requests:
            text += f"**Новые обращения:**\n"
            for req in new_requests[:3]:
                preview = req['message'][:50] + "..." if len(req['message']) > 50 else req['message']
                text += f"• {req['user_name']}: {preview}\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Новые обращения", callback_data="admin_new_support"),
                InlineKeyboardButton(text="✅ Отвеченные", callback_data="admin_answered_support")
            ],
            [
                InlineKeyboardButton(text="📋 Все обращения", callback_data="admin_all_support")
            ],
            [
                InlineKeyboardButton(text="🔙 Админ-панель", callback_data="admin_main")
            ]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_support_management: {e}")
        await callback.answer("❌ Ошибка при загрузке управления поддержкой")


@admin_router.callback_query(F.data == "admin_new_support")
async def show_new_support_requests(callback: CallbackQuery, db_queries: DatabaseQueries, config: BotConfig):
    """Показ новых обращений в поддержку"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        new_requests = await db_queries.get_support_requests_for_admin('new', 10)
        
        if not new_requests:
            text = "📝 **Новые обращения**\n\nНовых обращений нет!"
        else:
            text = f"📝 **Новые обращения** ({len(new_requests)})\n\n"
            
            for req in new_requests:
                text += f"**#{req['id']} от {req['user_name']}**\n"
                text += f"📞 {req['user_phone']}\n"
                text += f"📅 {req['created_at']}\n"
                text += f"💬 {req['message']}\n\n"
        
        # Создаем кнопки для ответа на каждое обращение
        keyboard_buttons = []
        if new_requests:
            for req in new_requests[:5]:  # Показываем кнопки для первых 5
                keyboard_buttons.append([
                    InlineKeyboardButton(
                        text=f"💬 Ответить #{req['id']}", 
                        callback_data=f"admin_respond_{req['id']}"
                    )
                ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Управление поддержкой", callback_data="admin_support_management")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_new_support_requests: {e}")
        await callback.answer("❌ Ошибка при загрузке новых обращений")


@admin_router.callback_query(F.data.startswith("admin_respond_"))
async def start_respond_to_support(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries, config: BotConfig):
    """Начало ответа на обращение в поддержку"""
    if not config.is_admin(callback.from_user.id):
        await callback.answer("❌ Доступ запрещен")
        return
    
    try:
        request_id = int(callback.data.split("_")[2])
        
        # Получаем информацию об обращении
        all_requests = await db_queries.get_support_requests_for_admin()
        request_info = next((r for r in all_requests if r['id'] == request_id), None)
        
        if not request_info:
            await callback.answer("Обращение не найдено")
            return
        
        # Сохраняем ID обращения в state
        await state.update_data(support_request_id=request_id)
        await state.set_state(AdminSupportStates.responding_to_request)
        
        text = f"💬 **Ответ на обращение #{request_id}**\n\n"
        text += f"**От:** {request_info['user_name']}\n"
        text += f"**Дата:** {request_info['created_at']}\n"
        text += f"**Сообщение:** {request_info['message']}\n\n"
        text += f"**Напишите ваш ответ:**"
        
        await callback.message.edit_text(text, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в start_respond_to_support: {e}")
        await callback.answer("❌ Ошибка при начале ответа")


@admin_router.message(AdminSupportStates.responding_to_request)
async def process_admin_response(message: Message, state: FSMContext, db_queries: DatabaseQueries, config: BotConfig):
    """Обработка ответа админа на обращение"""
    if not config.is_admin(message.from_user.id):
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        data = await state.get_data()
        request_id = data.get('support_request_id')
        
        if not request_id:
            await message.answer("❌ Ошибка: ID обращения не найден")
            await state.clear()
            return
        
        # Удаляем сообщение пользователя
        try:
            await message.delete()
        except:
            pass
        
        # Сохраняем ответ в БД
        success = await db_queries.respond_to_support_request(
            request_id, message.from_user.id, message.text
        )
        
        if success:
            await message.answer(
                f"✅ **Ответ отправлен!**\n\n"
                f"Ваш ответ на обращение #{request_id} сохранен.\n"
                f"Пользователь получит уведомление о том, что на его вопрос ответили.",
                parse_mode='Markdown'
            )
            logging.info(f"Админ {message.from_user.id} ответил на обращение {request_id}")
        else:
            await message.answer("❌ Ошибка при сохранении ответа")
        
        await state.clear()
    
    except Exception as e:
        logging.error(f"Ошибка в process_admin_response: {e}")
        await message.answer("❌ Ошибка при обработке ответа")
        await state.clear()


# === ОСТАЛЬНЫЕ ADMIN HANDLERS ===

@admin_router.callback_query(F.data == "admin_users")
async def show_admin_users(callback: CallbackQuery, db_queries: DatabaseQueries, config: BotConfig):
    """Управление пользователями"""
    if not config.is_admin(callback.from_user.id):
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


@admin_router.callback_query(F.data == "admin_ai")
async def show_admin_ai(callback: CallbackQuery, ai_service, config: BotConfig):
    """Управление ИИ сервисом"""
    if not config.is_admin(callback.from_user.id):
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
async def create_backup(callback: CallbackQuery, config: BotConfig):
    """Создание резервной копии"""
    if not config.is_admin(callback.from_user.id):
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
async def back_to_admin_main(callback: CallbackQuery, db_queries: DatabaseQueries, config: BotConfig):
    """Возврат к главной админ-панели"""
    if not config.is_admin(callback.from_user.id):
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
async def admin_complete_order(message: Message, db_queries: DatabaseQueries, config: BotConfig):
    """Админская команда завершения заказа"""
    if not config.is_admin(message.from_user.id):
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
async def admin_cancel_order(message: Message, db_queries: DatabaseQueries, config: BotConfig):
    """Админская команда отмены заказа"""
    if not config.is_admin(message.from_user.id):
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
async def show_admin_user_orders(message: Message, db_queries: DatabaseQueries, config: BotConfig):
    """Показ заказов админа для тестирования"""
    if not config.is_admin(message.from_user.id):
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
        f"Добавьте ваш ID в файл config.txt:\n"
        f"`ADMIN_IDS={message.from_user.id},1003589165`",
        parse_mode='Markdown'
    )


@admin_router.message(Command("admin_help"))
async def show_admin_help(message: Message, config: BotConfig):
    """Справка по админским командам"""
    if not config.is_admin(message.from_user.id):
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
    text += "• 📋 Управление всеми заказами\n"
    text += "• 💬 Обращения в поддержку с ответами\n"
    text += "• 🤖 Статус ИИ сервиса\n"
    text += "• 📥 Создание бэкапов БД"
    
    await message.answer(text, parse_mode='Markdown')

@admin_router.message(Command("get_id"))
async def get_user_id(message: Message):
    """Команда для получения своего Telegram ID"""
    user_id = message.from_user.id
    first_name = message.from_user.first_name or 'Не указано'
    username = message.from_user.username or 'Не указан'
    
    # Простое сообщение без Markdown
    text = f"🆔 Ваш Telegram ID: {user_id}\n\n"
    text += f"Информация:\n"
    text += f"• Имя: {first_name}\n"
    text += f"• Username: @{username}\n"
    text += f"• ID: {user_id}\n\n"
    text += f"💡 Для настройки админки:\n"
    text += f"Добавьте ваш ID в файл config.txt:\n"
    text += f"ADMIN_IDS={user_id},1003589165"
    
    await message.answer(text)

@admin_router.message(Command("check_admin"))
async def check_admin_status(message: Message, config: BotConfig):
    """Проверка админ статуса"""
    is_admin = config.is_admin(message.from_user.id)
    admin_ids = config.admin_ids
    
    text = f"🔍 Проверка админ статуса\n\n"
    text += f"Ваш ID: {message.from_user.id}\n"
    text += f"Админ статус: {'✅ ДА' if is_admin else '❌ НЕТ'}\n"
    text += f"Список админов: {admin_ids}\n\n"
    text += f"Содержится в списке: {'✅ ДА' if message.from_user.id in admin_ids else '❌ НЕТ'}"
    
    await message.answer(text)

@admin_router.message(Command("update_menu"))
async def force_update_menu(message: Message, config: BotConfig):
    """Принудительное обновление главного меню"""
    is_admin = config.is_admin(message.from_user.id)
    
    print(f"DEBUG force_update_menu: user_id = {message.from_user.id}")
    print(f"DEBUG force_update_menu: is_admin = {is_admin}")
    print(f"DEBUG force_update_menu: admin_ids = {config.admin_ids}")
    
    await message.answer(
        f"🔄 Обновление главного меню\n\n"
        f"Ваш статус: {'Администратор' if is_admin else 'Пользователь'}",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin)
    )

@admin_router.message(Command("test_admin"))
async def test_admin_button(message: Message, config: BotConfig):
    """Тест админ кнопки"""
    is_admin = config.is_admin(message.from_user.id)
    
    if is_admin:
        # Создаем клавиатуру с админ кнопкой
        keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔧 Админ панель")],
                [KeyboardButton(text="🔙 Обычное меню")]
            ],
            resize_keyboard=True
        )
        await message.answer("🔧 Тестовая админ клавиатура:", reply_markup=keyboard)
    else:
        await message.answer("❌ Вы не администратор")

@admin_router.message(F.text == "🔙 Обычное меню")
async def back_to_normal_menu(message: Message, config: BotConfig):
    """Возврат к обычному меню"""
    is_admin = config.is_admin(message.from_user.id)
    await message.answer(
        "🏠 Главное меню",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin)
    )