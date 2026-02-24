from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold

from bot.database.db import get_user, create_user
from bot.keyboards.reply import (
    get_main_keyboard,
    get_mood_keyboard,
    get_movie_actions_keyboard,
    get_folders_keyboard,  # ← Этого не хватало!
    get_navigation_keyboard
)

router = Router()


# ========== ОБРАБОТКА КОМАНДЫ /start ==========
@router.message(Command("start"))
async def cmd_start(message: Message):
    user = message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name or "друг"

    db_user = await get_user(user_id)

    if not db_user:
        await create_user(user_id, username, first_name)
        welcome_text = (
            f"👋 {hbold(f'Привет, {first_name}!')}\n\n"
            f"🎬 Добро пожаловать в {hbold('KinoBot by Inexis')}!\n\n"
            f"Я твой персональный кино-помощник. Выбирай кнопки ниже 👇"
        )
    else:
        welcome_text = (
            f"👋 {hbold(f'С возвращением, {first_name}!')}\n\n"
            f"🎬 Чем займемся сегодня?"
        )

    # Отправляем сообщение с главной клавиатурой
    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard()
    )


# ========== ОБРАБОТКА ТЕКСТОВЫХ КНОПОК ==========
@router.message(F.text == "🎲 Случайный фильм")
async def on_random_click(message: Message):
    await message.answer(
        "🎲 Ищу случайный фильм...\n\n"
        "Эта функция скоро появится!",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "🔍 Поиск")
async def on_search_click(message: Message):
    await message.answer(
        "🔍 Введите название фильма для поиска:",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "❤️ Избранное")
async def on_favorites_click(message: Message):
    await message.answer(
        "📁 Твои коллекции. Выбери папку:",
        reply_markup=get_folders_keyboard()  # ← Теперь работает!
    )


@router.message(F.text == "📊 Профиль")
async def on_profile_click(message: Message):
    await message.answer(
        "📊 Твоя статистика скоро появится!",
        reply_markup=get_main_keyboard()
    )


@router.message(F.text == "🎯 По настроению")
async def on_mood_click(message: Message):
    await message.answer(
        "🎯 Выбери настроение:",
        reply_markup=get_mood_keyboard()
    )


@router.message(F.text == "❓ Помощь")
async def on_help_click(message: Message):
    help_text = (
        f"📚 {hbold('KinoBot by Inexis')}\n\n"
        f"Просто нажимай на кнопки:\n"
        f"🎲 Случайный фильм — сюрприз\n"
        f"🔍 Поиск — ищи по названию\n"
        f"❤️ Избранное — сохраняй фильмы\n"
        f"📊 Профиль — твой уровень\n"
        f"🎯 По настроению — подборки\n\n"
        f"Вопросы: @Inexis667"
    )
    await message.answer(help_text, reply_markup=get_main_keyboard())


# ========== ОБРАБОТКА INLINE КНОПОК ==========
@router.callback_query(F.data.startswith("mood_"))
async def process_mood(callback: CallbackQuery):
    mood_map = {
        "mood_comedy": "комедию",
        "mood_drama": "драму",
        "mood_thriller": "триллер",
        "mood_romance": "романтику",
        "mood_group": "для компании",
        "mood_family": "семейный",
        "mood_action": "боевик",
        "mood_philosophy": "глубокий фильм"
    }

    mood_text = mood_map.get(callback.data, "фильм")

    await callback.message.edit_text(
        f"🔍 Ищу {mood_text}...\n\n"
        f"Скоро здесь будут рекомендации!",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("folder_"))
async def process_folder(callback: CallbackQuery):
    folder_map = {
        "folder_favorites": "Избранное",
        "folder_watchlist": "Посмотреть позже",
        "folder_top": "Любимое",
        "folder_friends": "С друзьями"
    }

    folder_name = folder_map.get(callback.data, "папку")

    await callback.message.edit_text(
        f"📁 Папка «{folder_name}»\n\n"
        f"Здесь будут твои фильмы. Пока пусто!",
        reply_markup=get_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "new_folder")
async def new_folder(callback: CallbackQuery):
    await callback.message.edit_text(
        "📁 Введите название новой папки:",
        reply_markup=get_navigation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "nav_main")
async def go_to_main(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Главное меню:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "nav_back")
async def go_back(callback: CallbackQuery):
    await callback.message.edit_text(
        "📁 Твои коллекции. Выбери папку:",
        reply_markup=get_folders_keyboard()
    )
    await callback.answer()