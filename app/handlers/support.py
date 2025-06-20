"""
Обработчики службы поддержки
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..database.queries import DatabaseQueries
from ..services.validation_service import ValidationService
from ..keyboards.main_menu import get_main_menu_keyboard
from ..keyboards.profile_keyboards import get_support_keyboard, get_faq_keyboard
from ..utils.constants import SECTION_DESCRIPTIONS, SUCCESS_MESSAGES


# Создаем роутер для поддержки
support_router = Router()


# Состояния поддержки
class SupportStates(StatesGroup):
    writing_message = State()


async def delete_current_message(message):
    """Безопасное удаление сообщения"""
    try:
        await message.delete()
    except Exception:
        pass


# === ГЛАВНОЕ МЕНЮ ПОДДЕРЖКИ ===

@support_router.message(F.text == "💬 Поддержка")
async def show_support_menu(message: Message, state: FSMContext, user):
    """Показ меню поддержки"""
    if not user:
        await message.answer(
            "❌ Для обращения в поддержку необходимо зарегистрироваться!\n"
            "Выполните команду /start"
        )
        return
    
    try:
        text = f"{SECTION_DESCRIPTIONS['SUPPORT_REQUEST']}"
        
        keyboard = get_support_keyboard()
        sent_message = await message.answer(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        await state.update_data(current_message_id=sent_message.message_id)
    
    except Exception as e:
        logging.error(f"Ошибка в show_support_menu: {e}")
        await message.answer(
            "Произошла ошибка при загрузке меню поддержки.\n"
            "Попробуйте еще раз."
        )


@support_router.callback_query(F.data == "write_support")
async def start_support_message(callback: CallbackQuery, state: FSMContext):
    """Начало написания сообщения в поддержку"""
    await callback.message.edit_text(
        "💬 **Написать в поддержку**\n\n"
        "Опишите вашу проблему или задайте вопрос.\n"
        "Наши специалисты обязательно вам помогут!\n\n"
        "**Требования к сообщению:**\n"
        "• От 10 до 1000 символов\n"
        "• Опишите проблему максимально подробно\n"
        "• Укажите, с каким заказом связана проблема (если применимо)",
        parse_mode='Markdown'
    )
    await state.set_state(SupportStates.writing_message)
    await callback.answer()


@support_router.message(SupportStates.writing_message)
async def process_support_message(message: Message, state: FSMContext, db_queries: DatabaseQueries):
    """Обработка сообщения в поддержку"""
    try:
        # Удаляем сообщение пользователя
        await delete_current_message(message)
        
        # Валидация сообщения
        is_valid, error_msg, cleaned_message = ValidationService.validate_support_request_data(message.text)
        
        if not is_valid:
            await message.answer(error_msg)
            return
        
        # Сохраняем обращение в БД
        success = await db_queries.save_support_request(message.from_user.id, cleaned_message)
        
        if success:
            await message.answer(
                f"📝 **Обращение принято!**\n\n"
                f"Ваше сообщение передано в службу поддержки.\n"
                f"Мы свяжемся с вами в ближайшее время.\n\n"
                f"**Ваше сообщение:**\n{cleaned_message[:200]}{'...' if len(cleaned_message) > 200 else ''}",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
            logging.info(
                f"Новое обращение в поддержку от пользователя {message.from_user.id}: "
                f"{cleaned_message[:50]}..."
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при отправке сообщения.\n"
                "Попробуйте еще раз или свяжитесь с нами другим способом.",
                reply_markup=get_main_menu_keyboard()
            )
        
        await state.clear()
    
    except Exception as e:
        logging.error(f"Ошибка в process_support_message: {e}")
        await message.answer(
            "Произошла ошибка при отправке сообщения в поддержку.\n"
            "Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()


# === FAQ ===

@support_router.callback_query(F.data == "faq")
async def show_faq(callback: CallbackQuery):
    """Показ часто задаваемых вопросов"""
    keyboard = get_faq_keyboard()
    
    await callback.message.edit_text(
        "❓ **Часто задаваемые вопросы**\n\n"
        "Выберите интересующую вас тему:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    await callback.answer()


@support_router.callback_query(F.data == "faq_order")
async def faq_how_to_order(callback: CallbackQuery):
    """FAQ: Как сделать заказ"""
    text = "❓ **Как сделать заказ?**\n\n"
    text += "**Пошаговая инструкция:**\n\n"
    text += "1️⃣ Нажмите кнопку «🛠️ Сделать заказ»\n"
    text += "2️⃣ Выберите необходимые услуги из каталога\n"
    text += "3️⃣ Укажите удобное время для визита мастера\n"
    text += "4️⃣ Выберите дату (доступны ближайшие 14 дней)\n"
    text += "5️⃣ Укажите адрес выезда мастера\n"
    text += "6️⃣ Проверьте данные и подтвердите заказ\n\n"
    text += "**Важно:**\n"
    text += "• Можно выбрать несколько услуг в одном заказе\n"
    text += "• Мастер свяжется с вами для уточнения деталей\n"
    text += "• Отменить заказ можно до начала работы"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠️ Сделать заказ", callback_data="make_order")],
        [InlineKeyboardButton(text="🔙 К FAQ", callback_data="faq")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
    await callback.answer()


@support_router.callback_query(F.data == "faq_payment")
async def faq_payment(callback: CallbackQuery):
    """FAQ: Оплата"""
    text = "💰 **Как происходит оплата?**\n\n"
    text += "**Способы оплаты:**\n"
    text += "• 💵 Наличными мастеру\n"
    text += "• 💳 Картой через терминал\n"
    text += "• 📱 Переводом на карту\n\n"
    text += "**Когда платить:**\n"
    text += "• Оплата после выполнения работ\n"
    text += "• Предоплата не требуется\n"
    text += "• Стоимость диагностики входит в стоимость ремонта\n\n"
    text += "**Гарантии:**\n"
    text += "• Все работы выполняются с гарантией\n"
    text += "• В случае некачественной работы - переделаем бесплатно\n"
    text += "• Предоставляем чек или квитанцию"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Описание услуг", callback_data="view_services")],
        [InlineKeyboardButton(text="🔙 К FAQ", callback_data="faq")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
    await callback.answer()


@support_router.callback_query(F.data == "faq_timing")
async def faq_timing(callback: CallbackQuery):
    """FAQ: Время выполнения"""
    text = "⏰ **Время выполнения работ**\n\n"
    text += "**Типичное время:**\n"
    text += "• 🔍 Диагностика: 30 минут\n"
    text += "• 🧹 Чистка от пыли: 45 минут\n"
    text += "• 🖥️ Установка Windows: 1.5 часа\n"
    text += "• 🔧 Замена компонентов: 30-60 минут\n"
    text += "• 🦠 Удаление вирусов: 45 минут\n\n"
    text += "**Факторы, влияющие на время:**\n"
    text += "• Сложность проблемы\n"
    text += "• Состояние компьютера\n"
    text += "• Необходимость дополнительных работ\n\n"
    text += "**Срочные работы:**\n"
    text += "• Возможность выезда в день обращения\n"
    text += "• Работаем с 10:00 до 22:00\n"
    text += "• В выходные дни по предварительной записи"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛠️ Сделать заказ", callback_data="make_order")],
        [InlineKeyboardButton(text="🔙 К FAQ", callback_data="faq")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
    await callback.answer()


@support_router.callback_query(F.data == "faq_warranty")
async def faq_warranty(callback: CallbackQuery):
    """FAQ: Гарантия"""
    text = "🛡️ **Гарантия на работы**\n\n"
    text += "**Мы гарантируем:**\n"
    text += "• ✅ Качественное выполнение всех работ\n"
    text += "• ✅ Использование оригинальных комплектующих\n"
    text += "• ✅ Сохранность ваших данных\n"
    text += "• ✅ Чистоту рабочего места\n\n"
    text += "**Сроки гарантии:**\n"
    text += "• 🔧 Ремонт компонентов: 6 месяцев\n"
    text += "• 🖥️ Установка ПО: 1 месяц\n"
    text += "• 🧹 Профилактические работы: 1 месяц\n"
    text += "• 💾 Восстановление данных: без гарантии на HDD/SSD\n\n"
    text += "**В случае проблем:**\n"
    text += "• Бесплатный повторный выезд\n"
    text += "• Устранение недочетов за наш счет\n"
    text += "• Компенсация при доказанной вине мастера"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Связаться с поддержкой", callback_data="write_support")],
        [InlineKeyboardButton(text="🔙 К FAQ", callback_data="faq")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
    await callback.answer()


@support_router.callback_query(F.data == "faq_ai")
async def faq_ai_consultation(callback: CallbackQuery):
    """FAQ: ИИ консультация"""
    text = "🤖 **Как работает ИИ консультация?**\n\n"
    text += "**Что это такое:**\n"
    text += "• Умный помощник для диагностики проблем\n"
    text += "• Анализирует описание и подбирает услуги\n"
    text += "• Работает на основе технологий Google Gemini\n\n"
    text += "**Как пользоваться:**\n"
    text += "1️⃣ Нажмите «🤖 Консультация ИИ»\n"
    text += "2️⃣ Опишите проблему максимально подробно\n"
    text += "3️⃣ Получите рекомендации по услугам\n"
    text += "4️⃣ Добавьте услуги в заказ одним кликом\n\n"
    text += "**Советы для лучшего результата:**\n"
    text += "• Опишите симптомы подробно\n"
    text += "• Укажите, когда проблема началась\n"
    text += "• Опишите, что вы уже пробовали делать\n\n"
    text += "**Точность:** 85-90% правильных рекомендаций"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Попробовать ИИ консультацию", callback_data="new_ai_consultation")],
        [InlineKeyboardButton(text="💡 Примеры проблем", callback_data="ai_examples")],
        [InlineKeyboardButton(text="🔙 К FAQ", callback_data="faq")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
    await callback.answer()


# === КОНТАКТЫ ===

@support_router.callback_query(F.data == "contacts")
async def show_contacts(callback: CallbackQuery):
    """Показ контактной информации"""
    text = "📞 **Контактная информация**\n\n"
    text += "**Служба поддержки:**\n"
    text += "📱 Телефон: +7 (XXX) XXX-XX-XX\n"
    text += "💬 Telegram: @support_bot\n"
    text += "📧 Email: support@repair.com\n\n"
    text += "**Режим работы:**\n"
    text += "🕘 Пн-Пт: 9:00 - 21:00\n"
    text += "🕘 Сб-Вс: 10:00 - 18:00\n\n"
    text += "**Экстренная связь:**\n"
    text += "📱 +7 (XXX) XXX-XX-XX (круглосуточно)\n\n"
    text += "**Адрес офиса:**\n"
    text += "📍 г. Москва, ул. Примерная, д. 1"
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать в поддержку", callback_data="write_support")],
        [InlineKeyboardButton(text="🔙 К поддержке", callback_data="support")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
    await callback.answer()


# === СТАТИСТИКА ПОДДЕРЖКИ (для админов) ===

@support_router.callback_query(F.data == "support_stats")
async def show_support_statistics(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Статистика обращений в поддержку"""
    try:
        # Получаем обращения в поддержку
        support_requests = await db_queries.get_support_requests(50)
        
        if not support_requests:
            text = "📊 **Статистика поддержки**\n\nОбращений пока нет."
        else:
            text = "📊 **Статистика поддержки**\n\n"
            text += f"**Всего обращений:** {len(support_requests)}\n\n"
            
            # Показываем последние обращения
            text += "**Последние обращения:**\n"
            for i, request in enumerate(support_requests[:5], 1):
                user_name = request['user_name']
                message_preview = request['message'][:50] + "..." if len(request['message']) > 50 else request['message']
                created_at = request['created_at'][:16] if request['created_at'] else ""
                
                text += f"{i}. **{user_name}** _{created_at}_\n"
                text += f"   {message_preview}\n\n"
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К поддержке", callback_data="support")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_support_statistics: {e}")
        await callback.answer("Ошибка при загрузке статистики")