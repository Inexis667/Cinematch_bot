from bot.services.tmdb_api import get_tmdb_client
from bot.services.kinopoisk_api import search_movies as search_kinopoisk
import asyncio


async def search_movies_all(query: str):
    """
    Ищет фильмы одновременно в TMDb и Kinopoisk
    Возвращает объединенный список
    """

    # Запускаем поиск в двух источниках параллельно
    tmdb_task = search_tmdb(query)
    kinopoisk_task = search_kinopoisk(query)

    # Ждем оба результата
    tmdb_results, kinopoisk_results = await asyncio.gather(
        tmdb_task,
        kinopoisk_task,
        return_exceptions=True
    )

    # Обрабатываем ошибки
    if isinstance(tmdb_results, Exception):
        print(f"❌ TMDb ошибка: {tmdb_results}")
        tmdb_results = []
    if isinstance(kinopoisk_results, Exception):
        print(f"❌ Kinopoisk ошибка: {kinopoisk_results}")
        kinopoisk_results = []

    # Объединяем результаты
    all_movies = []
    seen_titles = set()

    # TMDb
    for movie in tmdb_results:
        title = movie.get('title', '').lower()
        if title and title not in seen_titles:
            rating = movie.get('vote_average', 0)
            if rating is None:
                rating = 0

            # Описание TMDb
            description = movie.get('overview', '')
            if not description:
                description = '😢 Описание отсутствует на TMDb'

            # Постер TMDb
            poster = None
            if movie.get('poster_path'):
                poster = f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
            else:
                poster = "https://via.placeholder.com/300x450?text=TMDb"

            movie['rating'] = rating
            movie['description'] = description
            movie['poster'] = poster
            movie['source'] = 'tmdb'
            movie['source_emoji'] = '🎬'
            all_movies.append(movie)
            seen_titles.add(title)

    # Kinopoisk
    for movie in kinopoisk_results:
        title = movie.get('title', '').lower()
        if title and title not in seen_titles:
            movie['source'] = 'kinopoisk'
            movie['source_emoji'] = '🎥'
            all_movies.append(movie)
            seen_titles.add(title)

    # Сортируем по рейтингу (от высокого к низкому)
    all_movies.sort(key=lambda x: float(x.get('rating', 0)), reverse=True)

    return all_movies


async def search_tmdb(query: str):
    """Поиск в TMDb"""
    client = await get_tmdb_client()
    result = await client.search_movies(query)
    movies = result.get("results", []) if result else []

    # Добавляем год из release_date
    for movie in movies:
        if movie.get('release_date'):
            movie['year'] = movie['release_date'][:4]
        else:
            movie['year'] = 'Неизвестно'

    return movies