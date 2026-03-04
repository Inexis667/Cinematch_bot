from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

from bot.services.tmdb_api import get_tmdb_client
from bot.keyboards.reply import get_main_keyboard, get_mood_keyboard

router = Router()

# Кэш для результатов поиска по настроению
mood_cache = {}

# Соответствие настроения жанрам
MOOD_MAP = {
    "mood_comedy": {
        "name": "😂 ПОСМЕЯТЬСЯ",
        "emoji": "😂",
        "genres": [35],  # Комедия
        "description": "Самые смешные комедии для хорошего настроения"
    },
    "mood_drama": {
        "name": "😢 ПОГРУСТИТЬ",
        "emoji": "😢",
        "genres": [18],  # Драма
        "description": "Глубокие и трогательные драмы"
    },
    "mood_thriller": {
        "name": "😱 НАПРЯЖЕНИЕ",
        "emoji": "😱",
        "genres": [53, 80],  # Триллер, Криминал
        "description": "Держащие в напряжении триллеры"
    },
    "mood_romance": {
        "name": "💕 ДЛЯ ДВОИХ",
        "emoji": "💕",
        "genres": [10749],  # Мелодрама
        "description": "Романтические фильмы для особого вечера"
    },
    "mood_action": {
        "name": "💥 ЭКШЕН",
        "emoji": "💥",
        "genres": [28, 12],  # Боевик, Приключения
        "description": "Взрывные боевики и приключения"
    },
    "mood_family": {
        "name": "👪 СЕМЕЙНЫЙ",
        "emoji": "👪",
        "genres": [10751, 16],  # Семейный, Мультфильм
        "description": "Фильмы для всей семьи"
    },
    "mood_philosophy": {
        "name": "🤔 ЗАДУМАТЬСЯ",
        "emoji": "🤔",
        "genres": [18, 9648],  # Драма, Детектив
        "description": "Глубокие фильмы для размышлений"
    },
    "mood_horror": {
        "name": "👻 УЖАСЫ",
        "emoji": "👻",
        "genres": [27],  # Ужасы
        "description": "Страшные и мистические фильмы"
    }
}


@router.message(F.text == "🎯 НАСТРОЕНИЕ")
@router.message(Command("mood"))
async def show_mood_menu(message: Message):
    """Показать меню выбора настроения"""
    text = (
        f"🎯 {hbold('ВЫБЕРИ НАСТРОЕНИЕ')}\n\n"
        f"{hitalic('Я подберу фильмы под твое состояние')}\n\n"
        f"👇 Нажимай на кнопки ниже:"
    )

    await message.answer(text, reply_markup=get_mood_keyboard())


@router.callback_query(F.data.startswith("mood_"))
async def process_mood(callback: CallbackQuery):
    """Обработка выбора настроения"""
    mood_key = callback.data
    mood_data = MOOD_MAP.get(mood_key)
    user_id = callback.from_user.id

    if not mood_data:
        await callback.answer("Ошибка", show_alert=True)
        return

    # Отправляем сообщение о поиске
    await callback.message.edit_text(
        f"{mood_data['emoji']} {hbold(mood_data['name'])}\n\n"
        f"{hitalic('Ищем лучшие фильмы...')} ⏳"
    )

    try:
        # Ищем фильмы по жанрам
        client = await get_tmdb_client()

        # Берем первый жанр из списка для поиска
        genre_id = mood_data['genres'][0]

        # Поиск по жанру
        result = await client.discover_movies(genre_id)

        if not result or not result.get("results"):
            await callback.message.edit_text(
                f"{mood_data['emoji']} {hbold(mood_data['name'])}\n\n"
                f"😢 Не удалось найти фильмы. Попробуй позже.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="nav_back")]
                ])
            )
            await callback.answer()
            return

        # Выбираем случайные 5 фильмов
        movies = result["results"][:10]
        random.shuffle(movies)
        movies = movies[:5]

        # 🔥 СОХРАНЯЕМ В КЭШ ДЛЯ ВОЗВРАТА 🔥
        mood_cache[user_id] = {
            "mood": mood_key,
            "results": movies,
            "total": len(movies),
            "page": 1
        }

        # Формируем результат
        text = (
            f"{mood_data['emoji']} {hbold(mood_data['name'])}\n\n"
            f"📝 {mood_data['description']}\n\n"
            f"{hbold('РЕКОМЕНДУЮ:')}\n\n"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        for i, movie in enumerate(movies, 1):
            title = movie.get('title', 'Без названия')
            year = movie.get('release_date', '')[:4] if movie.get('release_date') else 'Неизвестно'
            rating = movie.get('vote_average', 0)

            text += f"{i}. {hbold(title)} ({year}) - ⭐ {rating}/10\n"

            # Добавляем кнопку для каждого фильма
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"🎬 {i}. {title[:30]}...",
                    callback_data=f"detail_{movie['id']}"
                )
            ])

        text += f"\n🎯 Настроение: {mood_data['name']}"

        # Добавляем кнопки навигации
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🎲 Другие", callback_data=f"mood_more_{mood_key}"),
            InlineKeyboardButton(text="🏠 Меню", callback_data="nav_main")
        ])

        await callback.message.edit_text(text, reply_markup=keyboard)

    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="nav_back")]
            ])
        )

    await callback.answer()


@router.callback_query(F.data.startswith("mood_more_"))
async def more_mood_movies(callback: CallbackQuery):
    """Показать еще фильмы по настроению"""
    mood_key = callback.data.replace("mood_more_", "")
    await process_mood(callback)


# Функция для показа результатов настроения (для навигации)
async def show_mood_results(message: Message, user_id: int):
    """Показать сохраненные результаты настроения"""
    if user_id not in mood_cache:
        await message.answer(
            "🎯 Выбери настроение:",
            reply_markup=get_mood_keyboard()
        )
        return

    data = mood_cache[user_id]
    mood_data = MOOD_MAP.get(data["mood"])
    movies = data["results"]

    if not mood_data or not movies:
        await message.answer(
            "🎯 Выбери настроение:",
            reply_markup=get_mood_keyboard()
        )
        return

    text = (
        f"{mood_data['emoji']} {hbold(mood_data['name'])}\n\n"
        f"📝 {mood_data['description']}\n\n"
        f"{hbold('РЕКОМЕНДУЮ:')}\n\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for i, movie in enumerate(movies, 1):
        title = movie.get('title', 'Без названия')
        year = movie.get('release_date', '')[:4] if movie.get('release_date') else 'Неизвестно'
        rating = movie.get('vote_average', 0)

        text += f"{i}. {hbold(title)} ({year}) - ⭐ {rating}/10\n"

        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🎬 {i}. {title[:30]}...",
                callback_data=f"detail_{movie['id']}"
            )
        ])

    text += f"\n🎯 Настроение: {mood_data['name']}"

    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="🎲 Другие", callback_data=f"mood_more_{data['mood']}"),
        InlineKeyboardButton(text="🏠 Меню", callback_data="nav_main")
    ])

    await message.answer(text, reply_markup=keyboard)