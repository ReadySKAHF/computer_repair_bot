"""
Обработчики профиля пользователя (обновленная версия)
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..database.queries import DatabaseQueries
from ..services.validation_service import ValidationService
from ..keyboards.main_menu import get_main_menu_keyboard
from ..keyboards.profile_keyboards import (
    get_profile_keyboard, get_profile_edit_keyboard, 
    get_order_history_keyboard, get_order_details_keyboard,
    get_complete_order_keyboard
)
from ..utils.constants import (
    SECTION_DESCRIPTIONS, SUCCESS_MESSAGES, ORDER_STATUS_EMOJI, ORDER_STATUSES
)


# Создаем роутер для профиля
profile_router = Router()


# Состояния редактирования профиля
class ProfileEditStates(StatesGroup):
    editing_name = State()
    editing_phone = State()
    editing_address = State()


async def delete_current_message(message):
    """Безопасное удаление сообщения"""
    try:
        await message.delete()
    except Exception:
        pass


# === ПРОСМОТР ПРОФИЛЯ ===

@profile_router.message(F.text == "👤 Профиль")
async def show_profile(message: Message, state: FSMContext, user):
    """Показ профиля пользователя"""
    if not user:
        await message.answer(
            "❌ Для просмотра профиля необходимо зарегистрироваться!\n"
            "Выполните команду /start"
        )
        return
    
    try:
        # Форматируем дату регистрации
        date_str = user['created_at'][:10] if user['created_at'] else "неизвестно"
        
        text = f"{SECTION_DESCRIPTIONS['PROFILE_INFO']}"
        text += f"**Имя:** {user['name']}\n"
        text += f"**Телефон:** {user['phone']}\n"
        text += f"**Адрес:** {user['address']}\n"
        text += f"**Дата регистрации:** {date_str}\n\n"
        text += "Используйте кнопки ниже для управления профилем."
        
        keyboard = get_profile_keyboard()
        sent_message = await message.answer(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        await state.update_data(current_message_id=sent_message.message_id)
    
    except Exception as e:
        logging.error(f"Ошибка в show_profile: {e}")
        await message.answer(
            "Произошла ошибка при загрузке профиля.\n"
            "Попробуйте еще раз."
        )


@profile_router.callback_query(F.data == "edit_profile")
async def edit_profile(callback: CallbackQuery):
    """Меню редактирования профиля"""
    keyboard = get_profile_edit_keyboard()
    
    await callback.message.edit_text(
        f"{SECTION_DESCRIPTIONS['PROFILE_EDITING']}",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    await callback.answer()


# === РЕДАКТИРОВАНИЕ ПРОФИЛЯ ===

@profile_router.callback_query(F.data.startswith("edit_"))
async def handle_profile_editing(callback: CallbackQuery, state: FSMContext):
    """Обработка начала редактирования поля профиля"""
    try:
        edit_type = callback.data.split("_")[1]
        
        if edit_type == "name":
            await callback.message.edit_text(
                "✏️ **Изменение имени**\n\n"
                "Введите новое имя:\n\n"
                "Требования:\n"
                "• От 2 до 50 символов\n"
                "• Только буквы, пробелы и дефисы",
                parse_mode='Markdown'
            )
            await state.set_state(ProfileEditStates.editing_name)
            
        elif edit_type == "phone":
            await callback.message.edit_text(
                "📞 **Изменение телефона**\n\n"
                "Введите новый номер телефона:\n\n"
                "Примеры правильного формата:\n"
                "• +7 900 123 45 67\n"
                "• 8 (900) 123-45-67\n"
                "• 79001234567",
                parse_mode='Markdown'
            )
            await state.set_state(ProfileEditStates.editing_phone)
            
        elif edit_type == "address":
            await callback.message.edit_text(
                "📍 **Изменение адреса**\n\n"
                "Введите новый адрес:\n\n"
                "Требования:\n"
                "• От 10 до 200 символов\n"
                "• Пример: ул. Пушкина, д. 10, кв. 15",
                parse_mode='Markdown'
            )
            await state.set_state(ProfileEditStates.editing_address)
        
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в handle_profile_editing: {e}")
        await callback.answer("Ошибка при начале редактирования")


@profile_router.message(ProfileEditStates.editing_name)
async def process_new_name(message: Message, state: FSMContext, db_queries: DatabaseQueries, is_admin: bool = False):
    """Обработка нового имени"""
    try:
        # Удаляем сообщение пользователя
        await delete_current_message(message)
        
        # Валидация нового имени
        is_valid, error_msg, cleaned_value = ValidationService.validate_profile_update_data('name', message.text)
        
        if not is_valid:
            await message.answer(error_msg)
            return
        
        # Обновляем в БД
        success = await db_queries.update_user_field(message.from_user.id, "name", cleaned_value)
        
        if success:
            await message.answer(
                f"✅ **Имя обновлено!**\n\n"
                f"Новое имя: **{cleaned_value}**\n\n"
                f"{SUCCESS_MESSAGES['PROFILE_UPDATED']}",
                reply_markup=get_main_menu_keyboard(is_admin=is_admin),
                parse_mode='Markdown'
            )
            logging.info(f"Пользователь {message.from_user.id} обновил имя на '{cleaned_value}'")
        else:
            await message.answer(
                "❌ Произошла ошибка при обновлении имени.\n"
                "Попробуйте еще раз или обратитесь в поддержку."
            )
        
        await state.clear()
    
    except Exception as e:
        logging.error(f"Ошибка в process_new_name: {e}")
        await message.answer(
            "Произошла ошибка при обновлении имени.\n"
            "Попробуйте еще раз."
        )
        await state.clear()


@profile_router.message(ProfileEditStates.editing_phone)
async def process_new_phone(message: Message, state: FSMContext, db_queries: DatabaseQueries, is_admin: bool = False):
    """Обработка нового телефона"""
    try:
        # Удаляем сообщение пользователя
        await delete_current_message(message)
        
        # Валидация нового телефона
        is_valid, error_msg, cleaned_value = ValidationService.validate_profile_update_data('phone', message.text)
        
        if not is_valid:
            await message.answer(error_msg)
            return
        
        # Обновляем в БД
        success = await db_queries.update_user_field(message.from_user.id, "phone", cleaned_value)
        
        if success:
            await message.answer(
                f"✅ **Телефон обновлен!**\n\n"
                f"Новый телефон: **{cleaned_value}**\n\n"
                f"{SUCCESS_MESSAGES['PROFILE_UPDATED']}",
                reply_markup=get_main_menu_keyboard(is_admin=is_admin),
                parse_mode='Markdown'
            )
            logging.info(f"Пользователь {message.from_user.id} обновил телефон")
        else:
            await message.answer(
                "❌ Произошла ошибка при обновлении телефона.\n"
                "Попробуйте еще раз или обратитесь в поддержку."
            )
        
        await state.clear()
    
    except Exception as e:
        logging.error(f"Ошибка в process_new_phone: {e}")
        await message.answer(
            "Произошла ошибка при обновлении телефона.\n"
            "Попробуйте еще раз."
        )
        await state.clear()


@profile_router.message(ProfileEditStates.editing_address)
async def process_new_address(message: Message, state: FSMContext, db_queries: DatabaseQueries, is_admin: bool = False):
    """Обработка нового адреса"""
    try:
        # Удаляем сообщение пользователя
        await delete_current_message(message)
        
        # Валидация нового адреса
        is_valid, error_msg, cleaned_value = ValidationService.validate_profile_update_data('address', message.text)
        
        if not is_valid:
            await message.answer(error_msg)
            return
        
        # Обновляем в БД
        success = await db_queries.update_user_field(message.from_user.id, "address", cleaned_value)
        
        if success:
            await message.answer(
                f"✅ **Адрес обновлен!**\n\n"
                f"Новый адрес: **{cleaned_value}**\n\n"
                f"{SUCCESS_MESSAGES['PROFILE_UPDATED']}",
                reply_markup=get_main_menu_keyboard(is_admin=is_admin),
                parse_mode='Markdown'
            )
            logging.info(f"Пользователь {message.from_user.id} обновил адрес")
        else:
            await message.answer(
                "❌ Произошла ошибка при обновлении адреса.\n"
                "Попробуйте еще раз или обратитесь в поддержку."
            )
        
        await state.clear()
    
    except Exception as e:
        logging.error(f"Ошибка в process_new_address: {e}")
        await message.answer(
            "Произошла ошибка при обновлении адреса.\n"
            "Попробуйте еще раз."
        )
        await state.clear()


# === ИСТОРИЯ ЗАКАЗОВ С ПАГИНАЦИЕЙ ===

@profile_router.callback_query(F.data == "order_history")
async def show_order_history(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Показ истории заказов (первая страница)"""
    await show_order_history_page(callback, state, db_queries, page=0)


@profile_router.callback_query(F.data.startswith("order_history_page_"))
async def show_order_history_page_handler(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Обработчик навигации по страницам истории заказов"""
    try:
        page = int(callback.data.split("_")[-1])
        await show_order_history_page(callback, state, db_queries, page=page)
    except (ValueError, IndexError) as e:
        logging.error(f"Ошибка в show_order_history_page_handler: {e}")
        await callback.answer("Ошибка навигации")


async def show_order_history_page(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries, page: int = 0):
    """Показ конкретной страницы истории заказов"""
    try:
        orders_per_page = 5
        offset = page * orders_per_page
        
        # Получаем заказы с запасом для определения наличия следующей страницы
        orders = await db_queries.get_user_orders(callback.from_user.id, orders_per_page + 1, offset)
        
        # Сохраняем текущую страницу в state
        await state.update_data(order_history_page=page)
        
        if not orders:
            if page == 0:
                # Нет заказов вообще
                text = f"{SECTION_DESCRIPTIONS['ORDER_HISTORY']}"
                text += "У вас пока нет заказов.\n"
                text += "Сделайте первый заказ прямо сейчас!"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🛠️ Сделать заказ", callback_data="make_order")],
                    [InlineKeyboardButton(text="🔙 Назад к профилю", callback_data="back_to_profile")]
                ])
            else:
                # Страница пустая, возвращаемся на предыдущую
                await show_order_history_page(callback, state, db_queries, page=max(0, page-1))
                return
        else:
            # Определяем есть ли следующая страница
            has_next_page = len(orders) > orders_per_page
            current_page_orders = orders[:orders_per_page]
            
            # Подсчитываем общее количество заказов для отображения
            all_orders = await db_queries.get_user_orders(callback.from_user.id, 1000)  # Получаем все для подсчета
            total_orders = len(all_orders) if all_orders else 0
            
            text = f"{SECTION_DESCRIPTIONS['ORDER_HISTORY']}"
            text += f"**Всего заказов:** {total_orders}\n"
            text += f"**Страница:** {page + 1}\n\n"
            
            # Показываем заказы текущей страницы
            for order in current_page_orders:
                order_id = order['id']
                date = order['order_date']
                time = order['order_time']
                cost = order['total_cost']
                status = order['status']
                master_name = order['master_name']
                services = order['services']
                
                status_emoji = ORDER_STATUS_EMOJI.get(status, "❓")
                status_text = ORDER_STATUSES.get(status, status)
                
                text += f"{status_emoji} **Заказ №{order_id}**\n"
                text += f"📅 {date} в {time}\n"
                text += f"👨‍🔧 Мастер: {master_name}\n"
                text += f"🛠️ Услуги: {services[:50]}{'...' if len(services) > 50 else ''}\n"
                text += f"💰 Стоимость: {cost}₽\n"
                text += f"📊 Статус: {status_text}\n\n"
            
            keyboard = get_order_history_keyboard(
                orders=current_page_orders, 
                page=page, 
                has_prev=(page > 0), 
                has_next=has_next_page
            )
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_order_history_page: {e}")
        await callback.answer("Ошибка при загрузке истории заказов")


@profile_router.callback_query(F.data.startswith("order_details_"))
async def show_order_details(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Показ деталей заказа"""
    try:
        order_id = int(callback.data.split("_")[2])
        order = await db_queries.get_order_by_id(order_id)
        
        if not order:
            await callback.answer("Заказ не найден")
            return
        
        # Проверяем, что заказ принадлежит пользователю
        if order['user_id'] != callback.from_user.id:
            await callback.answer("Доступ запрещен")
            return
        
        # Форматируем детали заказа
        status_emoji = ORDER_STATUS_EMOJI.get(order['status'], "❓")
        status_text = ORDER_STATUSES.get(order['status'], order['status'])
        
        text = f"📋 **Детали заказа №{order['id']}**\n\n"
        text += f"📅 **Дата и время:** {order['order_date']} в {order['order_time']}\n"
        text += f"📊 **Статус:** {status_emoji} {status_text}\n"
        text += f"👨‍🔧 **Мастер:** {order['master_name']}\n"
        text += f"📍 **Адрес:** {order['address']}\n"
        text += f"🛠️ **Услуги:** {order['services']}\n"
        text += f"💰 **Стоимость:** {order['total_cost']}₽\n"
        
        # Добавляем дополнительную информацию в зависимости от статуса
        if order['status'] == 'pending':
            text += f"\n⏳ **Заказ ожидает подтверждения.**\n"
            text += "Мастер свяжется с вами в ближайшее время."
        elif order['status'] == 'confirmed':
            text += f"\n✅ **Заказ подтвержден.**\n"
            text += "Мастер приедет в указанное время."
        elif order['status'] == 'in_progress':
            text += f"\n🔧 **Заказ выполняется.**\n"
            text += "Мастер уже работает над вашей проблемой."
        elif order['status'] == 'completed':
            text += f"\n✅ **Заказ выполнен.**\n"
            text += "Спасибо за обращение! Вы можете оставить отзыв."
        elif order['status'] == 'cancelled':
            text += f"\n❌ **Заказ отменен.**"
        
        keyboard = get_order_details_keyboard(order_id, order['status'])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except (ValueError, IndexError) as e:
        logging.error(f"Ошибка в show_order_details: {e}")
        await callback.answer("Ошибка обработки запроса")
    except Exception as e:
        logging.error(f"Критическая ошибка в show_order_details: {e}")
        await callback.answer("Произошла ошибка")


# === ЗАВЕРШЕНИЕ ЗАКАЗА ===

@profile_router.callback_query(F.data.startswith("complete_order_"))
async def complete_order_request(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Запрос на завершение заказа"""
    try:
        order_id = int(callback.data.split("_")[2])
        order = await db_queries.get_order_by_id(order_id)
        
        if not order or order['user_id'] != callback.from_user.id:
            await callback.answer("Заказ не найден")
            return
        
        if order['status'] not in ['confirmed', 'in_progress']:
            await callback.answer("Этот заказ нельзя завершить")
            return
        
        text = f"✅ **Завершение заказа №{order_id}**\n\n"
        text += "Работы по заказу выполнены?\n\n"
        text += f"**Дата:** {order['order_date']} в {order['order_time']}\n"
        text += f"**Мастер:** {order['master_name']}\n"
        text += f"**Стоимость:** {order['total_cost']}₽\n\n"
        text += "После завершения вы сможете оставить отзыв о работе мастера."
        
        keyboard = get_complete_order_keyboard(order_id)
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в complete_order_request: {e}")
        await callback.answer("Ошибка при запросе завершения")


@profile_router.callback_query(F.data.startswith("confirm_complete_"))
async def confirm_complete_order(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Подтверждение завершения заказа"""
    try:
        order_id = int(callback.data.split("_")[2])
        
        # Обновляем статус заказа
        success = await db_queries.update_order_status(order_id, 'completed')
        
        if success:
            await callback.message.edit_text(
                f"✅ **Заказ №{order_id} завершен**\n\n"
                "Спасибо за использование нашего сервиса!\n"
                "Теперь вы можете оставить отзыв о работе мастера.\n\n"
                "💡 **Совет:** Ваш отзыв поможет другим клиентам сделать правильный выбор!",
                parse_mode='Markdown'
            )
            logging.info(f"Пользователь {callback.from_user.id} завершил заказ {order_id}")
        else:
            await callback.message.edit_text(
                "❌ **Ошибка завершения заказа**\n\n"
                "Не удалось завершить заказ.\n"
                "Обратитесь в поддержку для решения вопроса.",
                parse_mode='Markdown'
            )
        
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в confirm_complete_order: {e}")
        await callback.answer("Ошибка при завершении заказа")


# === ОТМЕНА ЗАКАЗА ===

@profile_router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order_request(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Запрос на отмену заказа"""
    try:
        order_id = int(callback.data.split("_")[2])
        order = await db_queries.get_order_by_id(order_id)
        
        if not order or order['user_id'] != callback.from_user.id:
            await callback.answer("Заказ не найден")
            return
        
        if order['status'] not in ['pending', 'confirmed']:
            await callback.answer("Этот заказ нельзя отменить")
            return
        
        text = f"❌ **Отмена заказа №{order_id}**\n\n"
        text += "Вы уверены, что хотите отменить этот заказ?\n\n"
        text += f"**Дата:** {order['order_date']} в {order['order_time']}\n"
        text += f"**Мастер:** {order['master_name']}\n"
        text += f"**Стоимость:** {order['total_cost']}₽"
        
        from ..keyboards.profile_keyboards import get_cancel_order_keyboard
        keyboard = get_cancel_order_keyboard(order_id)
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в cancel_order_request: {e}")
        await callback.answer("Ошибка при запросе отмены")


@profile_router.callback_query(F.data.startswith("confirm_cancel_"))
async def confirm_cancel_order(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Подтверждение отмены заказа"""
    try:
        order_id = int(callback.data.split("_")[2])
        
        # Обновляем статус заказа
        success = await db_queries.update_order_status(order_id, 'cancelled')
        
        if success:
            await callback.message.edit_text(
                f"✅ **Заказ №{order_id} отменен**\n\n"
                "Заказ успешно отменен.\n"
                "Если у вас есть вопросы, обратитесь в поддержку.",
                parse_mode='Markdown'
            )
            logging.info(f"Пользователь {callback.from_user.id} отменил заказ {order_id}")
        else:
            await callback.message.edit_text(
                "❌ **Ошибка отмены заказа**\n\n"
                "Не удалось отменить заказ.\n"
                "Обратитесь в поддержку для решения вопроса.",
                parse_mode='Markdown'
            )
        
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в confirm_cancel_order: {e}")
        await callback.answer("Ошибка при отмене заказа")


# === НАВИГАЦИЯ ===

@profile_router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery, user):
    """Возврат к профилю"""
    if not user:
        await callback.answer("Пользователь не найден")
        return
    
    try:
        # Форматируем дату регистрации
        date_str = user['created_at'][:10] if user['created_at'] else "неизвестно"
        
        text = f"{SECTION_DESCRIPTIONS['PROFILE_INFO']}"
        text += f"**Имя:** {user['name']}\n"
        text += f"**Телефон:** {user['phone']}\n"
        text += f"**Адрес:** {user['address']}\n"
        text += f"**Дата регистрации:** {date_str}\n\n"
        text += "Используйте кнопки ниже для управления профилем."
        
        keyboard = get_profile_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в back_to_profile: {e}")
        await callback.answer("Ошибка при возврате к профилю")


@profile_router.callback_query(F.data == "back_to_order_history")
async def back_to_order_history(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Возврат к истории заказов"""
    try:
        # Получаем сохраненную страницу из state
        data = await state.get_data()
        page = data.get('order_history_page', 0)
        
        await show_order_history_page(callback, state, db_queries, page=page)
    
    except Exception as e:
        logging.error(f"Ошибка в back_to_order_history: {e}")
        # В случае ошибки показываем первую страницу
        await show_order_history_page(callback, state, db_queries, page=0)


# Команда для быстрого тестирования
@profile_router.message(F.text == "/admin_test_orders")
async def admin_test_orders(message: Message, db_queries: DatabaseQueries):
    """Админская команда для тестирования заказов"""
    admin_ids = [123456789, 987654321]  # Ваши админские ID
    
    if message.from_user.id not in admin_ids:
        await message.answer("❌ Доступ запрещен")
        return
    
    try:
        # Получаем последние заказы пользователя
        orders = await db_queries.get_user_orders(message.from_user.id, 5)
        
        if not orders:
            await message.answer("У вас нет заказов для тестирования")
            return
        
        text = "🔧 **Админ: Управление заказами**\n\n"
        
        for order in orders:
            order_id = order['id']
            status = order['status']
            date = order['order_date']
            
            text += f"**Заказ №{order_id}** ({date})\n"
            text += f"Статус: {status}\n\n"
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="📋 История заказов с админкой", 
                callback_data="admin_order_history"
            )],
            [InlineKeyboardButton(
                text="🔙 Главное меню", 
                callback_data="main_menu"
            )]
        ])
        
        await message.answer(text, reply_markup=keyboard, parse_mode='Markdown')
    
    except Exception as e:
        logging.error(f"Ошибка в admin_test_orders: {e}")
        await message.answer("Ошибка при загрузке админ панели")