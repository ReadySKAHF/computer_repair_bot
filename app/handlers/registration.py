"""
Обработчики регистрации пользователей (исправленная версия)
"""
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..database.queries import DatabaseQueries
from ..services.validation_service import ValidationService
from ..keyboards.main_menu import get_main_menu_keyboard
from ..utils.constants import SUCCESS_MESSAGES, SECTION_DESCRIPTIONS


# Создаем роутер для регистрации
registration_router = Router()

# Состояния регистрации
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()


@registration_router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext, db_queries: DatabaseQueries, is_admin: bool = False, config=None):
    """Команда /start - приветствие и проверка регистрации"""
    try:
        user = await db_queries.get_user(message.from_user.id)
        
        # Определяем статус администратора
        is_user_admin = is_admin if is_admin else (config and config.is_admin(message.from_user.id))
        
        if user:
            # Пользователь уже зарегистрирован
            await message.answer(
                f"Добро пожаловать обратно, {user['name']}! 👋\n\n"
                f"{SECTION_DESCRIPTIONS['MAIN_MENU']}",
                reply_markup=get_main_menu_keyboard(is_admin=is_user_admin),
                parse_mode='Markdown'
            )
            await state.clear()
        else:
            # Новый пользователь
            await message.answer(
                "Добро пожаловать в сервис ремонта компьютеров! 🔧\n\n"
                "Для начала работы необходимо зарегистрироваться.\n\n"
                "Пожалуйста, введите ваше имя:",
                parse_mode='Markdown'
            )
            await state.set_state(RegistrationStates.waiting_for_name)
    
    except Exception as e:
        logging.error(f"Ошибка в cmd_start: {e}")
        await message.answer(
            "Произошла ошибка при обращении к базе данных.\n"
            "Попробуйте еще раз через несколько секунд."
        )


@registration_router.message(StateFilter(RegistrationStates.waiting_for_name))
async def process_name(message: Message, state: FSMContext):
    """Обработка ввода имени"""
    try:
        # Валидация только имени
        from ..services.validation_service import ValidationService
        from ..utils.validators import validate_name, sanitize_input
        
        # Очищаем и валидируем только имя
        clean_name = sanitize_input(message.text)
        is_valid, error_msg = validate_name(clean_name)
        
        if not is_valid:
            await message.answer(f"❌ {error_msg}")
            return
        
        # Сохраняем валидное имя
        await state.update_data(name=clean_name.strip())
        
        await message.answer(
            "Отлично! ✅\n\n"
            "Теперь введите ваш номер телефона:\n\n"
            "Примеры правильного формата:\n"
            "• +7 900 123 45 67\n"
            "• 8 (900) 123-45-67\n"
            "• 79001234567",
            parse_mode='Markdown'
        )
        await state.set_state(RegistrationStates.waiting_for_phone)
    
    except Exception as e:
        logging.error(f"Ошибка в process_name: {e}")
        await message.answer(
            "Произошла ошибка при обработке имени.\n"
            "Попробуйте еще раз."
        )


@registration_router.message(StateFilter(RegistrationStates.waiting_for_phone))
async def process_phone(message: Message, state: FSMContext):
    """Обработка ввода телефона"""
    try:
        # Валидация только телефона
        from ..utils.validators import validate_phone, sanitize_input, format_phone_number
        
        # Очищаем и валидируем только телефон
        clean_phone = sanitize_input(message.text)
        is_valid, error_msg = validate_phone(clean_phone)
        
        if not is_valid:
            await message.answer(f"❌ {error_msg}")
            return
        
        # Сохраняем валидный телефон в отформатированном виде
        formatted_phone = format_phone_number(clean_phone)
        await state.update_data(phone=formatted_phone)
        
        await message.answer(
            "Отлично! ✅\n\n"
            "Теперь введите ваш адрес для выезда мастера:\n\n"
            "Пример: ул. Пушкина, д. 10, кв. 15\n"
            "Адрес должен содержать от 10 до 200 символов.",
            parse_mode='Markdown'
        )
        await state.set_state(RegistrationStates.waiting_for_address)
    
    except Exception as e:
        logging.error(f"Ошибка в process_phone: {e}")
        await message.answer(
            "Произошла ошибка при обработке телефона.\n"
            "Попробуйте еще раз."
        )


@registration_router.message(StateFilter(RegistrationStates.waiting_for_address))
async def process_address(message: Message, state: FSMContext, db_queries: DatabaseQueries, config=None):
    """Обработка ввода адреса и завершение регистрации"""
    try:
        # Валидация только адреса
        from ..utils.validators import validate_address, sanitize_input
        
        # Очищаем и валидируем только адрес
        clean_address = sanitize_input(message.text)
        is_valid, error_msg = validate_address(clean_address)
        
        if not is_valid:
            await message.answer(f"❌ {error_msg}")
            return
        
        # Получаем все сохраненные данные
        data = await state.get_data()
        name = data.get('name', '')
        phone = data.get('phone', '')
        
        # Проверяем, что все данные есть
        if not name or not phone:
            await message.answer(
                "❌ Произошла ошибка с ранее введенными данными.\n"
                "Давайте начнем регистрацию заново.\n\n"
                "Введите ваше имя:"
            )
            await state.set_state(RegistrationStates.waiting_for_name)
            return
        
        # Финальная валидация всех данных
        is_valid, error_msg, cleaned_data = ValidationService.validate_user_registration_data(
            name=name,
            phone=phone,
            address=clean_address.strip()
        )
        
        if not is_valid:
            await message.answer(
                f"❌ {error_msg}\n\n"
                "Давайте начнем регистрацию заново.\n"
                "Введите ваше имя:"
            )
            await state.set_state(RegistrationStates.waiting_for_name)
            return
        
        # Создаем пользователя в БД
        success = await db_queries.create_user(
            user_id=message.from_user.id,
            name=cleaned_data['name'],
            phone=cleaned_data['phone'],
            address=cleaned_data['address']
        )
        
        # Определяем статус администратора
        is_user_admin = config and config.is_admin(message.from_user.id)
        
        if success:
            await message.answer(
                f"{SUCCESS_MESSAGES['REGISTRATION_COMPLETE']}\n\n"
                f"✅ **Ваши данные:**\n"
                f"👤 Имя: {cleaned_data['name']}\n"
                f"📞 Телефон: {cleaned_data['phone']}\n"
                f"📍 Адрес: {cleaned_data['address']}\n\n"
                f"{SECTION_DESCRIPTIONS['MAIN_MENU']}",
                reply_markup=get_main_menu_keyboard(is_admin=is_user_admin),
                parse_mode='Markdown'
            )
            await state.clear()
            
            # Логируем успешную регистрацию
            logging.info(
                f"Новый пользователь зарегистрирован: "
                f"ID={message.from_user.id}, "
                f"name={cleaned_data['name']}, "
                f"username={message.from_user.username}, "
                f"is_admin={is_user_admin}"
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при сохранении данных.\n"
                "Попробуйте зарегистрироваться еще раз через команду /start"
            )
            await state.clear()
    
    except Exception as e:
        logging.error(f"Ошибка в process_address: {e}")
        await message.answer(
            "Произошла критическая ошибка при регистрации.\n"
            "Попробуйте еще раз через команду /start"
        )
        await state.clear()


@registration_router.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext, db_queries: DatabaseQueries, config=None):
    """Команда /register - принудительная перерегистрация"""
    try:
        user = await db_queries.get_user(message.from_user.id)
        is_user_admin = config and config.is_admin(message.from_user.id)
        
        if user:
            await message.answer(
                "Вы уже зарегистрированы в системе! 😊\n\n"
                f"👤 **Ваши данные:**\n"
                f"Имя: {user['name']}\n"
                f"Телефон: {user['phone']}\n"
                f"Адрес: {user['address']}\n\n"
                "Если хотите изменить данные, используйте раздел «Профиль».",
                reply_markup=get_main_menu_keyboard(is_admin=is_user_admin),
                parse_mode='Markdown'
            )
        else:
            await message.answer(
                "Начинаем регистрацию! 📝\n\n"
                "Введите ваше имя:"
            )
            await state.set_state(RegistrationStates.waiting_for_name)
    
    except Exception as e:
        logging.error(f"Ошибка в cmd_register: {e}")
        await message.answer(
            "Произошла ошибка при проверке регистрации.\n"
            "Попробуйте еще раз."
        )


@registration_router.message(Command("profile"))
async def cmd_profile_shortcut(message: Message, db_queries: DatabaseQueries, config=None):
    """Команда /profile - быстрый доступ к профилю"""
    try:
        user = await db_queries.get_user(message.from_user.id)
        is_user_admin = config and config.is_admin(message.from_user.id)
        
        if user:
            # Форматируем дату
            date_str = user['created_at'][:10] if user['created_at'] else "неизвестно"
            
            await message.answer(
                f"👤 **Ваш профиль**\n\n"
                f"**Имя:** {user['name']}\n"
                f"**Телефон:** {user['phone']}\n"
                f"**Адрес:** {user['address']}\n"
                f"**Дата регистрации:** {date_str}\n\n"
                "Для редактирования используйте кнопки ниже.",
                reply_markup=get_main_menu_keyboard(is_admin=is_user_admin),
                parse_mode='Markdown'
            )
        else:
            await message.answer(
                "❌ Вы не зарегистрированы в системе!\n\n"
                "Для начала работы выполните команду /start"
            )
    
    except Exception as e:
        logging.error(f"Ошибка в cmd_profile_shortcut: {e}")
        await message.answer(
            "Произошла ошибка при получении профиля.\n"
            "Попробуйте еще раз."
        )


# Middleware для проверки регистрации
class RegistrationMiddleware:
    """Middleware для проверки регистрации пользователя"""
    
    def __init__(self, db_queries: DatabaseQueries):
        self.db_queries = db_queries
    
    async def __call__(self, handler, event, data):
        """Проверяем регистрацию перед выполнением обработчика"""
        if hasattr(event, 'from_user') and event.from_user:
            user = await self.db_queries.get_user(event.from_user.id)
            data['user'] = user
            data['is_registered'] = user is not None
        
        return await handler(event, data)