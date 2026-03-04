from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

from bot.database.db import get_user_stats, get_search_history, get_favorites
from bot.keyboards.reply import get_main_keyboard

router = Router()


@router.message(F.text == "📊 ПРОФИЛЬ")
@router.message(Command("profile"))
@router.message(Command("stats"))
async def show_profile(message: Message):
    """Показать профиль пользователя"""
    user = message.from_user
    user_id = user.id

    # Получаем статистику из БД
    stats = await get_user_stats(user_id)

    if not stats:
        await message.answer(
            "❌ Сначала запусти /start",
            reply_markup=get_main_keyboard()
        )
        return

    # Получаем историю поиска
    history = await get_search_history(user_id, limit=10)

    # Уровень и опыт
    level = stats['level']
    exp = stats['experience']
    next_level = level * 100
    exp_progress = int((exp / next_level) * 10) if next_level > 0 else 0
    progress_bar = "▓" * exp_progress + "░" * (10 - exp_progress)

    # Дата регистрации
    reg_date = stats['created_at']
    if reg_date:
        if isinstance(reg_date, str):
            reg_date = reg_date[:10]
        else:
            reg_date = reg_date.strftime("%d.%m.%Y")
    else:
        reg_date = "недавно"

    # Получаем избранное для анализа жанров
    favorites = await get_favorites(user_id)

    # Топ жанров
    genre_text = ""
    if favorites:
        genre_stats = await get_favorite_genres(favorites)
        if genre_stats:
            genre_text = "\n📈 {hbold('Любимые жанры:')}\n"
            for genre, count in genre_stats[:3]:
                genre_text += f"• {genre}: {count} 🎬\n"

    # Текст профиля
    profile_text = (
        f"👤 {hbold('ПРОФИЛЬ КИНОМАНА')} 👤\n\n"
        f"🎭 {hbold('Имя:')} {user.full_name}\n"
        f"📅 {hbold('В кино с:')} {reg_date}\n\n"
        f"📊 {hbold('ПРОГРЕСС:')}\n"
        f"Уровень {level} {progress_bar}\n"
        f"⭐ Опыт: {exp}/{next_level}\n\n"
        f"📌 {hbold('СТАТИСТИКА:')}\n"
        f"• В избранном: {stats['fav_count']} фильмов\n"
        f"• Поисков: {stats['search_count']}\n"
    )

    profile_text += genre_text

    # Достижения
    achievements = []
    if stats['fav_count'] >= 1:
        achievements.append("🏺 Коллекционер")
    if stats['fav_count'] >= 5:
        achievements.append("🎯 Знаток")
    if stats['search_count'] >= 10:
        achievements.append("🔍 Исследователь")
    if level >= 5:
        achievements.append("⭐ Киноман")
    if level >= 10:
        achievements.append("👑 Легенда")

    if achievements:
        profile_text += f"\n🏆 {hbold('ДОСТИЖЕНИЯ:')}\n"
        for ach in achievements:
            profile_text += f"• {ach}\n"

    # Подсказка для следующего уровня
    if level < 10:
        exp_needed = next_level - exp
        profile_text += f"\n✨ До {level + 1} уровня: {exp_needed} опыта"

    # Клавиатура
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 История поиска", callback_data="profile_history")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="nav_main")]
    ])

    await message.answer(profile_text, reply_markup=keyboard)


async def get_favorite_genres(favorites: list) -> list:
    """Анализ любимых жанров"""
    genre_map = {
        28: "Боевик", 12: "Приключения", 16: "Мультфильм", 35: "Комедия",
        80: "Криминал", 18: "Драма", 10751: "Семейный", 14: "Фэнтези",
        27: "Ужасы", 10402: "Музыка", 9648: "Детектив", 10749: "Мелодрама",
        878: "Фантастика", 53: "Триллер", 10752: "Военный", 37: "Вестерн"
    }

    genre_count = {}

    for movie in favorites:
        try:
            if isinstance(movie.get('genres'), str):
                genres = json.loads(movie['genres'])
            else:
                genres = movie.get('genres', [])

            for g in genres:
                genre_name = genre_map.get(g, f"Жанр {g}")
                genre_count[genre_name] = genre_count.get(genre_name, 0) + 1
        except:
            continue

    return sorted(genre_count.items(), key=lambda x: x[1], reverse=True)


@router.callback_query(F.data == "profile_history")
async def show_history(callback: CallbackQuery):
    """Показать историю поиска из БД"""
    user_id = callback.from_user.id
    history = await get_search_history(user_id, limit=10)

    if not history:
        await callback.message.edit_text(
            "📋 История поиска пуста",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="nav_back")]
            ])
        )
        await callback.answer()
        return

    text = f"📋 {hbold('ИСТОРИЯ ПОИСКА')}\n\n"

    for i, item in enumerate(history, 1):
        date = item['created_at']
        if isinstance(date, str):
            date = date[:10]
        else:
            date = date.strftime("%d.%m")
        text += f"{i}. {hbold(item['query'])} ({date})\n"

    text += "\n🔍 Нажимай кнопки и ищи!"

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="nav_back")]
        ])
    )
    await callback.answer()