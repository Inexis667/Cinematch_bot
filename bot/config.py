import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

@dataclass
class Config:
    """Конфигурация бота"""
    bot_token: str
    tmdb_api_key: str | None = None
    tmdb_access_token: str | None = None
    kinopoisk_api_token: str | None = None
    database_path: str = "data/kinobot.db"

def load_config() -> Config:
    """Загружает конфигурацию из .env"""
    return Config(
        bot_token=os.getenv("BOT_TOKEN", ""),
        tmdb_api_key=os.getenv("TMDB_API_KEY"),
        tmdb_access_token=os.getenv("TMDB_ACCESS_TOKEN"),
        kinopoisk_api_token=os.getenv("KINOPOISK_API_TOKEN"),
        database_path=os.getenv("DATABASE_PATH", "data/kinobot.db")
    )

# Для проверки
if __name__ == "__main__":
    config = load_config()
    print(f"BOT_TOKEN: {'✅ загружен' if config.bot_token else '❌ не найден'}")
    print(f"DATABASE_PATH: {config.database_path}")