"""
Обработчики регистрации пользователей
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
async def cmd_start(message: Message, state: FSMContext, db_queries: DatabaseQueries):
    """Команда /start - приветствие и проверка регистрации"""
    try:
        user = await db_queries.get_user(message.from_user.id)
        
        if user:
            # Пользователь уже зарегистрирован
            await message.answer(
                f"Добро пожаловать обратно, {user['name']}! 👋\n\n"
                f"{SECTION_DESCRIPTIONS['MAIN_MENU']}",
                reply_markup=get_main_menu_keyboard(),
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
        # Валидация имени
        is_valid, error_msg, cleaned_data = ValidationService.validate_user_registration_data(
            name=message.text,
            phone="temp",  # Временные значения для валидации только имени
            address="temp"
        )
        
        if not is_valid and "имя" in error_msg.lower():
            await message.answer(error_msg)
            return
        
        # Сохраняем валидное имя
        await state.update_data(name=cleaned_data['name'])
        
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
        # Валидация телефона
        is_valid, error_msg, cleaned_data = ValidationService.validate_user_registration_data(
            name="temp",  # Временное значение
            phone=message.text,
            address="temp"
        )
        
        if not is_valid and "телефон" in error_msg.lower():
            await message.answer(error_msg)
            return
        
        # Сохраняем валидный телефон
        await state.update_data(phone=cleaned_data['phone'])
        
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
async def process_address(message: Message, state: FSMContext, db_queries: DatabaseQueries):
    """Обработка ввода адреса и завершение регистрации"""
    try:
        # Получаем сохраненные данные
        data = await state.get_data()
        
        # Валидация всех данных
        is_valid, error_msg, cleaned_data = ValidationService.validate_user_registration_data(
            name=data.get('name', ''),
            phone=data.get('phone', ''),
            address=message.text
        )
        
        if not is_valid:
            if "адрес" in error_msg.lower():
                await message.answer(error_msg)
                return
            else:
                # Ошибка в ранее введенных данных - начинаем заново
                await message.answer(
                    "Произошла ошибка с ранее введенными данными.\n"
                    "Давайте начнем регистрацию заново.\n\n"
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
        
        if success:
            await message.answer(
                f"{SUCCESS_MESSAGES['REGISTRATION_COMPLETE']}\n\n"
                f"✅ **Ваши данные:**\n"
                f"👤 Имя: {cleaned_data['name']}\n"
                f"📞 Телефон: {cleaned_data['phone']}\n"
                f"📍 Адрес: {cleaned_data['address']}\n\n"
                f"{SECTION_DESCRIPTIONS['MAIN_MENU']}",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            await state.clear()
            
            # Логируем успешную регистрацию
            logging.info(
                f"Новый пользователь зарегистрирован: "
                f"ID={message.from_user.id}, "
                f"name={cleaned_data['name']}, "
                f"username={message.from_user.username}"
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
async def cmd_register(message: Message, state: FSMContext, db_queries: DatabaseQueries):
    """Команда /register - принудительная перерегистрация"""
    try:
        user = await db_queries.get_user(message.from_user.id)
        
        if user:
            await message.answer(
                "Вы уже зарегистрированы в системе! 😊\n\n"
                f"👤 **Ваши данные:**\n"
                f"Имя: {user['name']}\n"
                f"Телефон: {user['phone']}\n"
                f"Адрес: {user['address']}\n\n"
                "Если хотите изменить данные, используйте раздел «Профиль».",
                reply_markup=get_main_menu_keyboard(),
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
async def cmd_profile_shortcut(message: Message, db_queries: DatabaseQueries):
    """Команда /profile - быстрый доступ к профилю"""
    try:
        user = await db_queries.get_user(message.from_user.id)
        
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
                reply_markup=get_main_menu_keyboard(),
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