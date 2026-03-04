from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


# ========== ГЛАВНОЕ МЕНЮ ==========
def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Главное меню с красивыми кнопками
    Возвращает клавиатуру, которая всегда снизу
    """
    builder = ReplyKeyboardBuilder()

    # Верхний ряд - основные функции
    builder.row(
        KeyboardButton(text="🎲 РУЛЕТКА"),
        KeyboardButton(text="🔍 ПОИСК")
    )

    # Средний ряд - коллекции
    builder.row(
        KeyboardButton(text="❤️ МОЁ"),
        KeyboardButton(text="📊 ПРОФИЛЬ")
    )

    # Нижний ряд - дополнительные функции
    builder.row(
        KeyboardButton(text="🎯 НАСТРОЕНИЕ"),
        KeyboardButton(text="❓ ПОМОЩЬ")
    )

    return builder.as_markup(
        resize_keyboard=True,  # Кнопки подгоняются под размер
        input_field_placeholder="👇 Нажми на кнопку..."  # Подсказка в поле ввода
    )


# ========== МЕНЮ НАСТРОЕНИЙ ==========
def get_mood_keyboard() -> InlineKeyboardMarkup:
    """
    Красивое меню выбора настроения
    """
    builder = InlineKeyboardBuilder()

    moods = [
        ("😂 Смех", "mood_comedy", "🎭"),
        ("😢 Грусть", "mood_drama", "💧"),
        ("😱 Адреналин", "mood_thriller", "⚡"),
        ("💕 Романтика", "mood_romance", "🌸"),
        ("👥 Компания", "mood_group", "🍕"),
        ("👪 Семья", "mood_family", "🏡"),
        ("💪 Экшен", "mood_action", "💥"),
        ("🤔 Мысли", "mood_philosophy", "🧠")
    ]

    for text, callback, emoji in moods:
        builder.button(
            text=f"{emoji} {text}",
            callback_data=callback
        )

    builder.adjust(2)  # По 2 кнопки в ряд
    return builder.as_markup()


# ========== КНОПКИ ДЛЯ ФИЛЬМА ==========
def get_movie_actions_keyboard(movie_id: int, is_favorite: bool = False) -> InlineKeyboardMarkup:
    """
    Кнопки под карточкой фильма
    """
    builder = InlineKeyboardBuilder()

    # Верхний ряд - информация
    builder.row(
        InlineKeyboardButton(
            text="📖 Подробнее",
            callback_data=f"detail_{movie_id}"
        ),
        InlineKeyboardButton(
            text="🎬 Трейлер",
            callback_data=f"trailer_{movie_id}",
            url="https://youtube.com"  # Заглушка
        )
    )

    # Средний ряд - действия
    fav_text = "❤️ В избранное" if not is_favorite else "❌ Удалить"
    builder.row(
        InlineKeyboardButton(
            text=fav_text,
            callback_data=f"fav_{movie_id}"
        ),
        InlineKeyboardButton(
            text="🔍 Похожие",
            callback_data=f"similar_{movie_id}"
        )
    )

    # Нижний ряд - навигация
    builder.row(
        InlineKeyboardButton(
            text="🏠 Меню",
            callback_data="nav_main"
        )
    )

    return builder.as_markup()


# ========== ПАПКИ ИЗБРАННОГО ==========
def get_folders_keyboard() -> InlineKeyboardMarkup:
    """
    Красивые папки для коллекций
    """
    builder = InlineKeyboardBuilder()

    folders = [
        ("⭐ Избранное", "folder_favorites"),
        ("📋 К просмотру", "folder_watchlist"),
        ("🏆 Шедевры", "folder_top"),
        ("👥 С друзьями", "folder_friends")
    ]

    for text, callback in folders:
        builder.button(
            text=f"📁 {text}",
            callback_data=callback
        )

    builder.row(
        InlineKeyboardButton(
            text="➕ Создать папку",
            callback_data="new_folder"
        )
    )

    return builder.as_markup()


# ========== НАВИГАЦИЯ ==========
def get_navigation_keyboard(show_back: bool = True, show_main: bool = True) -> InlineKeyboardMarkup:
    """
    Кнопки навигации
    """
    builder = InlineKeyboardBuilder()
    buttons = []

    if show_back:
        buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data="nav_back"
            )
        )

    if show_main:
        buttons.append(
            InlineKeyboardButton(
                text="🏠 Главная",
                callback_data="nav_main"
            )
        )

    builder.row(*buttons)
    return builder.as_markup()


# ========== КНОПКИ ДЛЯ ПАГИНАЦИИ ==========
def get_pagination_keyboard(current: int, total: int, prefix: str, user_id: int) -> InlineKeyboardMarkup:
    """
    Красивая навигация по страницам
    """
    builder = InlineKeyboardBuilder()
    buttons = []

    if current > 1:
        buttons.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"{prefix}_prev_{user_id}_{current}"
            )
        )

    buttons.append(
        InlineKeyboardButton(
            text=f"📄 {current}/{total}",
            callback_data="noop"
        )
    )

    if current < total:
        buttons.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"{prefix}_next_{user_id}_{current}"
            )
        )

    builder.row(*buttons)
    return builder.as_markup()