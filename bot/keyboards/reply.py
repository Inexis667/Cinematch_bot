from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


# ========== ГЛАВНОЕ МЕНЮ (Reply Keyboard) ==========
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню с кнопками"""
    builder = ReplyKeyboardBuilder()

    # Первый ряд
    builder.row(
        KeyboardButton(text="🎲 Случайный фильм"),
        KeyboardButton(text="🔍 Поиск")
    )

    # Второй ряд
    builder.row(
        KeyboardButton(text="❤️ Избранное"),
        KeyboardButton(text="📊 Профиль")
    )

    # Третий ряд
    builder.row(
        KeyboardButton(text="🎯 По настроению"),
        KeyboardButton(text="❓ Помощь")
    )

    return builder.as_markup(resize_keyboard=True)  # Кнопки подгоняются под размер


# ========== ПОИСК ПО НАСТРОЕНИЮ (Inline Keyboard) ==========
def get_mood_keyboard() -> InlineKeyboardMarkup:
    """Кнопки для выбора настроения"""
    builder = InlineKeyboardBuilder()

    moods = [
        ("😂 Посмеяться", "mood_comedy"),
        ("😢 Погрустить", "mood_drama"),
        ("😱 Напряжение", "mood_thriller"),
        ("💕 Для двоих", "mood_romance"),
        ("🍿 Для компании", "mood_group"),
        ("🎄 Семейный", "mood_family"),
        ("🔥 Боевик", "mood_action"),
        ("🤔 Задуматься", "mood_philosophy")
    ]

    # Создаем кнопки в 2 столбца
    for text, callback in moods:
        builder.button(text=text, callback_data=callback)

    builder.adjust(2)  # По 2 кнопки в ряд
    return builder.as_markup()


# ========== КНОПКИ ДЛЯ КАРТОЧКИ ФИЛЬМА ==========
def get_movie_actions_keyboard(movie_id: int, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """Кнопки под карточкой фильма"""
    builder = InlineKeyboardBuilder()

    # Первый ряд
    builder.row(
        InlineKeyboardButton(text="📋 Подробнее", callback_data=f"detail_{movie_id}"),
        InlineKeyboardButton(text="🎬 Трейлер", callback_data=f"trailer_{movie_id}")
    )

    # Второй ряд
    builder.row(
        InlineKeyboardButton(text="❤️ В избранное" if not is_favorite else "❌ Из избранного",
                             callback_data=f"fav_{movie_id}"),
        InlineKeyboardButton(text="🔍 Похожие", callback_data=f"similar_{movie_id}")
    )

    return builder.as_markup()


# ========== КНОПКИ ДЛЯ ИЗБРАННОГО ==========
def get_folders_keyboard() -> InlineKeyboardMarkup:
    """Папки для сохранения фильмов"""
    builder = InlineKeyboardBuilder()

    folders = [
        ("📁 Избранное", "folder_favorites"),
        ("🍿 Посмотреть позже", "folder_watchlist"),
        ("🏆 Любимое", "folder_top"),
        ("👥 С друзьями", "folder_friends"),
        ("➕ Новая папка", "new_folder")
    ]

    for text, callback in folders:
        builder.button(text=text, callback_data=callback)

    builder.adjust(2, 2, 1)  # 2,2,1 ряд
    return builder.as_markup()


# ========== КНОПКИ НАВИГАЦИИ ==========
def get_navigation_keyboard() -> InlineKeyboardMarkup:
    """Кнопки навигации"""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="nav_back"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="nav_main")
    )

    return builder.as_markup()