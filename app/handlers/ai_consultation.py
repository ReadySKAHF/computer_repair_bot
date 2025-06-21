"""
Обработчики ИИ консультации
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..database.queries import DatabaseQueries
from ..services.ai_service import AIConsultationService
from ..services.validation_service import ValidationService
from ..keyboards.main_menu import get_main_menu_keyboard
from ..keyboards.order_keyboards import get_ai_services_keyboard, get_time_slots_keyboard
from ..utils.constants import SECTION_DESCRIPTIONS, ERROR_MESSAGES, SUCCESS_MESSAGES


# Создаем роутер для ИИ консультации
ai_router = Router()


# Состояния ИИ консультации
class AIConsultationStates(StatesGroup):
    waiting_for_problem = State()
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


# === ИИ КОНСУЛЬТАЦИЯ ===

@ai_router.message(F.text == "🤖 Консультация ИИ")
async def start_ai_consultation(message: Message, state: FSMContext, user):
    """Начало ИИ консультации"""
    if not user:
        await message.answer(
            "❌ Для получения консультации необходимо зарегистрироваться!\n"
            "Выполните команду /start"
        )
        return
    
    try:
        sent_message = await message.answer(
            f"{SECTION_DESCRIPTIONS['AI_CONSULTATION']}",
            parse_mode='Markdown'
        )
        await state.update_data(current_message_id=sent_message.message_id)
        await state.set_state(AIConsultationStates.waiting_for_problem)
    
    except Exception as e:
        logging.error(f"Ошибка в start_ai_consultation: {e}")
        await message.answer(
            "Произошла ошибка при запуске консультации.\n"
            "Попробуйте еще раз."
        )


@ai_router.message(AIConsultationStates.waiting_for_problem)
async def process_ai_consultation(message: Message, state: FSMContext, 
                                db_queries: DatabaseQueries, ai_service: AIConsultationService, is_admin: bool = False):
    """Обработка описания проблемы пользователем"""
    try:
        # Удаляем сообщение пользователя
        await delete_current_message(message)
        
        # Валидация описания проблемы
        is_valid, error_msg, cleaned_problem = ValidationService.validate_ai_problem_data(message.text)
        
        if not is_valid:
            await message.answer(error_msg)
            return
        
        # Показываем индикатор загрузки
        loading_msg = await message.answer("🤖 Анализирую проблему...")
        
        try:
            # Получаем все услуги для ИИ анализа
            all_services = []
            page = 0
            while True:
                services_page = await db_queries.get_services(page, 100)
                if not services_page:
                    break
                all_services.extend(services_page)
                page += 1
            
            if not all_services:
                await delete_current_message(loading_msg)
                await message.answer(
                    "❌ К сожалению, услуги временно недоступны.\n"
                    "Попробуйте позже или обратитесь в поддержку."
                )
                await state.clear()
                return
            
            # Обрабатываем консультацию через ИИ сервис
            result = await ai_service.process_consultation(cleaned_problem, all_services)
            
            await delete_current_message(loading_msg)
            
            if not result['success']:
                await message.answer(
                    f"❌ **Ошибка консультации**\n\n{result['error']}\n\n"
                    "Попробуйте описать проблему по-другому или обратитесь в поддержку.",
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode='Markdown'
                )
                await state.clear()
                return
            
            # Формируем ответ пользователю
            text = "🤖 **Консультация ИИ**\n\n"
            text += f"**Ваша проблема:** {cleaned_problem[:100]}{'...' if len(cleaned_problem) > 100 else ''}\n\n"
            
            if result.get('fallback'):
                text += "**Рекомендации (базовый анализ):**\n"
            else:
                text += "**Рекомендации от ИИ:**\n"
            
            text += f"{result['ai_response']}\n\n"
            
            # Добавляем информацию о рекомендуемых услугах
            if result['recommended_services']:
                # Валидируем рекомендованные услуги
                valid_services = ai_service.validate_recommended_services(
                    result['recommended_services'], all_services
                )
                
                if valid_services:
                    services_text, total_cost = ai_service.format_services_info(valid_services, all_services)
                    
                    text += "**Рекомендуемые услуги:**\n"
                    text += services_text
                    text += f"\n💰 **Общая стоимость:** {total_cost}₽"
                    
                    # Сохраняем рекомендации в state (НЕ ОЧИЩАЕМ STATE!)
                    await state.update_data(recommended_services=valid_services)
                    
                    keyboard = get_ai_services_keyboard(has_services=True)
                else:
                    text += "\n❓ Рекомендованные услуги не найдены в каталоге."
                    keyboard = get_ai_services_keyboard(has_services=False)
            else:
                text += "\n❓ Не удалось подобрать подходящие услуги для вашей проблемы."
                keyboard = get_ai_services_keyboard(has_services=False)
            
            sent_message = await message.answer(text, reply_markup=keyboard, parse_mode='Markdown')
            await state.update_data(current_message_id=sent_message.message_id)
            
            # НЕ ОЧИЩАЕМ STATE! Данные нужны для добавления в заказ
            
        except Exception as e:
            logging.error(f"Ошибка ИИ обработки: {e}")
            
            await delete_current_message(loading_msg)
            
            await message.answer(
                f"{ERROR_MESSAGES['AI_ERROR']}\n\n"
                "**Возможные причины:**\n"
                "• Проблемы с подключением к ИИ\n" 
                "• Превышен лимит запросов\n"
                "• Временная недоступность сервиса\n\n"
                "Попробуйте еще раз или обратитесь в поддержку.",
                reply_markup=get_main_menu_keyboard(is_admin=is_admin),
                parse_mode='Markdown'
            )
            await state.clear()
    
    except Exception as e:
        logging.error(f"Критическая ошибка в process_ai_consultation: {e}")
        await message.answer(
            "Произошла критическая ошибка при обработке консультации.\n"
            "Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()


@ai_router.callback_query(F.data == "add_ai_services")
async def add_ai_recommended_services(callback: CallbackQuery, state: FSMContext):
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
        await callback.answer(SUCCESS_MESSAGES['AI_SERVICES_ADDED'])
    
    except Exception as e:
        logging.error(f"Ошибка в add_ai_recommended_services: {e}")
        await callback.answer("Ошибка при добавлении услуг в заказ")


@ai_router.callback_query(F.data == "new_ai_consultation")
async def new_ai_consultation(callback: CallbackQuery, state: FSMContext):
    """Новая ИИ консультация"""
    # Очищаем state только при запросе новой консультации
    await state.clear()
    
    await callback.message.edit_text(
        f"{SECTION_DESCRIPTIONS['AI_CONSULTATION']}",
        parse_mode='Markdown'
    )
    await state.set_state(AIConsultationStates.waiting_for_problem)
    await callback.answer()


# === ИСТОРИЯ КОНСУЛЬТАЦИЙ (для будущего развития) ===

@ai_router.callback_query(F.data == "ai_history")
async def show_ai_consultation_history(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Показ истории ИИ консультаций"""
    try:
        # В будущем можно добавить таблицу для хранения истории консультаций
        await callback.message.edit_text(
            "📋 **История консультаций**\n\n"
            "Функция находится в разработке.\n"
            "В будущем здесь будет отображаться история ваших обращений к ИИ консультанту.",
            parse_mode='Markdown'
        )
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_ai_consultation_history: {e}")
        await callback.answer("Ошибка при загрузке истории")


# === НАСТРОЙКИ ИИ (для админов) ===

@ai_router.callback_query(F.data == "ai_settings")
async def show_ai_settings(callback: CallbackQuery, ai_service: AIConsultationService):
    """Настройки ИИ консультанта (только для админов)"""
    try:
        # Проверка доступности ИИ сервиса
        is_available = ai_service.check_service_availability()
        
        text = "⚙️ **Настройки ИИ консультанта**\n\n"
        text += f"**Статус сервиса:** {'🟢 Доступен' if is_available else '🔴 Недоступен'}\n"
        text += f"**Модель:** Gemini 1.5 Flash\n"
        text += f"**Резервная логика:** Включена\n\n"
        
        if is_available:
            text += "✅ ИИ консультант работает нормально"
        else:
            text += "❌ Проблемы с ИИ сервисом\n"
            text += "Пользователи получают рекомендации на основе ключевых слов"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Проверить статус", callback_data="check_ai_status")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_ai_settings: {e}")
        await callback.answer("Ошибка при загрузке настроек")


@ai_router.callback_query(F.data == "check_ai_status")
async def check_ai_status(callback: CallbackQuery, ai_service: AIConsultationService):
    """Проверка статуса ИИ сервиса"""
    try:
        await callback.answer("Проверяю статус ИИ...")
        
        is_available = ai_service.check_service_availability()
        
        if is_available:
            text = "✅ **Проверка завершена**\n\nИИ сервис работает нормально"
        else:
            text = "❌ **Проверка завершена**\n\nИИ сервис недоступен"
        
        await callback.message.edit_text(text, parse_mode='Markdown')
    
    except Exception as e:
        logging.error(f"Ошибка в check_ai_status: {e}")
        await callback.answer("Ошибка при проверке статуса")


# === ПРИМЕРЫ ПРОБЛЕМ ===

@ai_router.callback_query(F.data == "ai_examples")
async def show_problem_examples(callback: CallbackQuery, state: FSMContext):
    """Показ примеров описания проблем"""
    try:
        text = "💡 **Примеры описания проблем**\n\n"
        text += "**Хорошие примеры:**\n\n"
        text += "• Компьютер стал очень медленно работать, особенно при запуске программ. "
        text += "Вентиляторы шумят громче обычного.\n\n"
        text += "• При включении компьютера появляется синий экран с ошибкой. "
        text += "Это началось после установки новой программы.\n\n"
        text += "• В играх стали появляться лаги и низкий FPS. "
        text += "Раньше все работало плавно.\n\n"
        text += "• Постоянно всплывают рекламные окна в браузере, "
        text += "компьютер сам открывает сайты.\n\n"
        text += "**Чем подробнее описание, тем точнее рекомендации!**"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Начать консультацию", callback_data="new_ai_consultation")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_problem_examples: {e}")
        await callback.answer("Ошибка при загрузке примеров")