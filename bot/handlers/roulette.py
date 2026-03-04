from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio
import random
import json

from bot.services.tmdb_api import get_tmdb_client
from bot.database.db import save_movie, get_favorites
from bot.keyboards.reply import get_main_keyboard

router = Router()


@router.message(F.text == "🎲 РУЛЕТКА")
@router.message(Command("random"))
async def cmd_random(message: Message):
    """Случайный фильм"""
    # Эффект рулетки
    msg = await message.answer("🎲 Крутим барабан... ⏳")
    await asyncio.sleep(1)
    await msg.delete()

    await message.bot.send_chat_action(message.chat.id, action="typing")

    try:
        client = await get_tmdb_client()

        # Получаем популярные фильмы с РАЗНЫХ страниц
        page = random.randint(1, 5)  # Случайная страница
        popular = await client.get_popular_movies(page)

        if not popular or not popular.get("results"):
            # Если не получилось, берем поиск
            result = await client.search_movies("")
            movies = result.get("results", [])
        else:
            movies = popular["results"]

        if not movies:
            await message.answer("😢 Не удалось получить фильм", reply_markup=get_main_keyboard())
            return

        # ВЫБИРАЕМ ДЕЙСТВИТЕЛЬНО СЛУЧАЙНЫЙ
        movie_data = random.choice(movies)

        # Получаем детали
        full_movie = await client.get_movie_details(movie_data["id"])
        if full_movie:
            movie_data = full_movie

        formatted = client.format_movie_for_display(movie_data)

        # Сохраняем
        movie_for_db = {
            'tmdb_id': formatted['id'],
            'title': formatted['title'],
            'original_title': movie_data.get('original_title', ''),
            'description': movie_data.get('overview', ''),
            'rating': formatted['rating'],
            'poster_path': movie_data.get('poster_path'),
            'release_year': formatted['year'] if formatted['year'] != "Неизвестно" else None,
            'genres': json.dumps([g['id'] for g in movie_data.get('genres', [])]) if movie_data.get('genres') else '[]'
        }
        await save_movie(movie_for_db)

        # Проверка избранного
        favorites = await get_favorites(message.from_user.id)
        is_favorite = any(str(fav.get('tmdb_id')) == str(formatted['id']) for fav in favorites)

        # Клавиатура
        fav_text = "❤️ В избранное" if not is_favorite else "❌ Удалить"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🎲 Ещё", callback_data="random_again"),
                InlineKeyboardButton(text=fav_text, callback_data=f"fav_{formatted['id']}")
            ],
            [InlineKeyboardButton(text="📖 Подробнее", callback_data=f"detail_{formatted['id']}")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="nav_main")]
        ])

        description = formatted['description']
        if len(description) > 300:
            description = description[:300] + "..."

        caption = (
            f"🎲 {hbold('КИНО-РУЛЕТКА')} 🎲\n\n"
            f"🎬 {hbold(formatted['title'])} ({formatted['year']})\n\n"
            f"⭐ {formatted['rating_text']}\n"
            f"📽️ {formatted['genres']}\n\n"
            f"📝 {description}"
        )

        if formatted['poster_url']:
            await message.answer_photo(formatted['poster_url'], caption, reply_markup=keyboard)
        else:
            await message.answer(caption, reply_markup=keyboard)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=get_main_keyboard())


@router.callback_query(F.data == "random_again")
async def random_again(callback: CallbackQuery):
    """Ещё раз"""
    await callback.message.delete()
    await cmd_random(callback.message)
    await callback.answer()