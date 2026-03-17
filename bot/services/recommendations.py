import random
import json
from collections import Counter
from typing import List, Dict, Tuple

from bot.database.db import get_search_history, get_favorites
from bot.services.tmdb_api import get_tmdb_client

# Словарь жанров для объяснений
GENRE_EXPLANATIONS = {
    28: "ты любишь боевики",
    12: "тебе нравятся приключения",
    16: "ты фанат анимации",
    35: "ты любишь посмеяться",
    80: "тебе нравятся криминальные истории",
    18: "ты ценишь глубокие драмы",
    10751: "ты любишь семейное кино",
    14: "тебе нравится фэнтези",
    27: "ты любишь пощекотать нервы",
    10749: "ты романтик в душе",
    878: "тебя манит фантастика",
    53: "ты любишь напряжение",
}


async def get_user_preferences(user_id: int) -> Tuple[List[int], List[str]]:
    """
    Анализирует историю пользователя и возвращает:
    - список любимых жанров (ID)
    - список любимых актёров/режиссёров
    """
    # Получаем историю поиска и избранное
    history = await get_search_history(user_id, limit=20)
    favorites = await get_favorites(user_id)

    print(f"📊 Анализ пользователя {user_id}")
    print(f"📁 Избранное: {len(favorites)} фильмов")
    print(f"🔍 История: {len(history)} запросов")

    # Собираем все фильмы, которые интересовали пользователя
    all_movies = []

    for fav in favorites:
        all_movies.append(fav)

    if not all_movies:
        print("❌ Нет фильмов в избранном")
        return [], []

    # Анализируем жанры
    genre_counter = Counter()

    for movie in all_movies:
        # Получаем жанры из БД
        genres_data = movie.get('genres')
        if genres_data:
            try:
                # Если это строка JSON
                if isinstance(genres_data, str):
                    genres = json.loads(genres_data)
                # Если это уже список
                elif isinstance(genres_data, list):
                    genres = genres_data
                else:
                    genres = []

                # Обрабатываем жанры
                for g in genres:
                    # Если жанр пришёл как число
                    if isinstance(g, (int, float)):
                        genre_counter[int(g)] += 1
                        print(f"  + Жанр ID {g}")
                    # Если как строка, пытаемся преобразовать
                    elif isinstance(g, str) and g.isdigit():
                        genre_counter[int(g)] += 1
                        print(f"  + Жанр ID {g}")
            except Exception as e:
                print(f"  ❌ Ошибка парсинга жанров: {e}")
                continue

    print(f"📊 Статистика жанров: {dict(genre_counter)}")

    # Топ-3 любимых жанра
    top_genres = [g for g, _ in genre_counter.most_common(3)]
    print(f"🏆 Топ жанры: {top_genres}")

    # Анализируем ключевые слова из истории поиска
    search_terms = []
    for item in history:
        if item.get('query'):
            query = item['query'].lower()
            search_terms.append(query)
            # Разбиваем на отдельные слова для лучшего анализа
            search_terms.extend(query.split())

    # Убираем дубликаты и короткие слова
    search_terms = list(set([t for t in search_terms if len(t) > 3]))
    print(f"🔍 Поисковые термины: {search_terms[:5]}")

    return top_genres, search_terms


async def get_recommendations(user_id: int, limit: int = 5) -> List[Dict]:
    """
    Генерирует персональные рекомендации на основе предпочтений пользователя
    """
    print(f"\n🎯 Генерация рекомендаций для пользователя {user_id}")

    top_genres, search_terms = await get_user_preferences(user_id)

    if not top_genres and not search_terms:
        print("⚠️ Нет данных для персонализации, показываем популярное")
        return await get_popular_recommendations(limit)

    client = await get_tmdb_client()
    recommendations = []

    # Используем любимые жанры для поиска
    for genre_id in top_genres[:2]:  # Берём первые 2 жанра
        print(f"🔍 Ищем фильмы жанра {genre_id}")
        result = await client.discover_movies(genre_id=genre_id, page=1)
        movies = result.get("results", [])[:5]

        for movie in movies:
            # Получаем детали для полной информации
            details = await client.get_movie_details(movie['id'])
            if details:
                formatted = client.format_movie_for_display(details)
                formatted['reason'] = get_reason_text(movie, genre_id, search_terms)
                recommendations.append(formatted)
                print(f"  + {formatted['title']}")

    # Перемешиваем и ограничиваем
    random.shuffle(recommendations)
    result = recommendations[:limit]
    print(f"✅ Готово рекомендаций: {len(result)}")

    return result


def get_reason_text(movie: Dict, genre_id: int, search_terms: List[str]) -> str:
    """
    Генерирует объяснение, почему рекомендуем этот фильм
    """
    reasons = []

    # Объяснение по жанру
    genre_explanation = GENRE_EXPLANATIONS.get(genre_id, "тебе нравятся такие фильмы")
    reasons.append(genre_explanation)

    # Если есть совпадение с поисковыми запросами
    title = movie.get('title', '').lower()
    for term in search_terms[:3]:  # Проверяем первые 3 термина
        if term and term in title:
            reasons.append(f"ты искал(а) что-то похожее на '{term}'")
            break

    # Если есть популярные актёры
    if random.choice([True, False]) and len(reasons) < 2:
        reasons.append("этот фильм высоко оценили другие зрители")

    # Формируем финальный текст
    if len(reasons) == 1:
        return f"🎯 Потому что {reasons[0]}"
    else:
        return f"🎯 Потому что {reasons[0]} и {reasons[1]}"


async def get_popular_recommendations(limit: int = 5) -> List[Dict]:
    """
    Рекомендации для новых пользователей (популярное)
    """
    print("📊 Загружаем популярные фильмы")
    client = await get_tmdb_client()
    result = await client.get_popular_movies(page=1)
    movies = result.get("results", [])[:limit]

    recommendations = []
    for movie in movies:
        details = await client.get_movie_details(movie['id'])
        if details:
            formatted = client.format_movie_for_display(details)
            formatted['reason'] = "🔥 Это популярный фильм, который нравится многим"
            recommendations.append(formatted)

    return recommendations