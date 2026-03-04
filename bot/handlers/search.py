from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
import json

from bot.services.tmdb_api import get_tmdb_client
from bot.services.movie_service import search_movies_all
from bot.database.db import save_movie, get_favorites, add_search_history
from bot.keyboards.reply import get_main_keyboard

router = Router()
search_cache = {}  # Хранилище результатов поиска


@router.message(F.text == "🔍 ПОИСК")
@router.message(Command("search"))
async def cmd_search(message: Message):
    """Начинаем поиск"""
    text = (
        f"🔍 {hbold('ПОИСК ФИЛЬМОВ')}\n\n"
        f"📝 {hitalic('Напиши название:')}\n\n"
        f"• {hcode('Аватар')}\n"
        f"• {hcode('Inception')}\n"
        f"• {hcode('Ди Каприо')}"
    )
    await message.answer(text, reply_markup=get_main_keyboard())


@router.message(F.text & ~F.text.startswith("/") & ~F.text.startswith("🎲")
                & ~F.text.startswith("🔍") & ~F.text.startswith("❤️")
                & ~F.text.startswith("📊") & ~F.text.startswith("🎯")
                & ~F.text.startswith("❓"))
async def process_search(message: Message):
    """Поиск по названию (TMDb + Kinopoisk)"""
    query = message.text.strip()
    user_id = message.from_user.id

    if len(query) < 2:
        await message.answer("❌ Слишком короткое название", reply_markup=get_main_keyboard())
        return

    wait_msg = await message.answer(f"🔎 Ищу: {hbold(query)}...")

    try:
        # 🔥 Ищем ВЕЗДЕ (TMDb + Kinopoisk)
        results = await search_movies_all(query)

        # Безопасное удаление сообщения
        try:
            await wait_msg.delete()
        except:
            pass  # Если сообщение уже удалено - игнорируем

        if not results:
            await message.answer(
                f"😢 По запросу {hbold(query)} ничего не найдено.\n\n"
                f"Попробуй другое название или 🎲 РУЛЕТКА",
                reply_markup=get_main_keyboard()
            )
            return

        # Сохраняем результаты
        search_cache[user_id] = {
            "query": query,
            "results": results[:10],
            "current": 0,
            "total": min(10, len(results)),
            "total_all": len(results)
        }

        await show_search_result(message, user_id, 0)

    except Exception as e:
        await wait_msg.delete()
        await message.answer(f"❌ Ошибка: {str(e)}", reply_markup=get_main_keyboard())


async def show_search_result(message: Message, user_id: int, index: int):
    """Показать результат поиска"""
    if user_id not in search_cache:
        return

    data = search_cache[user_id]
    movie = data["results"][index]
    current = index + 1
    total = data["total"]

    client = await get_tmdb_client()
    formatted = client.format_movie_for_display(movie)

    # Проверка избранного
    favorites = await get_favorites(user_id)
    is_favorite = any(str(fav.get('tmdb_id')) == str(formatted['id']) for fav in favorites)

    # Сохраняем в БД
    try:
        movie_for_db = {
            'tmdb_id': formatted['id'],
            'title': formatted['title'],
            'original_title': movie.get('original_title', ''),
            'description': movie.get('overview', ''),
            'rating': formatted['rating'],
            'poster_path': movie.get('poster_path'),
            'release_year': formatted['year'] if formatted['year'] != "Неизвестно" else None,
            'genres': json.dumps([g['id'] for g in movie.get('genres', [])]) if movie.get('genres') else '[]'
        }
        await save_movie(movie_for_db)
    except:
        pass

    # Клавиатура
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Навигация
    nav_buttons = []
    if current > 1:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data="search_prev"))
    nav_buttons.append(InlineKeyboardButton(text=f"📄 {current}/{total}", callback_data="noop"))
    if current < total:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data="search_next"))
    keyboard.inline_keyboard.append(nav_buttons)

    # Кнопки
    fav_text = "❤️ В избранное" if not is_favorite else "❌ Удалить"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="📖 Подробнее", callback_data=f"detail_{formatted['id']}"),
        InlineKeyboardButton(text=fav_text, callback_data=f"fav_{formatted['id']}")
    ])

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🏠 Меню", callback_data="nav_main")
    ])

    if formatted['rating'] > 0:
        rating_text = f"⭐ {formatted['rating']:.1f}/10"
    else:
        rating_text = "⭐ Нет оценок"

    # Жанры
    genres_text = formatted['genres'] if formatted['genres'] != "Неизвестно" else "📽️ Жанры неизвестны"

    # Описание
    description = formatted['description']
    if not description or description == 'Описание отсутствует':
        description = '😢 Описание отсутствует'
    elif len(description) > 300:
        description = description[:300] + "..."

    source_emoji = "🎬" if movie.get('source') == 'tmdb' else "🎥"
    source_name = "TMDb" if movie.get('source') == 'tmdb' else "Kinopoisk"

    caption = (
        f"{source_emoji} {hbold(formatted['title'])} ({formatted['year']})\n"
        f"📌 {hitalic(f'Источник: {source_name}')}\n\n"
        f"{rating_text}\n"
        f"{genres_text}\n\n"
        f"📝 {description}"
    )
    poster_url = movie.get('poster') or formatted.get('poster_url')

    # Если нет постера - используем заглушку
    if not poster_url:
        poster_url = "https://via.placeholder.com/300x450?text=No+Poster"

    try:
        # Пробуем отправить с фото
        await message.answer_photo(poster_url, caption, reply_markup=keyboard)
    except:
        # Если фото не грузится - отправляем без фото
        await message.answer(caption, reply_markup=keyboard)


@router.callback_query(F.data == "search_prev")
async def search_prev(callback: CallbackQuery):
    """Предыдущий"""
    user_id = callback.from_user.id
    if user_id in search_cache:
        data = search_cache[user_id]
        new_index = data["current"] - 1
        if new_index >= 0:
            data["current"] = new_index
            try:
                await callback.message.delete()
            except:
                pass
            await show_search_result(callback.message, user_id, new_index)
            await callback.answer()


@router.callback_query(F.data == "search_next")
async def search_next(callback: CallbackQuery):
    """Следующий"""
    user_id = callback.from_user.id
    if user_id in search_cache:
        data = search_cache[user_id]
        new_index = data["current"] + 1
        if new_index < data["total"]:
            data["current"] = new_index
            try:
                await callback.message.delete()
            except:
                pass
            await show_search_result(callback.message, user_id, new_index)
            await callback.answer()