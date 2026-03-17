from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.recommendations import get_recommendations
from bot.keyboards.reply import get_main_keyboard

router = Router()
recommendation_cache = {}


# 🔥 ОБРАБОТЧИК КНОПКИ "🤖 AI РЕКОМЕНДАЦИИ"
@router.message(F.text == "🤖 AI РЕКОМЕНДАЦИИ")
@router.message(Command("ai"))
async def ai_recommendations(message: Message):
    """Показать персональные рекомендации"""
    user_id = message.from_user.id

    await message.bot.send_chat_action(message.chat.id, action="typing")

    # Отправляем сообщение о начале анализа
    wait_msg = await message.answer(
        "🤖 Анализирую твои предпочтения...\n"
        "🔍 Сканирую историю поиска\n"
        "📊 Обрабатываю избранное\n"
        "✨ Генерирую рекомендации"
    )

    try:
        recommendations = await get_recommendations(user_id)
        await wait_msg.delete()

        if not recommendations:
            await message.answer(
                "😢 Пока недостаточно данных для рекомендаций.\n\n"
                "🔍 Ищи фильмы и добавляй в избранное, чтобы я лучше тебя узнал!",
                reply_markup=get_main_keyboard()
            )
            return

        # Сохраняем в кэш
        recommendation_cache[user_id] = recommendations

        await show_recommendation(message, user_id, 0)

    except Exception as e:
        await wait_msg.delete()
        await message.answer(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_keyboard()
        )


async def show_recommendation(message: Message, user_id: int, index: int):
    """Показать одну рекомендацию"""
    if user_id not in recommendation_cache:
        return

    recommendations = recommendation_cache[user_id]

    if index < 0 or index >= len(recommendations):
        return

    movie = recommendations[index]
    current = index + 1
    total = len(recommendations)

    # Клавиатура
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Навигация
    nav_buttons = []
    if current > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data="ai_prev"))
    nav_buttons.append(InlineKeyboardButton(text=f"🤖 {current}/{total}", callback_data="noop"))
    if current < total:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data="ai_next"))
    keyboard.inline_keyboard.append(nav_buttons)

    # Кнопки действий
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="📖 Подробнее", callback_data=f"detail_{movie['id']}"),
        InlineKeyboardButton(text="❤️ В избранное", callback_data=f"fav_{movie['id']}_{user_id}")
    ])

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🏠 Меню", callback_data="nav_main")
    ])

    # Формируем текст
    caption = (
        f"🤖 {hbold('AI-РЕКОМЕНДАЦИЯ')}\n\n"
        f"🎬 {hbold(movie['title'])} ({movie['year']})\n\n"
        f"⭐ {movie['rating_text']}\n"
        f"📽️ {movie['genres']}\n\n"
        f"📝 {movie['description'][:200]}...\n\n"
        f"{movie['reason']}"
    )

    if movie.get('poster_url'):
        try:
            await message.answer_photo(
                photo=movie['poster_url'],
                caption=caption,
                reply_markup=keyboard
            )
            return
        except:
            pass

    await message.answer(caption, reply_markup=keyboard)


@router.callback_query(F.data == "ai_prev")
async def ai_prev(callback: CallbackQuery):
    """Предыдущая рекомендация"""
    user_id = callback.from_user.id
    if user_id in recommendation_cache:
        # TODO: добавить логику переключения
        await callback.answer()
    await callback.answer()


@router.callback_query(F.data == "ai_next")
async def ai_next(callback: CallbackQuery):
    """Следующая рекомендация"""
    user_id = callback.from_user.id
    if user_id in recommendation_cache:
        # TODO: добавить логику переключения
        await callback.answer()
    await callback.answer()