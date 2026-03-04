import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

KINOPOISK_TOKEN = os.getenv("KINOPOISK_API_TOKEN")
BASE_URL = "https://kinopoiskapiunofficial.tech/api"

# Глобальная сессия
_session = None


async def get_session():
    """Получить или создать сессию"""
    global _session
    if _session is None:
        _session = aiohttp.ClientSession()
    return _session


async def close_client():
    """Закрыть сессию"""
    global _session
    if _session:
        await _session.close()
        _session = None


async def search_movies(query: str):
    """Поиск фильмов по названию"""
    if not KINOPOISK_TOKEN:
        print("❌ Нет токена Kinopoisk")
        return []

    session = await get_session()
    url = f"{BASE_URL}/v2.1/films/search-by-keyword"
    headers = {"X-API-KEY": KINOPOISK_TOKEN}
    params = {"keyword": query, "page": 1}

    try:
        async with session.get(url, headers=headers, params=params) as response:
            if response.status == 200:
                data = await response.json()
                films = data.get("films", [])

                results = []
                for film in films[:15]:
                    # 1️⃣ ГОД
                    year = film.get('year')
                    if not year and film.get('releaseDate'):
                        year = film['releaseDate'][:4]
                    if not year:
                        year = 'Неизвестно'

                    # 2️⃣ РЕЙТИНГ (может быть пустым)
                    rating = film.get('rating')
                    if rating is None or rating == '' or rating == 'null':
                        rating = 0
                    else:
                        try:
                            if isinstance(rating, str):
                                rating = float(rating.replace(',', '.'))
                            else:
                                rating = float(rating)
                        except:
                            rating = 0

                    # 3️⃣ ОПИСАНИЕ (может отсутствовать)
                    description = film.get('description') or film.get('shortDescription') or ''
                    if not description or description.strip() == '':
                        description = '😢 Описание отсутствует на Kinopoisk'

                    # 4️⃣ ПОСТЕР (может отсутствовать)
                    poster = film.get('posterUrlPreview') or film.get('posterUrl') or ''
                    if not poster:
                        poster = "https://via.placeholder.com/300x450?text=Kinopoisk"

                    # 5️⃣ ЖАНРЫ (если есть)
                    genres = []
                    if film.get('genres'):
                        genres = [g.get('genre') for g in film['genres'] if g.get('genre')]

                    results.append({
                        'id': film.get('filmId'),
                        'title': film.get('nameRu') or film.get('nameEn', 'Без названия'),
                        'year': year,
                        'rating': rating,
                        'description': description,
                        'poster': poster,
                        'genres': genres,
                    })
                return results
            else:
                print(f"❌ Ошибка API Kinopoisk: {response.status}")
                return []
    except Exception as e:
        print(f"❌ Ошибка Kinopoisk: {e}")
        return []