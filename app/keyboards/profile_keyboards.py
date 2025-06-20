"""
Клавиатуры для профиля пользователя (обновленная версия)
"""
from typing import List, Dict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..utils.constants import BUTTON_TEXTS, CALLBACK_DATA


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Основная клавиатура профиля"""
    keyboard = [
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['EDIT_PROFILE'], 
            callback_data=CALLBACK_DATA['EDIT_PROFILE']
        )],
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['ORDER_HISTORY'], 
            callback_data=CALLBACK_DATA['ORDER_HISTORY']
        )],
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['BACK_TO_MAIN'], 
            callback_data=CALLBACK_DATA['MAIN_MENU']
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_edit_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура редактирования профиля"""
    keyboard = [
        [InlineKeyboardButton(
            text="✏️ Изменить имя", 
            callback_data="edit_name"
        )],
        [InlineKeyboardButton(
            text="📞 Изменить телефон", 
            callback_data="edit_phone"
        )],
        [InlineKeyboardButton(
            text="📍 Изменить адрес", 
            callback_data="edit_address"
        )],
        [InlineKeyboardButton(
            text="🔙 Назад к профилю", 
            callback_data="back_to_profile"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_order_history_keyboard(orders: List[Dict] = None, page: int = 0, 
                              has_prev: bool = False, has_next: bool = False) -> InlineKeyboardMarkup:
    """
    Клавиатура истории заказов с пагинацией
    
    Args:
        orders: Список заказов пользователя
        page: Текущая страница (начиная с 0)
        has_prev: Есть ли предыдущая страница
        has_next: Есть ли следующая страница
    """
    keyboard = []
    
    if orders:
        # Показываем заказы как кнопки (максимум 5)
        for order in orders[:5]:
            order_id = order['id']
            date = order['order_date']
            status_emoji = "✅" if order['status'] == 'completed' else "⏳"
            
            button_text = f"{status_emoji} Заказ №{order_id} от {date}"
            keyboard.append([InlineKeyboardButton(
                text=button_text, 
                callback_data=f"order_details_{order_id}"
            )])
        
        # Кнопки навигации по страницам
        nav_buttons = []
        if has_prev:
            nav_buttons.append(InlineKeyboardButton(
                text="⬅️ Предыдущие", 
                callback_data=f"order_history_page_{page - 1}"
            ))
        
        if has_next:
            nav_buttons.append(InlineKeyboardButton(
                text="➡️ Следующие", 
                callback_data=f"order_history_page_{page + 1}"
            ))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Информация о странице (если есть навигация)
        if has_prev or has_next:
            keyboard.append([InlineKeyboardButton(
                text=f"📄 Страница {page + 1}", 
                callback_data="current_page"  # Нефункциональная кнопка
            )])
        
    else:
        # Если заказов нет
        keyboard.append([InlineKeyboardButton(
            text=BUTTON_TEXTS['MAKE_ORDER'], 
            callback_data=CALLBACK_DATA['MAKE_ORDER']
        )])
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        text="🔙 Назад к профилю", 
        callback_data="back_to_profile"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reviews_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отзывов"""
    keyboard = [
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['CREATE_REVIEW'], 
            callback_data=CALLBACK_DATA['CREATE_REVIEW']
        )],
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['BACK_TO_MAIN'], 
            callback_data=CALLBACK_DATA['MAIN_MENU']
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_review_creation_keyboard(orders: List[Dict]) -> InlineKeyboardMarkup:
    """
    Клавиатура для создания отзыва
    
    Args:
        orders: Список заказов для оценки
    """
    keyboard = []
    
    if orders:
        for order in orders:
            order_id = order['id']
            date = order['order_date']
            master_name = order['master_name']
            
            button_text = f"Заказ №{order_id} ({date}) - {master_name}"
            keyboard.append([InlineKeyboardButton(
                text=button_text, 
                callback_data=f"review_order_{order_id}"
            )])
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        text="🔙 К отзывам", 
        callback_data="back_to_reviews"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_rating_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора рейтинга"""
    keyboard = []
    
    # Кнопки рейтинга от 1 до 5
    for i in range(1, 6):
        stars = "⭐" * i
        keyboard.append([InlineKeyboardButton(
            text=f"{stars} {i}", 
            callback_data=f"rating_{i}"
        )])
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        text="🔙 К отзывам", 
        callback_data="back_to_reviews"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_support_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура поддержки"""
    keyboard = [
        [InlineKeyboardButton(
            text="📝 Написать в поддержку", 
            callback_data="write_support"
        )],
        [InlineKeyboardButton(
            text="❓ Часто задаваемые вопросы", 
            callback_data="faq"
        )],
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['BACK_TO_MAIN'], 
            callback_data=CALLBACK_DATA['MAIN_MENU']
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_faq_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура FAQ"""
    keyboard = [
        [InlineKeyboardButton(
            text="❓ Как сделать заказ?", 
            callback_data="faq_order"
        )],
        [InlineKeyboardButton(
            text="💰 Как происходит оплата?", 
            callback_data="faq_payment"
        )],
        [InlineKeyboardButton(
            text="⏰ Время выполнения работ?", 
            callback_data="faq_timing"
        )],
        [InlineKeyboardButton(
            text="🛡️ Есть ли гарантия?", 
            callback_data="faq_warranty"
        )],
        [InlineKeyboardButton(
            text="🤖 Как работает ИИ консультация?", 
            callback_data="faq_ai"
        )],
        [InlineKeyboardButton(
            text="🔙 Назад", 
            callback_data=CALLBACK_DATA['SUPPORT']
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_order_details_keyboard(order_id: int, order_status: str) -> InlineKeyboardMarkup:
    """
    Клавиатура деталей заказа с поддержкой завершения
    
    Args:
        order_id: ID заказа
        order_status: Статус заказа
    """
    keyboard = []
    
    # Действия в зависимости от статуса
    if order_status == 'pending':
        keyboard.append([InlineKeyboardButton(
            text="❌ Отменить заказ", 
            callback_data=f"cancel_order_{order_id}"
        )])
    elif order_status in ['confirmed', 'in_progress']:
        # Можно и отменить и завершить
        keyboard.append([
            InlineKeyboardButton(
                text="✅ Завершить заказ", 
                callback_data=f"complete_order_{order_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отменить заказ", 
                callback_data=f"cancel_order_{order_id}"
            )
        ])
    elif order_status == 'completed':
        keyboard.append([InlineKeyboardButton(
            text="✍️ Оставить отзыв", 
            callback_data=f"review_order_{order_id}"
        )])
        keyboard.append([InlineKeyboardButton(
            text="🔄 Повторить заказ", 
            callback_data=f"repeat_order_{order_id}"
        )])
    
    # Общие действия
    keyboard.extend([
        [InlineKeyboardButton(
            text="📱 Связаться с мастером", 
            callback_data=f"contact_master_{order_id}"
        )],
        [InlineKeyboardButton(
            text="🔙 К истории заказов", 
            callback_data="back_to_order_history"
        )]
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_complete_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения завершения заказа"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Да, завершить", 
                callback_data=f"confirm_complete_{order_id}"
            ),
            InlineKeyboardButton(
                text="❌ Нет, продолжить", 
                callback_data=f"order_details_{order_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cancel_order_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения отмены заказа"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Да, отменить", 
                callback_data=f"confirm_cancel_{order_id}"
            ),
            InlineKeyboardButton(
                text="❌ Нет, оставить", 
                callback_data=f"order_details_{order_id}"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_notification_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек уведомлений"""
    keyboard = [
        [InlineKeyboardButton(
            text="🔔 Уведомления о заказах", 
            callback_data="toggle_order_notifications"
        )],
        [InlineKeyboardButton(
            text="📢 Рекламные уведомления", 
            callback_data="toggle_promo_notifications"
        )],
        [InlineKeyboardButton(
            text="⭐ Напоминания об отзывах", 
            callback_data="toggle_review_notifications"
        )],
        [InlineKeyboardButton(
            text="🔙 Назад к профилю", 
            callback_data="back_to_profile"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_export_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура экспорта данных профиля"""
    keyboard = [
        [InlineKeyboardButton(
            text="📄 Экспорт истории заказов", 
            callback_data="export_orders"
        )],
        [InlineKeyboardButton(
            text="📊 Статистика использования", 
            callback_data="user_statistics"
        )],
        [InlineKeyboardButton(
            text="🗑️ Удалить аккаунт", 
            callback_data="delete_account"
        )],
        [InlineKeyboardButton(
            text="🔙 Назад к профилю", 
            callback_data="back_to_profile"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_delete_account_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления аккаунта"""
    keyboard = [
        [
            InlineKeyboardButton(
                text="⚠️ Да, удалить", 
                callback_data="confirm_delete_account"
            ),
            InlineKeyboardButton(
                text="❌ Отменить", 
                callback_data="back_to_profile"
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)