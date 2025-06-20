"""
Клавиатуры для заказов
"""
from datetime import datetime, timedelta
from typing import List, Dict, Set
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..utils.constants import TIME_SLOTS, BUTTON_TEXTS, CALLBACK_DATA


def get_services_keyboard(services: List[Dict], page: int, total_pages: int, 
                         selected_services: Set[int], action_prefix: str = "order_service") -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора услуг
    
    Args:
        services: Список услуг
        page: Текущая страница
        total_pages: Общее количество страниц
        selected_services: Выбранные услуги
        action_prefix: Префикс для callback'ов
    """
    keyboard = []
    
    # Кнопки услуг
    for service in services:
        service_id = service['id']
        name = service['name']
        price = service['price']
        
        if action_prefix == "order_service":
            checkmark = "✅ " if service_id in selected_services else ""
            button_text = f"{checkmark}{name} - {price}₽"
        else:
            button_text = f"{name} - {price}₽"
        
        keyboard.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"{action_prefix}_{service_id}"
        )])
    
    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(
            text=BUTTON_TEXTS['PREV'], 
            callback_data=f"{action_prefix}_page_{page-1}"
        ))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(
            text=BUTTON_TEXTS['NEXT'], 
            callback_data=f"{action_prefix}_page_{page+1}"
        ))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    # Кнопки управления
    if action_prefix == "order_service":
        if selected_services:
            keyboard.append([InlineKeyboardButton(
                text=BUTTON_TEXTS['CONFIRM_ORDER'], 
                callback_data=CALLBACK_DATA['CONFIRM_ORDER']
            )])
        keyboard.append([InlineKeyboardButton(
            text=BUTTON_TEXTS['BACK_TO_MAIN'], 
            callback_data=CALLBACK_DATA['MAIN_MENU']
        )])
    elif action_prefix == "view_service":
        keyboard.append([InlineKeyboardButton(
            text=BUTTON_TEXTS['BACK_TO_MAIN'], 
            callback_data=CALLBACK_DATA['MAIN_MENU']
        )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_time_slots_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора времени"""
    keyboard = []
    
    # Разбиваем временные слоты по 3 в ряд
    for i in range(0, len(TIME_SLOTS), 3):
        row = []
        for j in range(i, min(i + 3, len(TIME_SLOTS))):
            row.append(InlineKeyboardButton(
                text=TIME_SLOTS[j], 
                callback_data=f"time_{TIME_SLOTS[j]}"
            ))
        keyboard.append(row)
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        text=BUTTON_TEXTS['BACK'], 
        callback_data="back_to_services"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_dates_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора даты"""
    keyboard = []
    today = datetime.now()
    
    # Следующие 14 дней
    for i in range(1, 15):
        date = today + timedelta(days=i)
        date_str = date.strftime("%d.%m")
        day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][date.weekday()]
        button_text = f"{day_name} {date_str}"
        
        # По 2 кнопки в ряд
        if i % 2 == 1:
            row = [InlineKeyboardButton(
                text=button_text, 
                callback_data=f"date_{date.strftime('%Y-%m-%d')}"
            )]
            
            # Добавляем вторую кнопку если есть
            if i + 1 <= 14:
                next_date = today + timedelta(days=i + 1)
                next_date_str = next_date.strftime("%d.%m")
                next_day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][next_date.weekday()]
                next_button_text = f"{next_day_name} {next_date_str}"
                row.append(InlineKeyboardButton(
                    text=next_button_text, 
                    callback_data=f"date_{next_date.strftime('%Y-%m-%d')}"
                ))
            
            keyboard.append(row)
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        text=BUTTON_TEXTS['BACK'], 
        callback_data="back_to_time"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_address_selection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора адреса"""
    keyboard = [
        [InlineKeyboardButton(
            text="🏠 Адрес из профиля", 
            callback_data="address_profile"
        )],
        [InlineKeyboardButton(
            text="📍 Другой адрес", 
            callback_data="address_custom"
        )],
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['BACK'], 
            callback_data="back_to_date"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа"""
    keyboard = [
        [InlineKeyboardButton(
            text="✅ Подтвердить заказ", 
            callback_data="final_confirm"
        )],
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['CANCEL'], 
            callback_data=CALLBACK_DATA['MAIN_MENU']
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_masters_keyboard(masters: List[Dict], page: int = 0, total_pages: int = 1) -> InlineKeyboardMarkup:
    """Клавиатура выбора мастера"""
    keyboard = []
    
    # Кнопки мастеров
    for master in masters:
        master_id = master['id']
        name = master['name']
        experience = master['experience_years']
        rating = master['rating']
        
        button_text = f"{name} (опыт: {experience} лет, рейтинг: {rating}⭐)"
        keyboard.append([InlineKeyboardButton(
            text=button_text, 
            callback_data=f"master_{master_id}"
        )])
    
    # Навигация (если нужна)
    if total_pages > 1:
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton(
                text=BUTTON_TEXTS['PREV'], 
                callback_data=f"masters_page_{page-1}"
            ))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton(
                text=BUTTON_TEXTS['NEXT'], 
                callback_data=f"masters_page_{page+1}"
            ))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        text=BUTTON_TEXTS['BACK_TO_MAIN'], 
        callback_data=CALLBACK_DATA['MAIN_MENU']
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_order_actions_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    """Клавиатура действий с заказом"""
    keyboard = []
    
    # Действия в зависимости от статуса
    if status == 'pending':
        keyboard.append([
            InlineKeyboardButton(
                text="❌ Отменить заказ", 
                callback_data=f"cancel_order_{order_id}"
            )
        ])
    elif status == 'completed':
        keyboard.append([
            InlineKeyboardButton(
                text="✍️ Оставить отзыв", 
                callback_data=f"review_order_{order_id}"
            )
        ])
    
    # Общие действия
    keyboard.extend([
        [InlineKeyboardButton(
            text="📋 Детали заказа", 
            callback_data=f"order_details_{order_id}"
        )],
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['BACK'], 
            callback_data=CALLBACK_DATA['ORDER_HISTORY']
        )]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ai_services_keyboard(has_services: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для ИИ консультации"""
    keyboard = []
    
    if has_services:
        keyboard.append([InlineKeyboardButton(
            text=BUTTON_TEXTS['ADD_TO_ORDER'], 
            callback_data=CALLBACK_DATA['ADD_AI_SERVICES']
        )])
    
    keyboard.extend([
        [InlineKeyboardButton(
            text="🔄 Другая консультация", 
            callback_data=CALLBACK_DATA['NEW_AI_CONSULTATION']
        )],
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['BACK_TO_MAIN'], 
            callback_data=CALLBACK_DATA['MAIN_MENU']
        )]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_service_detail_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра услуги"""
    keyboard = [
        [InlineKeyboardButton(
            text="🔙 К списку услуг", 
            callback_data="back_to_services_catalog"
        )],
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['BACK_TO_MAIN'], 
            callback_data=CALLBACK_DATA['MAIN_MENU']
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_master_detail_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для детального просмотра мастера"""
    keyboard = [
        [InlineKeyboardButton(
            text="🔙 К списку мастеров", 
            callback_data="back_to_masters_catalog"
        )],
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['BACK_TO_MAIN'], 
            callback_data=CALLBACK_DATA['MAIN_MENU']
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_order_navigation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура навигации по этапам заказа"""
    keyboard = [
        [
            InlineKeyboardButton(text="1️⃣ Услуги", callback_data="order_step_services"),
            InlineKeyboardButton(text="2️⃣ Время", callback_data="order_step_time")
        ],
        [
            InlineKeyboardButton(text="3️⃣ Дата", callback_data="order_step_date"),
            InlineKeyboardButton(text="4️⃣ Адрес", callback_data="order_step_address")
        ],
        [
            InlineKeyboardButton(
                text=BUTTON_TEXTS['CANCEL'], 
                callback_data=CALLBACK_DATA['MAIN_MENU']
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)