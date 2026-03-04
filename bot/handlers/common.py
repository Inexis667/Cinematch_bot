"""
🔄 Общие обработчики (детали, навигация)
KinoBot by Inexis
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.markdown import hbold
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.tmdb_api import get_tmdb_client
from bot.database.db import (
    add_to_favorites, remove_from_favorites,
    get_favorites, get_movie, add_favorite_experience
)
from bot.keyboards.reply import get_main_keyboard, get_folders_keyboard

router = Router()


@router.callback_query(F.data.startswith("detail_"))
async def movie_details(callback: CallbackQuery):
    """Детали фильма"""
    movie_id = int(callback.data.split("_")[1])

    try:
        client = await get_tmdb_client()
        movie_data = await client.get_movie_details(movie_id)

        if not movie_data:
            await callback.answer("Ошибка", show_alert=True)
            return

        formatted = client.format_movie_for_display(movie_data)

        # Клавиатура
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        if formatted['trailer_key']:
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text="🎬 Трейлер",
                    url=f"https://youtu.be/{formatted['trailer_key']}"
                )
            ])

        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="◀️ Назад", callback_data="nav_back"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="nav_main")
        ])

        text = (
            f"🎬 {hbold(formatted['title'])} ({formatted['year']})\n\n"
            f"⭐ {formatted['rating_text']}\n"
            f"📌 {formatted['genres']}\n"
            f"🎬 {hbold('Режиссёр:')} {formatted['director']}\n"
            f"👥 {hbold('В ролях:')} {formatted['cast'][:100]}...\n\n"
            f"📝 {formatted['description']}"
        )

        await callback.message.edit_caption(caption=text, reply_markup=keyboard)

    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

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
            await callback.answer("❌ Удалено")
        else:
            await add_to_favorites(user_id, movie_id)
            await add_favorite_experience(user_id)  # ← СТРОКА ДОБАВЛЕНА
            await callback.answer("❤️ Добавлено")

        # Обновляем кнопку
        try:
            if callback.message.reply_markup:
                keyboard = callback.message.reply_markup
                for row in keyboard.inline_keyboard:
                    for button in row:
                        if button.callback_data and button.callback_data.startswith("fav_"):
                            button.text = "❤️ В избранное" if is_favorite else "❌ Удалить"
                await callback.message.edit_reply_markup(reply_markup=keyboard)
        except:
            pass

    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data == "nav_main")
async def go_to_main(callback: CallbackQuery):
    """В главное меню"""
    await callback.message.delete()
    await callback.message.answer("🏠 Главное меню:", reply_markup=get_main_keyboard())
    await callback.answer()


@router.callback_query(F.data == "nav_back")
async def go_back(callback: CallbackQuery):
    """Умный возврат назад - СНАЧАЛА ПОИСК, ПОТОМ ИЗБРАННОЕ"""
    user_id = callback.from_user.id

    # Импортируем кэши здесь, чтобы избежать циклических импортов
    from bot.handlers.search import search_cache, show_search_result
    from bot.handlers.favorites import favorites_cache, show_favorite
    from bot.handlers.mood import mood_cache, show_mood_results

    # 🔍 1️⃣ СНАЧАЛА ПРОВЕРЯЕМ ПОИСК
    if user_id in search_cache:
        data = search_cache[user_id]
        try:
            await callback.message.delete()
        except:
            pass
        await show_search_result(callback.message, user_id, data["current"])
        await callback.answer()
        return

    # ❤️ 2️⃣ ПОТОМ ИЗБРАННОЕ
    if user_id in favorites_cache:
        data = favorites_cache[user_id]
        try:
            await callback.message.delete()
        except:
            pass
        await show_favorite(callback.message, user_id, data["current"])
        await callback.answer()
        return

    # 🎯 3️⃣ ПОТОМ НАСТРОЕНИЕ
    if user_id in mood_cache:
        try:
            await callback.message.delete()
        except:
            pass
        await show_mood_results(callback.message, user_id)
        await callback.answer()
        return

    # 🏠 4️⃣ И ТОЛЬКО ПОТОМ МЕНЮ
    try:
        await callback.message.delete()
    except:
        pass
    await callback.message.answer(
        "🏠 Главное меню:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    """Заглушка"""
    await callback.answer()