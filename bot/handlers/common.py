from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.markdown import hbold
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.tmdb_api import get_tmdb_client
from bot.database.db import (
    add_to_favorites, remove_from_favorites,
    get_favorites, get_movie, add_favorite_experience,
    add_experience  # ← ДОБАВЛЕНО для опыта за детали
)
from bot.keyboards.reply import get_main_keyboard, get_folders_keyboard

router = Router()


@router.callback_query(F.data.startswith("detail_"))
async def movie_details(callback: CallbackQuery):
    """Детали фильма"""
    movie_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    await add_experience(user_id, 1)

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

        if callback.message.caption is not None:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(text, reply_markup=keyboard)

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
            await add_favorite_experience(user_id)
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


@router.callback_query(F.data.startswith("similar_"))
async def similar_movies(callback: CallbackQuery):
    """Показать похожие фильмы (или того же жанра) и сразу перейти к первому"""
    movie_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    await callback.message.bot.send_chat_action(
        callback.message.chat.id, action="typing"
    )

    try:
        client = await get_tmdb_client()
        movie_data = await client.get_movie_details(movie_id)

        if not movie_data:
            await callback.answer("Не удалось загрузить информацию о фильме", show_alert=True)
            return

        # Пробуем получить официальные похожие
        similar = movie_data.get('similar', {}).get('results', [])

        # Если нет похожих — берём фильмы того же жанра
        if not similar and movie_data.get('genres'):
            # Берём первый жанр
            genre_id = movie_data['genres'][0]['id']
            discover = await client.discover_movies(genre_id=genre_id, page=1)
            similar = discover.get('results', [])[:10]

            # Убираем текущий фильм из списка
            similar = [m for m in similar if m['id'] != movie_id]

        if not similar:
            await callback.answer("Не удалось найти похожие фильмы", show_alert=True)
            return

        # Если есть похожие фильмы, сразу показываем первый
        first_similar = similar[0]

        # Получаем детальную информацию о первом похожем фильме
        similar_details = await client.get_movie_details(first_similar['id'])

        if similar_details:
            formatted = client.format_movie_for_display(similar_details)

            # Создаём клавиатуру для этого фильма
            keyboard = InlineKeyboardMarkup(inline_keyboard=[])

            # Кнопки
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="📖 Подробнее", callback_data=f"detail_{formatted['id']}"),
                InlineKeyboardButton(text="🔍 Похожие", callback_data=f"similar_{formatted['id']}")
            ])
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="🏠 Меню", callback_data="nav_main")
            ])

            # Формируем текст
            text = (
                f"🎬 {hbold(formatted['title'])} ({formatted['year']})\n\n"
                f"⭐ {formatted['rating_text']}\n"
                f"📌 {formatted['genres']}\n\n"
                f"📝 {formatted['description'][:300]}..."
            )

            # Отправляем новое сообщение с постером
            if formatted['poster_url']:
                await callback.message.answer_photo(
                    photo=formatted['poster_url'],
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await callback.message.answer(text, reply_markup=keyboard)
        else:
            await callback.answer("Не удалось загрузить детали похожего фильма", show_alert=True)

    except Exception as e:
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)

    await callback.answer()


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

    from bot.handlers.search import search_cache, show_search_result
    from bot.handlers.favorites import favorites_cache, show_favorite
    from bot.handlers.mood import mood_cache, show_mood_results

    if user_id in search_cache:
        data = search_cache[user_id]
        try:
            await callback.message.delete()
        except:
            pass
        await show_search_result(callback.message, user_id, data["current"])
        await callback.answer()
        return

    if user_id in favorites_cache:
        data = favorites_cache[user_id]
        try:
            await callback.message.delete()
        except:
            pass
        await show_favorite(callback.message, user_id, data["current"])
        await callback.answer()
        return

    if user_id in mood_cache:
        try:
            await callback.message.delete()
        except:
            pass
        from bot.handlers.mood import show_mood_results
        await show_mood_results(callback.message, user_id)
        await callback.answer()
        return

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

