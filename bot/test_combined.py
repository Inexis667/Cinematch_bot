import asyncio
from bot.services.movie_service import search_movies_all
from bot.services.kinopoisk_api import close_client
from bot.services.tmdb_api import close_tmdb_client


async def test():
    print("🔍 Тестируем объединенный поиск...")
    try:
        results = await search_movies_all("Аватар")

        print(f"✅ Всего найдено: {len(results)}")
        for i, movie in enumerate(results[:5], 1):
            source = "🎬 TMDb" if movie.get('source') == 'tmdb' else "🎥 Kinopoisk"
            year = movie.get('year', 'Неизвестно')
            print(f"\n{i}. {source}")
            print(f"   {movie.get('title')} ({year})")
            print(f"   Рейтинг: {movie.get('rating')}")
    finally:
        # Закрываем все соединения
        await close_client()
        await close_tmdb_client()


if __name__ == "__main__":
    asyncio.run(test())