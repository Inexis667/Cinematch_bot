import asyncio
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold, hitalic, hcode
from datetime import datetime

from bot.database.db import get_user, create_user
from bot.keyboards.reply import (
    get_main_keyboard,
    get_mood_keyboard,
    get_folders_keyboard,
    get_navigation_keyboard
)

router = Router()


# ========== ЭПИЧНЫЙ СТАРТ ==========
@router.message(Command("start"))
async def cmd_start(message: Message):
    """
    Великолепное приветствие с анимацией и стилем
    """
    user = message.from_user
    user_id = user.id
    username = user.username
    first_name = user.first_name or "друг"
    current_hour = datetime.now().hour

    # Определяем время суток для персонализации
    if 5 <= current_hour < 12:
        time_greeting = "Доброе утро"
    elif 12 <= current_hour < 18:
        time_greeting = "Добрый день"
    elif 18 <= current_hour < 23:
        time_greeting = "Добрый вечер"
    else:
        time_greeting = "Доброй ночи"

    db_user = await get_user(user_id)

    if not db_user:
        await create_user(user_id, username, first_name)

        # Эпичное приветствие для новичков
        welcome_text = (
            f"🎬✨ {hbold('KINOBOT by Inexis')} ✨🎬\n\n"
            f"{hbold('🌟 Добро пожаловать в мир кино!')}\n\n"
            f"👤 {hitalic(first_name)}, ты стал частью самого уютного кино-сообщества!\n\n"
            f"{hbold('🎯 Что тебя ждет:')}\n"
            f"▫️ 🔍 {hitalic('Умный поиск')} — найдет любой фильм за секунду\n"
            f"▫️ 🎲 {hitalic('Кино-рулетка')} — сюрприз для смелых\n"
            f"▫️ ❤️ {hitalic('Личные коллекции')} — храни любимое\n"
            f"▫️ 🎭 {hitalic('По настроению')} — подборки для души\n"
            f"▫️ 📊 {hitalic('Статистика')} — расти как киноман\n\n"
            f"{hbold('👇 Начинай с кнопки ПОИСК или РУЛЕТКА!')}"
        )
    else:
        # Теплое приветствие для старичков
        welcome_text = (
            f"🎬 {hbold(f'{time_greeting}, {first_name}!')} 🎬\n\n"
            f"⭐ Рад снова тебя видеть!\n\n"
            f"{hbold('Твои возможности сегодня:')}\n"
            f"• Найди фильм по 🔍 поиску\n"
            f"• Рискни в 🎲 рулетке\n"
            f"• Проверь ❤️ коллекции\n\n"
            f"{hitalic('Что будем смотреть сегодня?')}"
        )

    # Отправляем приветствие с красивым постером
    await message.answer_photo(
        photo="https://image.tmdb.org/t/p/original/wwemzKWzjKYJFfCeiB57q3r4Bcm.png",
        caption=welcome_text,
        reply_markup=get_main_keyboard()
    )


# ========== ЭЛЕГАНТНЫЙ ПОИСК ==========
@router.message(F.text == "🔍 ПОИСК")
async def on_search_click(message: Message):
    """
    Запуск поиска с инструкцией
    """
    search_text = (
        f"🔍 {hbold('ПОИСК ФИЛЬМОВ')}\n\n"
        f"📝 {hitalic('Просто напиши название:')}\n"
        f"▫️ На русском: {hcode('Аватар')}\n"
        f"▫️ На английском: {hcode('Inception')}\n"
        f"▫️ По актеру: {hcode('Ди Каприо')}\n\n"
        f"⚡ {hbold('Я найду всё!')}"
    )

    await message.answer(
        search_text,
        reply_markup=get_main_keyboard()
    )


# ========== КИНО-РУЛЕТКА ==========
@router.message(F.text == "🎲 РУЛЕТКА")
async def on_random_click(message: Message):
    """
    Эффектная кино-рулетка
    """
    await message.bot.send_chat_action(message.chat.id, action="typing")

    # Эффект ожидания
    wait_msg = await message.answer("🎲 Крутим барабан...")
    await asyncio.sleep(1)
    await wait_msg.delete()

    # Просто перенаправляем в roulette.py
    from bot.handlers.roulette import cmd_random
    await cmd_random(message)


# ========== МОИ КОЛЛЕКЦИИ ==========
@router.message(F.text == "❤️ МОЁ")
async def on_favorites_click(message: Message):
    """
    Красивый показ коллекций
    """
    # Перенаправляем в favorites.py
    from bot.handlers.favorites import show_favorites
    await show_favorites(message)


# ========== ПРОФИЛЬ КИНОМАНА ==========
@router.message(F.text == "📊 ПРОФИЛЬ")
async def on_profile_click(message: Message):
    """
    Стильный профиль с прогрессом
    """
    # Перенаправляем в profile.py
    from bot.handlers.profile import show_profile
    await show_profile(message)


# ========== МЕНЮ НАСТРОЕНИЙ ==========
@router.message(F.text == "🎯 НАСТРОЕНИЕ")
async def on_mood_click(message: Message):
    """
    Выбор настроения
    """
    # Перенаправляем в mood.py
    from bot.handlers.mood import show_mood_menu
    await show_mood_menu(message)


# ========== ПОМОЩЬ ==========
@router.message(F.text == "❓ ПОМОЩЬ")
async def on_help_click(message: Message):
    """
    Элегантный help
    """
    help_text = (
        f"❓ {hbold('ПОМОЩЬ ПО KINOBOT')}\n\n"
        f"{hbold('🔍 ПОИСК:')}\n"
        f"  Нажми кнопку и введи название\n\n"
        f"{hbold('🎲 РУЛЕТКА:')}\n"
        f"  Случайный фильм для смелых\n\n"
        f"{hbold('❤️ МОЁ:')}\n"
        f"  Твои личные коллекции\n\n"
        f"{hbold('📊 ПРОФИЛЬ:')}\n"
        f"  Статистика и достижения\n\n"
        f"{hbold('🎯 НАСТРОЕНИЕ:')}\n"
        f"  Подборки под эмоции\n\n"
        f"📱 {hbold('Контакты:')} @Inexis667\n"
        f"🤖 {hbold('Версия:')} 2.0.0 (Премиум)"
    )

    await message.answer(help_text, reply_markup=get_main_keyboard())


# ========== ОБРАБОТКА ПАПОК ==========
@router.callback_query(F.data.startswith("folder_"))
async def process_folder(callback: CallbackQuery):
    """
    Показ содержимого папки
    """
    folder_map = {
        "folder_favorites": "⭐ Избранное",
        "folder_watchlist": "📋 К просмотру",
        "folder_top": "🏆 Шедевры",
        "folder_friends": "👥 С друзьями"
    }

    folder_name = folder_map.get(callback.data, "папка")

    await callback.message.edit_text(
        f"📁 {hbold(folder_name)}\n\n"
        f"😢 {hitalic('Здесь пока пусто...')}\n\n"
        f"💡 Найди фильм через поиск и добавь в коллекцию!",
        reply_markup=get_navigation_keyboard()
    )
    await callback.answer()


# ========== СОЗДАНИЕ НОВОЙ ПАПКИ ==========
@router.callback_query(F.data == "new_folder")
async def new_folder(callback: CallbackQuery):
    """
    Создание новой папки
    """
    await callback.message.edit_text(
        f"📁 {hbold('СОЗДАНИЕ ПАПКИ')}\n\n"
        f"{hitalic('Введите название для новой папки:')}\n\n"
        f"{hcode('Например: Любимые комедии')}",
        reply_markup=get_navigation_keyboard()
    )
    await callback.answer()