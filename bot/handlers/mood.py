from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

from bot.services.tmdb_api import get_tmdb_client
from bot.keyboards.reply import get_main_keyboard

router = Router()

# Словарь для хранения временных результатов поиска
mood_cache = {}

MOOD_MAP = {
    "mood_comedy": {
        "name": "😂 КОМЕДИЯ",
        "emoji": "😂",
        "genres": [35],
        "description": "Самые смешные комедии для хорошего настроения"
    },
    "mood_drama": {
        "name": "😢 ДРАМА",
        "emoji": "😢",
        "genres": [18],
        "description": "Глубокие и трогательные драмы"
    },
    "mood_thriller": {
        "name": "😱 ТРИЛЛЕР",
        "emoji": "😱",
        "genres": [53, 80],
        "description": "Держащие в напряжении триллеры"
    },
    "mood_romance": {
        "name": "💕 РОМАНТИКА",
        "emoji": "💕",
        "genres": [10749],
        "description": "Романтические фильмы для особого вечера"
    },
    "mood_action": {
        "name": "💥 БОЕВИК",
        "emoji": "💥",
        "genres": [28, 12],
        "description": "Взрывные боевики и приключения"
    },
    "mood_family": {
        "name": "👪 СЕМЕЙНЫЙ",
        "emoji": "👪",
        "genres": [10751, 16],
        "description": "Фильмы для всей семьи"
    },
    "mood_horror": {
        "name": "👻 УЖАСЫ",
        "emoji": "👻",
        "genres": [27],
        "description": "Страшные и мистические фильмы"
    },
    "mood_sci_fi": {
        "name": "🤖 ФАНТАСТИКА",
        "emoji": "🤖",
        "genres": [878],
        "description": "Невероятные миры и технологии будущего"
    }
}


@router.message(F.text == "🎯 НАСТРОЕНИЕ")
@router.message(Command("mood"))
async def show_mood_menu(message: Message):
    """Показать меню выбора настроения/жанра"""
    text = (
        f"🎭 {hbold('ВЫБЕРИ НАСТРОЕНИЕ')}\n\n"
        f"{hitalic('Я подберу фильмы под твое состояние или любимый жанр')}\n\n"
        f"👇 Нажимай на кнопки ниже:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="😂 Комедия", callback_data="mood_comedy"),
            InlineKeyboardButton(text="😢 Драма", callback_data="mood_drama")
        ],
        [
            InlineKeyboardButton(text="😱 Триллер", callback_data="mood_thriller"),
            InlineKeyboardButton(text="💕 Романтика", callback_data="mood_romance")
        ],
        [
            InlineKeyboardButton(text="💥 Боевик", callback_data="mood_action"),
            InlineKeyboardButton(text="👪 Семейный", callback_data="mood_family")
        ],
        [
            InlineKeyboardButton(text="👻 Ужасы", callback_data="mood_horror"),
            InlineKeyboardButton(text="🤖 Фантастика", callback_data="mood_sci_fi")
        ],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="nav_main")]
    ])

    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("mood_"))
async def process_mood(callback: CallbackQuery):
    """Обработка выбора настроения"""
    mood_key = callback.data
    mood_data = MOOD_MAP.get(mood_key)
    user_id = callback.from_user.id

    if not mood_data:
        await callback.answer("Ошибка", show_alert=True)
        return

    # Показываем сообщение о поиске
    await callback.message.edit_text(
        f"{mood_data['emoji']} {hbold(mood_data['name'])}\n\n"
        f"{hitalic('Ищем лучшие фильмы...')} ⏳"
    )

    try:
        client = await get_tmdb_client()
        genre_id = mood_data['genres'][0]
        result = await client.discover_movies(genre_id=genre_id)

        if not result or not result.get("results"):
            await callback.message.edit_text(
                f"{mood_data['emoji']} {hbold(mood_data['name'])}\n\n"
                f"😢 Не удалось найти фильмы. Попробуй позже.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад к жанрам", callback_data="nav_back")]
                ])
            )
            await callback.answer()
            return

        # Берём все результаты и перемешиваем
        all_movies = result["results"]
        random.shuffle(all_movies)

        # Сохраняем в кэш
        mood_cache[user_id] = {
            "mood": mood_key,
            "all_movies": all_movies,
            "page": 0  # страница 0 = первые 5 фильмов
        }

        await show_movies_page(callback.message, user_id, mood_data, page=0)

    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="nav_back")]
            ])
        )
    await callback.answer()


async def show_movies_page(message: Message, user_id: int, mood_data: dict, page: int):
    """Показать страницу с фильмами"""
    if user_id not in mood_cache:
        return

    cache = mood_cache[user_id]
    all_movies = cache["all_movies"]
    start_idx = page * 5
    end_idx = start_idx + 5
    movies_to_show = all_movies[start_idx:end_idx]

    if not movies_to_show:
        # Если фильмы кончились, показываем первую страницу
        page = 0
        movies_to_show = all_movies[:5]
        cache["page"] = 0

    text = (
        f"{mood_data['emoji']} {hbold(mood_data['name'])}\n\n"
        f"📝 {mood_data['description']}\n\n"
        f"{hbold('РЕКОМЕНДУЮ:')}\n\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for i, movie in enumerate(movies_to_show, start_idx + 1):
        title = movie.get('title', 'Без названия')
        year = movie.get('release_date', '')[:4] if movie.get('release_date') else 'Неизвестно'
        rating = movie.get('vote_average', 0)

        text += f"{i}. {hbold(title)} ({year}) - ⭐ {rating:.1f}/10\n"
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"🎬 {i}. {title[:30]}...",
                callback_data=f"detail_{movie['id']}"
            )
        ])

    text += f"\n🎯 Настроение: {mood_data['name']}"

    # Кнопки навигации
    nav_buttons = []

    # Кнопка "Другие" (следующая страница)
    nav_buttons.append(InlineKeyboardButton(
        text="🎲 Другие",
        callback_data=f"mood_page_{page + 1}"
    ))

    nav_buttons.append(InlineKeyboardButton(
        text="🏠 Меню",
        callback_data="nav_main"
    ))

    keyboard.inline_keyboard.append(nav_buttons)

    # Сохраняем текущую страницу
    cache["page"] = page

    # Отправляем или редактируем сообщение
    if message.caption:  # если это фото с подписью
        await message.edit_caption(caption=text, reply_markup=keyboard)
    else:  # если это обычный текст
        await message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("mood_page_"))
async def mood_page(callback: CallbackQuery):
    """Переключение страницы с фильмами"""
    try:
        page = int(callback.data.replace("mood_page_", ""))
    except:
        page = 0

    user_id = callback.from_user.id

    if user_id not in mood_cache:
        await callback.answer("Поиск устарел, начни заново", show_alert=True)
        return

    cache = mood_cache[user_id]
    mood_data = MOOD_MAP.get(cache["mood"])

    await show_movies_page(callback.message, user_id, mood_data, page)
    await callback.answer()


# Функция для возврата к результатам настроения (для навигации)
async def show_mood_results(message: Message, user_id: int):
    """Показать сохраненные результаты настроения"""
    if user_id not in mood_cache:
        await show_mood_menu(message)
        return

    cache = mood_cache[user_id]
    mood_data = MOOD_MAP.get(cache["mood"])
    if not mood_data:
        await show_mood_menu(message)
        return

    await show_movies_page(message, user_id, mood_data, cache["page"])