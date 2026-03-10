from bot.services.tmdb_api import get_tmdb_client
import re

async def search_movies_all(query: str):
    """
    Ищет фильмы в TMDb.
    Поддерживает формат: "название год"
    """

    # --- 1. Парсим запрос на название и год ---
    year_match = re.search(r'\s+(\d{4})$', query)
    year = None
    title_query = query

    if year_match:
        year = year_match.group(1)
        # Убираем год из строки запроса, чтобы искать только по названию
        title_query = query[:year_match.start()].strip()

    print(f"🔍 Ищем название: '{title_query}', фильтруем по году: {year}")

    # --- 2. Получаем клиент и выполняем поиск ТОЛЬКО ПО НАЗВАНИЮ ---
    client = await get_tmdb_client()
    # Здесь мы всегда вызываем search_movies ТОЛЬКО с названием
    result = await client.search_movies(title_query)
    all_movies = result.get("results", []) if result else []

    if not all_movies:
        return []

    # --- 3. Финальная фильтрация ---
    final_results = []

    for movie in all_movies:
        movie_year = movie.get('release_date', '')[:4] if movie.get('release_date') else None
        movie['source'] = 'tmdb' # Добавляем источник для отображения

        # Если год не указан в запросе, добавляем все фильмы
        if not year:
            final_results.append(movie)
        # Если год указан, добавляем только те, у которых год совпадает
        elif movie_year == year:
            final_results.append(movie)

    # Если мы искали конкретный фильм с годом, возвращаем только его (или пустой список)
    if year:
        return final_results
    else:
        # Если искали без года, возвращаем всё, что нашли (как обычно)
        return final_results