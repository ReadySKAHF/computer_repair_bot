"""
Клавиатуры главного меню
"""
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from ..utils.constants import BUTTON_TEXTS, CALLBACK_DATA


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=BUTTON_TEXTS['MAKE_ORDER']), 
                KeyboardButton(text=BUTTON_TEXTS['SERVICE_DESCRIPTIONS'])
            ],
            [
                KeyboardButton(text=BUTTON_TEXTS['MASTERS']), 
                KeyboardButton(text=BUTTON_TEXTS['REVIEWS'])
            ],
            [
                KeyboardButton(text=BUTTON_TEXTS['AI_CONSULTATION']), 
                KeyboardButton(text=BUTTON_TEXTS['SUPPORT'])
            ],
            [
                KeyboardButton(text=BUTTON_TEXTS['PROFILE'])
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_welcome_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура приветствия для новых пользователей"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🚀 Начать использование", 
            callback_data=CALLBACK_DATA['MAIN_MENU']
        )]
    ])
    return keyboard


def get_main_menu_inline_keyboard() -> InlineKeyboardMarkup:
    """Inline-версия главного меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=BUTTON_TEXTS['MAKE_ORDER'], 
                callback_data=CALLBACK_DATA['MAKE_ORDER']
            ),
            InlineKeyboardButton(
                text=BUTTON_TEXTS['SERVICE_DESCRIPTIONS'], 
                callback_data=CALLBACK_DATA['VIEW_SERVICES']
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTON_TEXTS['MASTERS'], 
                callback_data=CALLBACK_DATA['VIEW_MASTERS']
            ),
            InlineKeyboardButton(
                text=BUTTON_TEXTS['REVIEWS'], 
                callback_data=CALLBACK_DATA['VIEW_REVIEWS']
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTON_TEXTS['AI_CONSULTATION'], 
                callback_data=CALLBACK_DATA['AI_CONSULTATION']
            ),
            InlineKeyboardButton(
                text=BUTTON_TEXTS['SUPPORT'], 
                callback_data=CALLBACK_DATA['SUPPORT']
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTON_TEXTS['PROFILE'], 
                callback_data=CALLBACK_DATA['PROFILE']
            )
        ]
    ])
    return keyboard


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой возврата в главное меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=BUTTON_TEXTS['BACK_TO_MAIN'], 
            callback_data=CALLBACK_DATA['MAIN_MENU']
        )]
    ])
    return keyboard


def get_help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура помощи"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📋 Как сделать заказ?", 
                callback_data="help_order"
            )
        ],
        [
            InlineKeyboardButton(
                text="🤖 Как работает ИИ консультация?", 
                callback_data="help_ai"
            )
        ],
        [
            InlineKeyboardButton(
                text="💰 Как оплачивать услуги?", 
                callback_data="help_payment"
            )
        ],
        [
            InlineKeyboardButton(
                text="📞 Связаться с поддержкой", 
                callback_data=CALLBACK_DATA['SUPPORT']
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTON_TEXTS['BACK_TO_MAIN'], 
                callback_data=CALLBACK_DATA['MAIN_MENU']
            )
        ]
    ])
    return keyboard


def get_error_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для обработки ошибок"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=BUTTON_TEXTS['TRY_AGAIN'], 
                callback_data="retry_action"
            ),
            InlineKeyboardButton(
                text=BUTTON_TEXTS['SUPPORT'], 
                callback_data=CALLBACK_DATA['SUPPORT']
            )
        ],
        [
            InlineKeyboardButton(
                text=BUTTON_TEXTS['BACK_TO_MAIN'], 
                callback_data=CALLBACK_DATA['MAIN_MENU']
            )
        ]
    ])
    return keyboard


def get_confirmation_keyboard(confirm_callback: str, cancel_callback: str = None) -> InlineKeyboardMarkup:
    """
    Клавиатура подтверждения действия
    
    Args:
        confirm_callback: Callback для подтверждения
        cancel_callback: Callback для отмены (по умолчанию - главное меню)
    """
    if cancel_callback is None:
        cancel_callback = CALLBACK_DATA['MAIN_MENU']
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=confirm_callback),
            InlineKeyboardButton(text="❌ Отменить", callback_data=cancel_callback)
        ]
    ])
    return keyboard


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Админ-панель (для будущего использования)"""
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
            InlineKeyboardButton(text="🔧 Настройки", callback_data="admin_settings"),
            InlineKeyboardButton(text="📥 Бэкап БД", callback_data="admin_backup")
        ],
        [
            InlineKeyboardButton(
                text=BUTTON_TEXTS['BACK_TO_MAIN'], 
                callback_data=CALLBACK_DATA['MAIN_MENU']
            )
        ]
    ])
    return keyboard


def get_loading_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура во время загрузки"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ Обработка...", callback_data="loading")]
    ])
    return keyboard