"""
Обработчики услуг и мастеров
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from ..database.queries import DatabaseQueries
from ..keyboards.order_keyboards import (
    get_services_keyboard, get_service_detail_keyboard,
    get_masters_keyboard, get_master_detail_keyboard
)
from ..utils.constants import SECTION_DESCRIPTIONS, LIMITS


# Создаем роутер для услуг
services_router = Router()


# === КАТАЛОГ УСЛУГ ===

@services_router.message(F.text == "📋 Описание услуг")
async def show_services_catalog(message: Message, state: FSMContext, db_queries: DatabaseQueries):
    """Показ каталога услуг"""
    try:
        services = await db_queries.get_services(0, LIMITS['MAX_SERVICES_PER_PAGE'])
        total_services = await db_queries.get_services_count()
        total_pages = (total_services + LIMITS['MAX_SERVICES_PER_PAGE'] - 1) // LIMITS['MAX_SERVICES_PER_PAGE']
        
        if not services:
            await message.answer(
                "❌ К сожалению, каталог услуг временно недоступен.\n"
                "Попробуйте позже или обратитесь в поддержку."
            )
            return
        
        await state.update_data(view_services_page=0)
        
        keyboard = get_services_keyboard(services, 0, total_pages, set(), "view_service")
        sent_message = await message.answer(
            f"{SECTION_DESCRIPTIONS['SERVICE_CATALOG']}\n\n"
            f"**Страница 1 из {total_pages}**",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        await state.update_data(current_message_id=sent_message.message_id)
    
    except Exception as e:
        logging.error(f"Ошибка в show_services_catalog: {e}")
        await message.answer(
            "Произошла ошибка при загрузке каталога услуг.\n"
            "Попробуйте еще раз."
        )


@services_router.callback_query(F.data.startswith("view_service_"))
async def handle_service_view(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Обработка просмотра услуг"""
    try:
        callback_parts = callback.data.split("_")
        
        if len(callback_parts) >= 4 and callback_parts[2] == "page":
            # Навигация по страницам
            page = int(callback_parts[3])
            await handle_services_catalog_pagination(callback, state, db_queries, page)
        else:
            # Просмотр конкретной услуги
            service_id = int(callback_parts[2])
            await show_service_details(callback, state, db_queries, service_id)
    
    except (ValueError, IndexError) as e:
        logging.error(f"Ошибка в handle_service_view: {e}")
        await callback.answer("Ошибка обработки запроса")
    except Exception as e:
        logging.error(f"Критическая ошибка в handle_service_view: {e}")
        await callback.answer("Произошла ошибка")


async def handle_services_catalog_pagination(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries, page: int):
    """Пагинация каталога услуг"""
    try:
        await state.update_data(view_services_page=page)
        
        services = await db_queries.get_services(page, LIMITS['MAX_SERVICES_PER_PAGE'])
        total_services = await db_queries.get_services_count()
        total_pages = (total_services + LIMITS['MAX_SERVICES_PER_PAGE'] - 1) // LIMITS['MAX_SERVICES_PER_PAGE']
        
        keyboard = get_services_keyboard(services, page, total_pages, set(), "view_service")
        await callback.message.edit_text(
            f"{SECTION_DESCRIPTIONS['SERVICE_CATALOG']}\n\n"
            f"**Страница {page + 1} из {total_pages}**",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в handle_services_catalog_pagination: {e}")
        await callback.answer("Ошибка при навигации по каталогу")


async def show_service_details(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries, service_id: int):
    """Показ детальной информации об услуге"""
    try:
        service = await db_queries.get_service_by_id(service_id)
        
        if not service:
            await callback.answer("Услуга не найдена")
            return
        
        # Форматируем время выполнения
        duration = service['duration_minutes']
        if duration >= 60:
            hours = duration // 60
            minutes = duration % 60
            duration_str = f"{hours} ч"
            if minutes > 0:
                duration_str += f" {minutes} мин"
        else:
            duration_str = f"{duration} мин"
        
        text = f"🛠️ **{service['name']}**\n\n"
        text += f"💰 **Цена:** {service['price']}₽\n"
        text += f"⏱️ **Время выполнения:** {duration_str}\n\n"
        text += f"📝 **Описание:**\n{service['description']}\n\n"
        
        # Добавляем рекомендации
        if 'диагностика' in service['name'].lower():
            text += "💡 **Рекомендуется как первый шаг** при неясных проблемах с компьютером."
        elif 'чистка' in service['name'].lower():
            text += "💡 **Рекомендуется проводить** каждые 6-12 месяцев для поддержания производительности."
        elif 'термопаста' in service['name'].lower():
            text += "💡 **Рекомендуется менять** каждые 2-3 года или при перегреве процессора."
        elif 'windows' in service['name'].lower():
            text += "💡 **Включает установку** базовых драйверов и необходимых программ."
        
        keyboard = get_service_detail_keyboard()
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_service_details: {e}")
        await callback.answer("Ошибка при загрузке информации об услуге")


@services_router.callback_query(F.data == "back_to_services_catalog")
async def back_to_services_catalog(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Возврат к каталогу услуг"""
    try:
        data = await state.get_data()
        page = data.get('view_services_page', 0)
        
        services = await db_queries.get_services(page, LIMITS['MAX_SERVICES_PER_PAGE'])
        total_services = await db_queries.get_services_count()
        total_pages = (total_services + LIMITS['MAX_SERVICES_PER_PAGE'] - 1) // LIMITS['MAX_SERVICES_PER_PAGE']
        
        keyboard = get_services_keyboard(services, page, total_pages, set(), "view_service")
        await callback.message.edit_text(
            f"{SECTION_DESCRIPTIONS['SERVICE_CATALOG']}\n\n"
            f"**Страница {page + 1} из {total_pages}**",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в back_to_services_catalog: {e}")
        await callback.answer("Ошибка при возврате к каталогу")


# === МАСТЕРА ===

@services_router.message(F.text == "👥 Мастера")
async def show_masters_list(message: Message, state: FSMContext, db_queries: DatabaseQueries):
    """Показ списка мастеров"""
    try:
        masters = await db_queries.get_masters(0, LIMITS['MAX_MASTERS_PER_PAGE'])
        total_masters = await db_queries.get_masters_count()
        total_pages = (total_masters + LIMITS['MAX_MASTERS_PER_PAGE'] - 1) // LIMITS['MAX_MASTERS_PER_PAGE']
        
        if not masters:
            await message.answer(
                "❌ К сожалению, информация о мастерах временно недоступна.\n"
                "Попробуйте позже или обратитесь в поддержку."
            )
            return
        
        keyboard = get_masters_keyboard(masters, 0, total_pages)
        sent_message = await message.answer(
            f"{SECTION_DESCRIPTIONS['MASTERS_LIST']}\n\n"
            f"**Всего мастеров:** {total_masters}",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        await state.update_data(current_message_id=sent_message.message_id)
    
    except Exception as e:
        logging.error(f"Ошибка в show_masters_list: {e}")
        await message.answer(
            "Произошла ошибка при загрузке списка мастеров.\n"
            "Попробуйте еще раз."
        )


@services_router.callback_query(F.data.startswith("master_"))
async def view_master_details(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Просмотр информации о мастере"""
    try:
        master_id = int(callback.data.split("_")[1])
        master = await db_queries.get_master_by_id(master_id)
        
        if not master:
            await callback.answer("Мастер не найден")
            return
        
        # Форматируем опыт работы
        experience = master['experience_years']
        if experience == 1:
            exp_text = "1 год"
        elif 2 <= experience <= 4:
            exp_text = f"{experience} года"
        else:
            exp_text = f"{experience} лет"
        
        # Генерируем описание на основе опыта и рейтинга
        if master['rating'] >= 4.8:
            quality_text = "Один из лучших наших мастеров!"
        elif master['rating'] >= 4.5:
            quality_text = "Высококвалифицированный специалист."
        else:
            quality_text = "Опытный мастер с хорошими отзывами."
        
        if experience >= 7:
            exp_desc = "Эксперт с большим опытом работы."
        elif experience >= 4:
            exp_desc = "Опытный специалист."
        else:
            exp_desc = "Молодой перспективный мастер."
        
        text = f"👨‍🔧 **{master['name']}**\n\n"
        text += f"🎯 **Опыт работы:** {exp_text}\n"
        text += f"⭐ **Рейтинг:** {master['rating']}/5.0\n\n"
        text += f"📋 **О мастере:**\n{quality_text} {exp_desc}\n\n"
        text += "🔧 **Специализация:**\n"
        text += "• Диагностика и ремонт компьютеров\n"
        text += "• Установка и настройка ПО\n"
        text += "• Чистка и профилактика\n"
        text += "• Восстановление данных"
        
        keyboard = get_master_detail_keyboard()
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except (ValueError, IndexError) as e:
        logging.error(f"Ошибка в view_master_details: {e}")
        await callback.answer("Ошибка обработки запроса")
    except Exception as e:
        logging.error(f"Критическая ошибка в view_master_details: {e}")
        await callback.answer("Произошла ошибка")


@services_router.callback_query(F.data == "back_to_masters_catalog")
async def back_to_masters_catalog(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Возврат к списку мастеров"""
    try:
        masters = await db_queries.get_masters(0, LIMITS['MAX_MASTERS_PER_PAGE'])
        total_masters = await db_queries.get_masters_count()
        total_pages = (total_masters + LIMITS['MAX_MASTERS_PER_PAGE'] - 1) // LIMITS['MAX_MASTERS_PER_PAGE']
        
        keyboard = get_masters_keyboard(masters, 0, total_pages)
        await callback.message.edit_text(
            f"{SECTION_DESCRIPTIONS['MASTERS_LIST']}\n\n"
            f"**Всего мастеров:** {total_masters}",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в back_to_masters_catalog: {e}")
        await callback.answer("Ошибка при возврате к списку мастеров")


# === ПОИСК УСЛУГ ===

@services_router.message(F.text.startswith("🔍"))
async def search_services(message: Message, db_queries: DatabaseQueries):
    """Поиск услуг по ключевым словам"""
    try:
        # Извлекаем поисковый запрос
        query = message.text.replace("🔍", "").strip()
        
        if len(query) < 3:
            await message.answer(
                "🔍 **Поиск услуг**\n\n"
                "Для поиска введите минимум 3 символа.\n"
                "Пример: `🔍 диагностика`",
                parse_mode='Markdown'
            )
            return
        
        # Получаем все услуги для поиска
        all_services = await db_queries.get_services(0, 100)  # Получаем больше услуг для поиска
        
        # Фильтруем услуги по запросу
        found_services = []
        query_lower = query.lower()
        
        for service in all_services:
            if (query_lower in service['name'].lower() or 
                query_lower in service['description'].lower()):
                found_services.append(service)
        
        if not found_services:
            await message.answer(
                f"🔍 **Результаты поиска: «{query}»**\n\n"
                "❌ Услуги не найдены.\n\n"
                "Попробуйте другие ключевые слова или посмотрите полный каталог услуг.",
                parse_mode='Markdown'
            )
            return
        
        # Формируем результаты поиска
        text = f"🔍 **Результаты поиска: «{query}»**\n\n"
        text += f"Найдено услуг: **{len(found_services)}**\n\n"
        
        for i, service in enumerate(found_services[:10], 1):  # Показываем максимум 10
            text += f"{i}. **{service['name']}** - {service['price']}₽\n"
            text += f"   _{service['description'][:60]}..._\n\n"
        
        if len(found_services) > 10:
            text += f"... и еще {len(found_services) - 10} услуг.\n\n"
        
        text += "Для просмотра полного каталога используйте кнопку «📋 Описание услуг»."
        
        await message.answer(text, parse_mode='Markdown')
    
    except Exception as e:
        logging.error(f"Ошибка в search_services: {e}")
        await message.answer(
            "Произошла ошибка при поиске услуг.\n"
            "Попробуйте еще раз."
        )


# === ПОПУЛЯРНЫЕ УСЛУГИ ===

@services_router.callback_query(F.data == "popular_services")
async def show_popular_services(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Показ популярных услуг"""
    try:
        # ID популярных услуг (можно вынести в константы)
        popular_service_ids = [1, 2, 3, 4, 9]  # Диагностика, чистка, термопаста, Windows, антивирус
        
        text = "🔥 **Популярные услуги**\n\n"
        
        for i, service_id in enumerate(popular_service_ids, 1):
            service = await db_queries.get_service_by_id(service_id)
            if service:
                text += f"{i}. **{service['name']}** - {service['price']}₽\n"
                text += f"   ⏱️ {service['duration_minutes']} мин\n\n"
        
        text += "Выберите услуги из каталога для создания заказа!"
        
        # Можно добавить инлайн-клавиатуру с быстрыми действиями
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛠️ Сделать заказ", callback_data="make_order")],
            [InlineKeyboardButton(text="📋 Полный каталог", callback_data="view_all_services")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_popular_services: {e}")
        await callback.answer("Ошибка при загрузке популярных услуг")