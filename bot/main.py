import asyncio
import logging
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent))

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import Config, load_config
from bot.database.db import init_db
from bot.handlers import start


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    logger.info("🚀 Запуск KinoBot by Inexis")

    # Загружаем конфиг
    config = load_config()

    # Проверяем, что токен есть
    if not config.bot_token:
        logger.error("❌ BOT_TOKEN не найден в .env файле!")
        logger.error("📝 Проверь файл .env в корне проекта")
        return

    # Инициализируем базу данных
    try:
        await init_db()
        logger.info("✅ База данных инициализирована")
    except Exception as e:
        logger.error(f"❌ Ошибка базы данных: {e}")
        return

    # Создаем бота и диспетчер
    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем роутеры (обработчики команд)
    dp.include_router(start.router)

    # Пропускаем накопившиеся обновления
    await bot.delete_webhook(drop_pending_updates=True)

    # Получаем информацию о боте
    bot_info = await bot.me()
    logger.info(f"✅ Бот запущен: @{bot_info.username}")
    logger.info("🤖 Жду команды...")

    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("👋 Бот остановлен по команде")
    except Exception as e:
        logger.error(f"❌ Ошибка при работе: {e}")
    finally:
        await bot.session.close()
        await dp.storage.close()
        logger.info("👋 Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())