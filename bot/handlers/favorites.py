from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

from bot.database.db import (
    get_favorites, remove_from_favorites, add_to_favorites,
    add_favorite_experience, get_movie
)
from bot.keyboards.reply import get_main_keyboard

router = Router()
favorites_cache = {}


@router.message(F.text == "❤️ МОЁ")
@router.message(Command("favorites"))
async def show_favorites(message: Message):
    """Показать избранное"""
    user_id = message.from_user.id
    favorites = await get_favorites(user_id)

    if not favorites:
        await message.answer(
            f"📁 {hbold('ИЗБРАННОЕ')}\n\n"
            f"😢 {hitalic('Здесь пока пусто...')}\n\n"
            f"💡 Найди фильм через 🔍 ПОИСК или 🎲 РУЛЕТКУ",
            reply_markup=get_main_keyboard()
        )
        return

    favorites_cache[user_id] = {
        "results": favorites,
        "current": 0,
        "total": len(favorites)
    }

    await show_favorite(message, user_id, 0)


async def show_favorite(message: Message, user_id: int, index: int):
    """Показать один фильм из избранного"""
    if user_id not in favorites_cache:
        return

    data = favorites_cache[user_id]
    movie = data["results"][index]
    current = index + 1
    total = data["total"]

    # Клавиатура
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Навигация
    nav_buttons = []
    if current > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data="fav_prev"))
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {current}/{total}", callback_data="noop"))
    if current < total:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data="fav_next"))
    keyboard.inline_keyboard.append(nav_buttons)

    # Кнопки
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="📖 Подробнее", callback_data=f"detail_{movie['tmdb_id']}"),
        InlineKeyboardButton(text="❌ Удалить", callback_data=f"fav_{movie['tmdb_id']}")
    ])

    # Кнопка похожих
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🔍 Похожие", callback_data=f"similar_{movie['tmdb_id']}")
    ])

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🏠 Меню", callback_data="nav_main")
    ])

    # Жанры
    try:
        genres = json.loads(movie['genres']) if movie['genres'] else []
    except:
        genres = []

    genre_map = {
        28: "Боевик", 12: "Приключения", 35: "Комедия", 18: "Драма",
        27: "Ужасы", 10749: "Мелодрама", 878: "Фантастика", 53: "Триллер"
    }
    genre_names = [genre_map.get(g, str(g)) for g in genres[:3]]
    genre_text = ", ".join(genre_names) if genre_names else "Неизвестно"

    description = movie['description']
    if len(description) > 300:
        description = description[:300] + "..."

    caption = (
        f"❤️ {hbold('ИЗБРАННОЕ')} ❤️\n\n"
        f"🎬 {hbold(movie['title'])} ({movie['release_year']})\n\n"
        f"⭐ {hbold('Рейтинг:')} {movie['rating']}/10\n"
        f"📽️ {genre_text}\n\n"
        f"📝 {description}"
    )

    if movie.get('poster_path'):
        poster_url = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
        try:
            await message.answer_photo(poster_url, caption, reply_markup=keyboard)
            return
        except:
            pass

    await message.answer(caption, reply_markup=keyboard)


@router.callback_query(F.data == "fav_prev")
async def fav_prev(callback: CallbackQuery):
    """Предыдущий"""
    user_id = callback.from_user.id
    if user_id in favorites_cache:
        data = favorites_cache[user_id]
        new_index = data["current"] - 1
        if new_index >= 0:
            data["current"] = new_index
            try:
                await callback.message.delete()
            except:
                pass
            await show_favorite(callback.message, user_id, new_index)
    await callback.answer()


@router.callback_query(F.data == "fav_next")
async def fav_next(callback: CallbackQuery):
    """Следующий"""
    user_id = callback.from_user.id
    if user_id in favorites_cache:
        data = favorites_cache[user_id]
        new_index = data["current"] + 1
        if new_index < data["total"]:
            data["current"] = new_index
            try:
                await callback.message.delete()
            except:
                pass
            await show_favorite(callback.message, user_id, new_index)
    await callback.answer()


@router.callback_query(F.data.startswith("fav_") & ~F.data.startswith("fav_prev") & ~F.data.startswith("fav_next"))
async def toggle_favorite(callback: CallbackQuery):
    """Добавить/удалить из избранного"""
    try:
        movie_id = int(callback.data.split("_")[1])
        user_id = callback.from_user.id

        movie = await get_movie(movie_id)
        if not movie:
            await callback.answer("Фильм не найден", show_alert=True)
            return

        favorites = await get_favorites(user_id)
        is_favorite = any(str(fav.get('tmdb_id')) == str(movie_id) for fav in favorites)

        if is_favorite:
            await remove_from_favorites(user_id, movie_id)
            await callback.answer("❌ Удалено из избранного")

            # ОБНОВЛЯЕМ КЭШ ПОСЛЕ УДАЛЕНИЯ
            new_favorites = await get_favorites(user_id)
            if new_favorites:
                favorites_cache[user_id] = {
                    "results": new_favorites,
                    "current": 0,
                    "total": len(new_favorites)
                }
                # Удаляем старое сообщение и показываем первый фильм
                try:
                    await callback.message.delete()
                except:
                    pass
                await show_favorite(callback.message, user_id, 0)
            else:
                # Если избранное пусто
                favorites_cache.pop(user_id, None)
                try:
                    await callback.message.delete()
                except:
                    pass
                await callback.message.answer(
                    f"📁 {hbold('ИЗБРАННОЕ')}\n\n"
                    f"😢 {hitalic('Здесь пока пусто...')}\n\n"
                    f"💡 Найди фильм через 🔍 ПОИСК или 🎲 РУЛЕТКУ",
                    reply_markup=get_main_keyboard()
                )
        else:
            await add_to_favorites(user_id, movie_id)
            await add_favorite_experience(user_id)
            await callback.answer("❤️ Добавлено в избранное")

            # Обновляем кэш
            new_favorites = await get_favorites(user_id)
            favorites_cache[user_id] = {
                "results": new_favorites,
                "current": 0,
                "total": len(new_favorites)
            }

    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)