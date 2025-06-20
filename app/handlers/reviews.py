"""
Обработчики отзывов
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..database.queries import DatabaseQueries
from ..services.validation_service import ValidationService
from ..keyboards.main_menu import get_main_menu_keyboard
from ..keyboards.profile_keyboards import (
    get_reviews_keyboard, get_review_creation_keyboard, get_rating_keyboard
)
from ..utils.constants import SECTION_DESCRIPTIONS, SUCCESS_MESSAGES


# Создаем роутер для отзывов
reviews_router = Router()


# Состояния создания отзыва
class ReviewStates(StatesGroup):
    selecting_order = State()
    rating_order = State()
    writing_comment = State()


async def delete_current_message(message):
    """Безопасное удаление сообщения"""
    try:
        await message.delete()
    except Exception:
        pass


# === ПРОСМОТР ОТЗЫВОВ ===

@reviews_router.message(F.text == "⭐ Отзывы")
async def show_reviews(message: Message, state: FSMContext, db_queries: DatabaseQueries):
    """Показ отзывов клиентов"""
    try:
        reviews = await db_queries.get_recent_reviews(10)
        
        text = f"{SECTION_DESCRIPTIONS['REVIEWS_LIST']}"
        
        if reviews:
            for review in reviews:
                rating = review['rating']
                comment = review['comment']
                created_at = review['created_at']
                user_name = review['name']
                
                stars = "⭐" * rating
                # Берем только дату без времени
                date_str = created_at[:10] if created_at else "дата неизвестна"
                
                text += f"{stars} **{user_name}** _{date_str}_\n"
                text += f"{comment}\n\n"
        else:
            text += "Пока нет отзывов. Станьте первым!\n\n"
            text += "После выполнения заказа вы сможете оставить отзыв о работе мастера."
        
        keyboard = get_reviews_keyboard()
        sent_message = await message.answer(
            text, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
        await state.update_data(current_message_id=sent_message.message_id)
    
    except Exception as e:
        logging.error(f"Ошибка в show_reviews: {e}")
        await message.answer(
            "Произошла ошибка при загрузке отзывов.\n"
            "Попробуйте еще раз."
        )


# === СОЗДАНИЕ ОТЗЫВА ===

@reviews_router.callback_query(F.data == "create_review")
async def start_create_review(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Начало создания отзыва"""
    try:
        # Получаем заказы пользователя
        orders = await db_queries.get_user_orders(callback.from_user.id, 20)
        
        logging.info(f"Пользователь {callback.from_user.id}: найдено {len(orders) if orders else 0} заказов")
        
        if not orders:
            new_text = (
                f"{SECTION_DESCRIPTIONS['REVIEW_CREATION']}\n\n"
                "❌ У вас пока нет заказов для оценки.\n"
                "Сначала сделайте заказ и дождитесь его выполнения!"
            )
            keyboard = get_reviews_keyboard()
            
            # Проверяем, отличается ли новый текст от текущего
            current_text = callback.message.text or ""
            if new_text != current_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            await callback.answer()
            return
        
        # Фильтруем заказы без отзывов
        available_orders = []
        for order in orders:
            order_id = order['id']
            order_status = order['status']
            
            logging.info(f"Заказ {order_id}: статус = {order_status}")
            
            # Проверяем, есть ли уже отзыв на этот заказ
            has_review = await db_queries.check_review_exists(callback.from_user.id, order_id)
            logging.info(f"Заказ {order_id}: отзыв существует = {has_review}")
            
            # Заказ доступен для отзыва если статус 'completed' и нет отзыва
            if not has_review and order_status == 'completed':
                available_orders.append(order)
                logging.info(f"Заказ {order_id} добавлен для отзыва")
        
        logging.info(f"Доступно для отзыва: {len(available_orders)} заказов")
        
        if not available_orders:
            # Проверяем причину недоступности
            completed_orders = [o for o in orders if o['status'] == 'completed']
            
            if not completed_orders:
                new_text = (
                    f"{SECTION_DESCRIPTIONS['REVIEW_CREATION']}\n\n"
                    "⏳ У вас нет завершенных заказов для оценки.\n"
                    "Дождитесь выполнения ваших заказов!"
                )
            else:
                new_text = (
                    f"{SECTION_DESCRIPTIONS['REVIEW_CREATION']}\n\n"
                    "✅ Вы уже оставили отзывы на все выполненные заказы!\n"
                    "Спасибо за обратную связь!"
                )
            
            keyboard = get_reviews_keyboard()
            
            # Проверяем, отличается ли новый текст от текущего
            current_text = callback.message.text or ""
            if new_text != current_text:
                await callback.message.edit_text(
                    new_text,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
            await callback.answer()
            return
        
        # Есть заказы для отзыва
        new_text = (
            f"{SECTION_DESCRIPTIONS['REVIEW_CREATION']}\n\n"
            "Выберите заказ для оценки:"
        )
        keyboard = get_review_creation_keyboard(available_orders)
        
        # Проверяем, отличается ли новый контент от текущего
        current_text = callback.message.text or ""
        if new_text != current_text:
            await callback.message.edit_text(
                new_text,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            # Если текст тот же, просто обновляем клавиатуру
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        
        await state.set_state(ReviewStates.selecting_order)
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в start_create_review: {e}")
        await callback.answer("Ошибка при создании отзыва")


@reviews_router.callback_query(F.data.startswith("review_order_"))
async def select_order_for_review(callback: CallbackQuery, state: FSMContext, db_queries: DatabaseQueries):
    """Выбор заказа для отзыва"""
    try:
        order_id = int(callback.data.split("_")[2])
        order = await db_queries.get_order_by_id(order_id)
        
        if not order or order['user_id'] != callback.from_user.id:
            await callback.answer("Заказ не найден")
            return
        
        # Проверяем, что отзыв еще не создан
        has_review = await db_queries.check_review_exists(callback.from_user.id, order_id)
        if has_review:
            await callback.answer("На этот заказ уже есть отзыв")
            return
        
        await state.update_data(review_order_id=order_id)
        await state.set_state(ReviewStates.rating_order)
        
        text = f"{SECTION_DESCRIPTIONS['REVIEW_RATING']}\n\n"
        text += f"**Заказ №{order_id}**\n"
        text += f"**Дата:** {order['order_date']} в {order['order_time']}\n"
        text += f"**Мастер:** {order['master_name']}\n"
        text += f"**Стоимость:** {order['total_cost']}₽\n\n"
        text += "Поставьте оценку работе мастера:"
        
        keyboard = get_rating_keyboard()
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except (ValueError, IndexError) as e:
        logging.error(f"Ошибка в select_order_for_review: {e}")
        await callback.answer("Ошибка обработки запроса")
    except Exception as e:
        logging.error(f"Критическая ошибка в select_order_for_review: {e}")
        await callback.answer("Произошла ошибка")


@reviews_router.callback_query(F.data.startswith("rating_"))
async def handle_rating_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора рейтинга"""
    try:
        rating = int(callback.data.split("_")[1])
        await state.update_data(review_rating=rating)
        await state.set_state(ReviewStates.writing_comment)
        
        stars = "⭐" * rating
        
        await callback.message.edit_text(
            f"{SECTION_DESCRIPTIONS['REVIEW_COMMENT']}\n\n"
            f"Ваша оценка: {stars} ({rating}/5)\n\n"
            "Теперь напишите комментарий о качестве работы:\n\n"
            "Требования:\n"
            "• От 5 до 500 символов\n"
            "• Опишите, что понравилось или не понравилось",
            parse_mode='Markdown'
        )
        await callback.answer()
    
    except (ValueError, IndexError) as e:
        logging.error(f"Ошибка в handle_rating_selection: {e}")
        await callback.answer("Ошибка обработки рейтинга")
    except Exception as e:
        logging.error(f"Критическая ошибка в handle_rating_selection: {e}")
        await callback.answer("Произошла ошибка")


@reviews_router.message(ReviewStates.writing_comment)
async def process_review_comment(message: Message, state: FSMContext, db_queries: DatabaseQueries):
    """Обработка комментария к отзыву"""
    try:
        # Удаляем сообщение пользователя
        await delete_current_message(message)
        
        data = await state.get_data()
        order_id = data.get('review_order_id')
        rating = data.get('review_rating')
        
        if not order_id or not rating:
            await message.answer(
                "❌ Ошибка: потеряны данные отзыва.\n"
                "Начните создание отзыва заново.",
                reply_markup=get_main_menu_keyboard()
            )
            await state.clear()
            return
        
        # Валидация данных отзыва
        is_valid, error_msg, cleaned_data = ValidationService.validate_review_data(rating, message.text)
        
        if not is_valid:
            await message.answer(error_msg)
            return
        
        # Создаем отзыв в БД
        success = await db_queries.create_review(
            user_id=message.from_user.id,
            order_id=order_id,
            rating=cleaned_data['rating'],
            comment=cleaned_data['comment']
        )
        
        if success:
            stars = "⭐" * rating
            await message.answer(
                f"✅ **Отзыв создан!**\n\n"
                f"Ваша оценка: {stars} ({rating}/5)\n"
                f"Комментарий: {cleaned_data['comment']}\n\n"
                f"{SUCCESS_MESSAGES['REVIEW_CREATED']}",
                reply_markup=get_main_menu_keyboard(),
                parse_mode='Markdown'
            )
            
            logging.info(
                f"Создан отзыв: пользователь {message.from_user.id}, "
                f"заказ {order_id}, рейтинг {rating}"
            )
        else:
            await message.answer(
                "❌ Произошла ошибка при создании отзыва.\n"
                "Попробуйте еще раз или обратитесь в поддержку.",
                reply_markup=get_main_menu_keyboard()
            )
        
        await state.clear()
    
    except Exception as e:
        logging.error(f"Ошибка в process_review_comment: {e}")
        await message.answer(
            "Произошла ошибка при создании отзыва.\n"
            "Попробуйте еще раз.",
            reply_markup=get_main_menu_keyboard()
        )
        await state.clear()


# === СТАТИСТИКА ОТЗЫВОВ ===

@reviews_router.callback_query(F.data == "reviews_stats")
async def show_reviews_statistics(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Показ статистики отзывов"""
    try:
        # Получаем все отзывы для статистики
        all_reviews = await db_queries.get_recent_reviews(100)
        
        if not all_reviews:
            await callback.message.edit_text(
                "📊 **Статистика отзывов**\n\n"
                "Пока нет отзывов для анализа.",
                parse_mode='Markdown'
            )
            return
        
        # Подсчитываем статистику
        total_reviews = len(all_reviews)
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        total_rating = 0
        
        for review in all_reviews:
            rating = review['rating']
            rating_counts[rating] += 1
            total_rating += rating
        
        average_rating = total_rating / total_reviews
        
        # Формируем текст статистики
        text = "📊 **Статистика отзывов**\n\n"
        text += f"**Общее количество:** {total_reviews}\n"
        text += f"**Средняя оценка:** {average_rating:.1f}/5.0\n\n"
        text += "**Распределение оценок:**\n"
        
        for rating in range(5, 0, -1):
            count = rating_counts[rating]
            percentage = (count / total_reviews) * 100 if total_reviews > 0 else 0
            stars = "⭐" * rating
            bar = "█" * int(percentage / 5)  # Простая визуализация
            text += f"{stars} {rating}: {count} ({percentage:.1f}%) {bar}\n"
        
        # Добавляем последние отзывы
        text += "\n**Последние отзывы:**\n"
        for review in all_reviews[:3]:
            stars = "⭐" * review['rating']
            comment = review['comment'][:50] + "..." if len(review['comment']) > 50 else review['comment']
            text += f"{stars} {comment}\n"
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К отзывам", callback_data="back_to_reviews")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_reviews_statistics: {e}")
        await callback.answer("Ошибка при загрузке статистики")


# === ЛУЧШИЕ ОТЗЫВЫ ===

@reviews_router.callback_query(F.data == "best_reviews")
async def show_best_reviews(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Показ лучших отзывов (5 звезд)"""
    try:
        all_reviews = await db_queries.get_recent_reviews(50)
        
        # Фильтруем только 5-звездочные отзывы
        best_reviews = [review for review in all_reviews if review['rating'] == 5]
        
        if not best_reviews:
            await callback.message.edit_text(
                "⭐ **Лучшие отзывы**\n\n"
                "Пока нет отзывов с оценкой 5 звезд.\n"
                "Станьте первым, кто поставит максимальную оценку!",
                parse_mode='Markdown'
            )
            return
        
        text = f"⭐ **Лучшие отзывы** ({len(best_reviews)} отзывов с 5 звездами)\n\n"
        
        for i, review in enumerate(best_reviews[:5], 1):  # Показываем топ-5
            comment = review['comment']
            user_name = review['name']
            date_str = review['created_at'][:10] if review['created_at'] else ""
            
            text += f"{i}. ⭐⭐⭐⭐⭐ **{user_name}** _{date_str}_\n"
            text += f"   {comment}\n\n"
        
        if len(best_reviews) > 5:
            text += f"... и еще {len(best_reviews) - 5} отличных отзывов!"
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="reviews_stats")],
            [InlineKeyboardButton(text="🔙 К отзывам", callback_data="back_to_reviews")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в show_best_reviews: {e}")
        await callback.answer("Ошибка при загрузке лучших отзывов")


# === НАВИГАЦИЯ ===

@reviews_router.callback_query(F.data == "back_to_reviews")
async def back_to_reviews(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Возврат к списку отзывов"""
    try:
        reviews = await db_queries.get_recent_reviews(10)
        
        text = f"{SECTION_DESCRIPTIONS['REVIEWS_LIST']}"
        
        if reviews:
            for review in reviews:
                rating = review['rating']
                comment = review['comment']
                created_at = review['created_at']
                user_name = review['name']
                
                stars = "⭐" * rating
                date_str = created_at[:10] if created_at else "дата неизвестна"
                
                text += f"{stars} **{user_name}** _{date_str}_\n"
                text += f"{comment}\n\n"
        else:
            text += "Пока нет отзывов. Станьте первым!"
        
        # Расширенная клавиатура с дополнительными опциями
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Оставить отзыв", callback_data="create_review")],
            [
                InlineKeyboardButton(text="⭐ Лучшие отзывы", callback_data="best_reviews"),
                InlineKeyboardButton(text="📊 Статистика", callback_data="reviews_stats")
            ],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в back_to_reviews: {e}")
        await callback.answer("Ошибка при возврате к отзывам")


# === МОДЕРАЦИЯ ОТЗЫВОВ (для админов) ===

@reviews_router.callback_query(F.data == "moderate_reviews")
async def moderate_reviews(callback: CallbackQuery, db_queries: DatabaseQueries):
    """Модерация отзывов (только для админов)"""
    try:
        # Здесь должна быть проверка на админа
        # if callback.from_user.id not in admin_ids:
        #     await callback.answer("Доступ запрещен")
        #     return
        
        reviews = await db_queries.get_recent_reviews(20)
        
        text = "🛡️ **Модерация отзывов**\n\n"
        text += f"Всего отзывов: {len(reviews)}\n\n"
        
        # Показываем отзывы с возможностью модерации
        for review in reviews[:5]:
            rating = review['rating']
            comment = review['comment']
            user_name = review['name']
            
            stars = "⭐" * rating
            text += f"{stars} **{user_name}**\n"
            text += f"{comment[:100]}{'...' if len(comment) > 100 else ''}\n\n"
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К отзывам", callback_data="back_to_reviews")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode='Markdown')
        await callback.answer()
    
    except Exception as e:
        logging.error(f"Ошибка в moderate_reviews: {e}")
        await callback.answer("Ошибка модерации")