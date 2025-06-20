"""
Обработчики заказов (исправленная версия)
"""
import logging
import random
from datetime import datetime
from typing import Set
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..database.queries import DatabaseQueries
from ..services.validation_service import ValidationService
from ..keyboards.main_menu import get_main_menu_keyboard
from ..keyboards.order_keyboards import (
    get_services_keyboard, get_time_slots_keyboard, get_dates_keyboard,
    get_address_selection_keyboard, get_order_confirmation_keyboard
)
from ..utils.constants import (
    SECTION_DESCRIPTIONS, SUCCESS_MESSAGES, ERROR_MESSAGES, LIMITS
)


# Создаем роутер для заказов
orders_router = Router()


# Состояния заказа
class OrderStates(StatesGroup):
    selecting_services = State()
    selecting_time = State()
    selecting_date = State()
    selecting_address = State()
    entering_custom_address = State()


async def delete_current_message(message):
    """Безопасное удаление сообщения"""
    try:
        await message.delete()
    except Exception:
        pass


# === СОЗДАНИЕ ЗАКАЗА ===

@orders_router.message(F.text == "🛠️ Сделать заказ")
async def start_order_creation(message: Message, state: FSMContext, db_queries: DatabaseQueries, user):
    """Начало создания заказа"""
    if not user:
        await message.answer(
            "❌ Для создания заказа необходимо зарегистрироваться!\n"
            "Выполните команду /start"
        )
        return
    
    try:
        # Получаем услуги
        services = await db_queries.get_services(0, LIMITS['MAX_SERVICES_PER_PAGE'])
        total_services = await db_queries.get_services_count()
        total_pages = (total_services + LIMITS['MAX_SERVICES_PER_PAGE'] - 1) // LIMITS['MAX_SERVICES_PER_PAGE']
        
        if not services:
            await message.answer(
                "❌ К сожалению, услуги временно недоступны.\n"
                "Попробуйте позже или обратитесь в поддержку."
            )
            return
        
        # Инициализируем состояние заказа
        await state.update_data(
            selected_services=set(),
            page=0,
            total_pages=total_pages
        )
        
        keyboard = get_services_keyboard(services, 0, total_pages, set(), "order_service")
        sent_message = await message.answer(
            f"{SECTION_DESCRIPTIONS['ORDER_CREATION']}\n\n"
            f"**Страница 1 из {total_pages}**",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        await state.update_data(current_message_id=sent_message.message_id)
        await state.set_state(OrderStates.selecting_services)
    
    except Exception as e:
        logging.error(f"Ошибка в start_order_creation: {e}")
        await message.answer(ERROR_MESSAGES['DATABASE_ERROR'])


@orders_router.callback_query(F.data.startswith("order_service_"))
async def handle_service_selection(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Обработка выбора услуг"""
    try:
        callback_parts = callback.data.split("_")
        
        if len(callback_parts) >= 4 and callback_parts[2] == "page":
            # Навигация по страницам
            page = int(callback_parts[3])
            await handle_services_pagination(callback, state, db_queries, page)
        else:
            # Выбор/отмена услуги
            service_id = int(callback_parts[2])
            await toggle_service_selection(callback, state, db_queries, service_id)
    
    except (ValueError, IndexError) as e:
        logging.error(f"Ошибка в handle_service_selection: {e}")
        await callback.answer("Ошибка обработки запроса")
    except Exception as e:
        logging.error(f"Критическая ошибка в handle_service_selection: {e}")
        await callback.answer("Произошла ошибка")


async def handle_services_pagination(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries, page: int):
    """Обработка пагинации услуг"""
    try:
        data = await state.get_data()
        selected_services = data.get('selected_services', set())
        
        await state.update_data(page=page)
        
        services = await db_queries.get_services(page, LIMITS['MAX_SERVICES_PER_PAGE'])
        total_services = await db_queries.get_services_count()
        total_pages = (total_services + LIMITS['MAX_SERVICES_PER_PAGE'] - 1) // LIMITS['MAX_SERVICES_PER_PAGE']
        
        keyboard = get_services_keyboard(services, page, total_pages, selected_services, "order_service")
        
        text = f"{SECTION_DESCRIPTIONS['ORDER_CREATION']}\n\n"
        text += f"**Страница {page + 1} из {total_pages}**\n\n"
        if selected_services:
            text += f"**Выбрано услуг:** {len(selected_services)}"
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в handle_services_pagination: {e}")
        await callback.answer("Ошибка при переходе между страницами")


async def toggle_service_selection(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries, service_id: int):
    """Переключение выбора услуги"""
    try:
        data = await state.get_data()
        selected_services = data.get('selected_services', set())
        page = data.get('page', 0)
        
        # Проверяем лимит услуг
        if service_id not in selected_services and len(selected_services) >= LIMITS['MAX_SERVICES_PER_ORDER']:
            await callback.answer(f"Максимальное количество услуг: {LIMITS['MAX_SERVICES_PER_ORDER']}")
            return
        
        # Переключаем выбор
        if service_id in selected_services:
            selected_services.remove(service_id)
        else:
            selected_services.add(service_id)
        
        await state.update_data(selected_services=selected_services)
        
        # Обновляем клавиатуру
        services = await db_queries.get_services(page, LIMITS['MAX_SERVICES_PER_PAGE'])
        total_services = await db_queries.get_services_count()
        total_pages = (total_services + LIMITS['MAX_SERVICES_PER_PAGE'] - 1) // LIMITS['MAX_SERVICES_PER_PAGE']
        
        keyboard = get_services_keyboard(services, page, total_pages, selected_services, "order_service")
        
        text = f"{SECTION_DESCRIPTIONS['ORDER_CREATION']}\n\n"
        text += f"**Страница {page + 1} из {total_pages}**\n\n"
        if selected_services:
            text += f"**Выбрано услуг:** {len(selected_services)}"
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в toggle_service_selection: {e}")
        await callback.answer("Ошибка при выборе услуги")


@orders_router.callback_query(F.data == "confirm_order")
async def confirm_services_selection(callback: CallbackQuery, state: FSMContext):
    """Подтверждение выбора услуг и переход к времени"""
    try:
        data = await state.get_data()
        selected_services = data.get('selected_services', set())
        
        if not selected_services:
            await callback.answer("Выберите хотя бы одну услугу!")
            return
        
        await state.set_state(OrderStates.selecting_time)
        
        keyboard = get_time_slots_keyboard()
        await callback.message.edit_text(
            f"{SECTION_DESCRIPTIONS['TIME_SELECTION']}",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в confirm_services_selection: {e}")
        await callback.answer("Ошибка при подтверждении услуг")


@orders_router.callback_query(F.data.startswith("time_"))
async def handle_time_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени"""
    try:
        time = callback.data.split("_")[1]
        await state.update_data(order_time=time)
        await state.set_state(OrderStates.selecting_date)
        
        keyboard = get_dates_keyboard()
        await callback.message.edit_text(
            f"{SECTION_DESCRIPTIONS['DATE_SELECTION']}\n\n"
            f"Выбранное время: **{time}**\n"
            "Теперь выберите дату:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в handle_time_selection: {e}")
        await callback.answer("Ошибка при выборе времени")


@orders_router.callback_query(F.data.startswith("date_"))
async def handle_date_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора даты"""
    try:
        date = callback.data.split("_")[1]
        
        # Валидация даты
        data = await state.get_data()
        time = data.get('order_time')
        
        is_valid, error_msg, datetime_data = ValidationService.validate_date_time(date, time)
        if not is_valid:
            await callback.answer(error_msg)
            return
        
        await state.update_data(order_date=date)
        await state.set_state(OrderStates.selecting_address)
        
        # Форматируем дату для отображения
        formatted_date = datetime_data['date_obj'].strftime('%d.%m.%Y')
        
        keyboard = get_address_selection_keyboard()
        await callback.message.edit_text(
            f"{SECTION_DESCRIPTIONS['ADDRESS_SELECTION']}\n\n"
            f"**Время:** {time}\n"
            f"**Дата:** {formatted_date}\n\n"
            "Выберите адрес для выезда мастера:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в handle_date_selection: {e}")
        await callback.answer("Ошибка при выборе даты")


@orders_router.callback_query(F.data == "address_profile")
async def use_profile_address(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries, user):
    """Использование адреса из профиля"""
    try:
        if not user:
            await callback.answer("Ошибка: пользователь не найден")
            return
        
        await state.update_data(order_address=user['address'])
        
        # Назначаем мастера здесь, когда все данные заказа готовы
        await assign_master_to_order(state, db_queries)
        
        await show_order_summary(callback, state, db_queries)
    
    except Exception as e:
        logging.error(f"Ошибка в use_profile_address: {e}")
        await callback.answer("Ошибка при использовании адреса")


@orders_router.callback_query(F.data == "address_custom")
async def use_custom_address(callback: CallbackQuery, state: FSMContext):
    """Ввод пользовательского адреса"""
    await state.set_state(OrderStates.entering_custom_address)
    await callback.message.edit_text(
        "📍 **Ввод адреса**\n\n"
        "Введите адрес для выезда мастера:\n\n"
        "Пример: ул. Пушкина, д. 10, кв. 15",
        parse_mode='Markdown'
    )
    await callback.answer()


@orders_router.message(OrderStates.entering_custom_address)
async def process_custom_address(message: Message, state: FSMContext, db_queries: DatabaseQueries):
    """Обработка пользовательского адреса"""
    try:
        # Удаляем сообщение пользователя
        await delete_current_message(message)
        
        # Валидация адреса
        is_valid, error_msg, cleaned_address = ValidationService.validate_profile_update_data('address', message.text)
        if not is_valid:
            await message.answer(error_msg)
            return
        
        await state.update_data(order_address=cleaned_address)
        
        # Назначаем мастера здесь, когда все данные заказа готовы
        await assign_master_to_order(state, db_queries)
        
        await show_order_summary_after_address(message, state, db_queries)
    
    except Exception as e:
        logging.error(f"Ошибка в process_custom_address: {e}")
        await message.answer("Ошибка при обработке адреса")


async def assign_master_to_order(state: FSMContext, db_queries: DatabaseQueries):
    """Назначение мастера для заказа"""
    try:
        data = await state.get_data()
        
        # Если мастер уже назначен, не меняем
        if data.get('assigned_master_id'):
            return
        
        # Получаем всех мастеров и выбираем случайного
        masters = await db_queries.get_masters()
        if masters:
            master = random.choice(masters)
            
            # Вычисляем общую стоимость
            selected_services = data.get('selected_services', set())
            total_cost = 0
            for service_id in selected_services:
                service = await db_queries.get_service_by_id(service_id)
                if service:
                    total_cost += service['price']
            
            # Сохраняем назначенного мастера и стоимость
            await state.update_data(
                assigned_master_id=master['id'],
                assigned_master_name=master['name'],
                total_cost=total_cost
            )
            
            logging.info(f"Назначен мастер {master['name']} (ID: {master['id']}) для заказа")
    
    except Exception as e:
        logging.error(f"Ошибка в assign_master_to_order: {e}")


async def show_order_summary(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Показ итогового резюме заказа (из callback)"""
    try:
        summary_text, keyboard = await build_order_summary(state, db_queries)
        
        await callback.message.edit_text(summary_text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_order_summary: {e}")
        await callback.answer("Ошибка при формировании резюме заказа")


async def show_order_summary_after_address(message: Message, state: FSMContext, db_queries: DatabaseQueries):
    """Показ итогового резюме заказа (после ввода адреса)"""
    try:
        summary_text, keyboard = await build_order_summary(state, db_queries)
        
        await message.answer(summary_text, reply_markup=keyboard, parse_mode='Markdown')
    
    except Exception as e:
        logging.error(f"Ошибка в show_order_summary_after_address: {e}")
        await message.answer("Ошибка при формировании резюме заказа")


async def build_order_summary(state: FSMContext, db_queries: DatabaseQueries) -> tuple:
    """Построение резюме заказа с уже назначенным мастером"""
    data = await state.get_data()
    selected_services = data.get('selected_services', set())
    order_time = data.get('order_time')
    order_date = data.get('order_date')
    order_address = data.get('order_address')
    assigned_master_id = data.get('assigned_master_id')
    assigned_master_name = data.get('assigned_master_name')
    total_cost = data.get('total_cost', 0)
    
    if not selected_services:
        raise ValueError("Не выбраны услуги для заказа")
    
    if not assigned_master_id:
        raise ValueError("Мастер не назначен")
    
    # Получаем информацию об услугах
    services_info = []
    calculated_total_cost = 0
    total_duration = 0
    
    for service_id in selected_services:
        service = await db_queries.get_service_by_id(service_id)
        if service:
            services_info.append({
                'name': service['name'],
                'price': service['price'],
                'duration': service['duration_minutes']
            })
            calculated_total_cost += service['price']
            total_duration += service['duration_minutes']
    
    if not services_info:
        raise ValueError("Выбранные услуги не найдены в базе данных")
    
    # Используем сохраненную стоимость, но если её нет - вычисляем
    if total_cost == 0:
        total_cost = calculated_total_cost
    
    # Форматируем дату
    formatted_date = datetime.strptime(order_date, '%Y-%m-%d').strftime('%d.%m.%Y')
    
    # Формируем текст заказа
    text = f"{SECTION_DESCRIPTIONS['ORDER_CONFIRMATION']}"
    text += "🛠️ **Услуги:**\n"
    for service in services_info:
        text += f"• {service['name']} - {service['price']}₽\n"
    
    text += f"\n📅 **Дата:** {formatted_date}"
    text += f"\n🕐 **Время:** {order_time}"
    text += f"\n📍 **Адрес:** {order_address}"
    text += f"\n👨‍🔧 **Мастер:** {assigned_master_name}"
    text += f"\n⏱️ **Примерное время работы:** {total_duration} мин"
    text += f"\n💰 **Общая стоимость:** {total_cost}₽"
    
    keyboard = get_order_confirmation_keyboard()
    
    return text, keyboard


@orders_router.callback_query(F.data == "final_confirm")
async def final_confirm_order(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Финальное подтверждение и создание заказа"""
    try:
        data = await state.get_data()
        
        # Используем уже назначенного мастера из state
        assigned_master_id = data.get('assigned_master_id')
        assigned_master_name = data.get('assigned_master_name')
        total_cost = data.get('total_cost', 0)
        
        if not assigned_master_id or not assigned_master_name:
            await callback.answer("Ошибка: мастер не назначен")
            return
        
        # Валидация данных заказа
        selected_services = data.get('selected_services', set())
        is_valid, error_msg, validated_data = ValidationService.validate_order_data(
            user_id=callback.from_user.id,
            master_id=assigned_master_id,
            address=data.get('order_address'),
            date_str=data.get('order_date'),
            time_str=data.get('order_time'),
            service_ids=list(selected_services)
        )
        
        if not is_valid:
            await callback.answer(error_msg)
            return
        
        # Создаем заказ в БД
        order_id = await db_queries.create_order(
            user_id=validated_data['user_id'],
            master_id=validated_data['master_id'],
            address=validated_data['address'],
            order_date=validated_data['order_date'],
            order_time=validated_data['order_time'],
            total_cost=total_cost,
            service_ids=validated_data['service_ids']
        )
        
        if order_id:
            await callback.message.edit_text(
                f"🎉 **Заказ успешно создан!**\n\n"
                f"**Номер заказа:** №{order_id}\n\n"
                f"Мастер **{assigned_master_name}** свяжется с вами в указанное время.\n"
                f"Спасибо за обращение!\n\n"
                "Вы можете отслеживать статус заказа в разделе «История заказов».",
                parse_mode='Markdown'
            )
            
            logging.info(f"Создан заказ {order_id} для пользователя {callback.from_user.id} с мастером {assigned_master_name} (ID: {assigned_master_id})")
        else:
            await callback.message.edit_text(
                "❌ Произошла ошибка при создании заказа.\n"
                "Попробуйте еще раз или обратитесь в поддержку."
            )
        
        await state.clear()
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в final_confirm_order: {e}")
        await callback.answer("Ошибка при создании заказа")


# Обработчик для услуг ИИ (если есть)
@orders_router.callback_query(F.data == "add_ai_services")
async def add_ai_recommended_services(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Добавление рекомендованных ИИ услуг в заказ"""
    try:
        data = await state.get_data()
        recommended_services = data.get('recommended_services', [])
        
        # Подробное логирование для отладки
        logging.info(f"=== ОТЛАДКА add_ai_services ===")
        logging.info(f"Все данные state: {data}")
        logging.info(f"recommended_services из state: {recommended_services}")
        logging.info(f"Тип recommended_services: {type(recommended_services)}")
        
        if not recommended_services:
            logging.error("❌ recommended_services пустой или None")
            await callback.answer("Ошибка: нет рекомендованных услуг")
            return
        
        # Сохраняем выбранные услуги как set для совместимости с остальной логикой заказов
        await state.update_data(selected_services=set(recommended_services))
        
        # Назначаем мастера сразу для ИИ услуг
        await assign_master_to_order(state, db_queries)
        
        # Переходим к выбору времени
        from ..handlers.orders import OrderStates
        await state.set_state(OrderStates.selecting_time)
        
        keyboard = get_time_slots_keyboard()
        await callback.message.edit_text(
            f"🕐 **Выбор времени**\n\n"
            f"**Выбранные услуги от ИИ:**\n"
            f"Количество услуг: {len(recommended_services)}\n\n"
            f"Выберите удобное время для визита мастера:",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        logging.info(f"✅ Успешно добавлены услуги ИИ в заказ: {recommended_services}")
        await callback.answer("✅ Услуги добавлены в заказ!")
    
    except Exception as e:
        logging.error(f"Ошибка в add_ai_recommended_services: {e}")
        await callback.answer("Ошибка при добавлении услуг в заказ")


# === НАВИГАЦИЯ ===

@orders_router.callback_query(F.data == "back_to_services")
async def back_to_services(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Возврат к выбору услуг"""
    try:
        data = await state.get_data()
        selected_services = data.get('selected_services', set())
        page = data.get('page', 0)
        
        services = await db_queries.get_services(page, LIMITS['MAX_SERVICES_PER_PAGE'])
        total_services = await db_queries.get_services_count()
        total_pages = (total_services + LIMITS['MAX_SERVICES_PER_PAGE'] - 1) // LIMITS['MAX_SERVICES_PER_PAGE']
        
        keyboard = get_services_keyboard(services, page, total_pages, selected_services, "order_service")
        
        text = f"{SECTION_DESCRIPTIONS['ORDER_CREATION']}\n\n"
        text += f"**Страница {page + 1} из {total_pages}**\n\n"
        if selected_services:
            text += f"**Выбрано услуг:** {len(selected_services)}"
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await state.set_state(OrderStates.selecting_services)
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в back_to_services: {e}")
        await callback.answer("Ошибка при возврате к услугам")


@orders_router.callback_query(F.data == "back_to_time")
async def back_to_time(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору времени"""
    keyboard = get_time_slots_keyboard()
    await callback.message.edit_text(
        f"{SECTION_DESCRIPTIONS['TIME_SELECTION']}",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    await state.set_state(OrderStates.selecting_time)
    await callback.answer()


@orders_router.callback_query(F.data == "back_to_date")
async def back_to_date(callback: CallbackQuery, state: FSMContext):
    """Возврат к выбору даты"""
    data = await state.get_data()
    time = data.get('order_time')
    
    keyboard = get_dates_keyboard()
    await callback.message.edit_text(
        f"{SECTION_DESCRIPTIONS['DATE_SELECTION']}\n\n"
        f"Выбранное время: **{time}**\n"
        "Теперь выберите дату:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    await state.set_state(OrderStates.selecting_date)
    await callback.answer()