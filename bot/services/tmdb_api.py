import aiohttp
import os
import random
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN")
BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
LARGE_IMAGE_URL = "https://image.tmdb.org/t/p/original"

# Жанры фильмов (для красивого отображения)
GENRE_MAP = {
    28: "Боевик",
    12: "Приключения",
    16: "Мультфильм",
    35: "Комедия",
    80: "Криминал",
    99: "Документальный",
    18: "Драма",
    10751: "Семейный",
    14: "Фэнтези",
    36: "История",
    27: "Ужасы",
    10402: "Музыка",
    9648: "Детектив",
    10749: "Мелодрама",
    878: "Фантастика",
    10770: "ТВ фильм",
    53: "Триллер",
    10752: "Военный",
    37: "Вестерн"
}


class TMDBClient:
    """Клиент для работы с TMDb API"""

    def __init__(self):
        self.api_key = TMDB_API_KEY
        self.access_token = TMDB_ACCESS_TOKEN
        self.session = None

    async def get_session(self):
        """Получить или создать сессию"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Закрыть сессию"""
        if self.session:
            await self.session.close()

    async def search_movies(self, query: str, page: int = 1) -> Dict:
        """
        Поиск фильмов по названию

        Args:
            query: поисковый запрос
            page: страница результатов

        Returns:
            Dict с результатами поиска
        """
        session = await self.get_session()

        url = f"{BASE_URL}/search/movie"
        params = {
            "api_key": self.api_key,
            "query": query,
            "language": "ru-RU",
            "page": page,
            "include_adult": "false"  # ← ИСПРАВЛЕНО: строка вместо булева
        }

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"Ошибка TMDb API: {response.status}")
                    return {"results": [], "total_results": 0}
        except Exception as e:
            print(f"Исключение при запросе к TMDb: {e}")
            return {"results": [], "total_results": 0}

    async def get_popular_movies(self, page: int = 1) -> Dict:
        """
        Получить популярные фильмы

        Args:
            page: страница результатов

        Returns:
            Dict с популярными фильмами
        """
        session = await self.get_session()

        url = f"{BASE_URL}/movie/popular"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
            "page": page
        }

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return {"results": []}
        except Exception as e:
            print(f"Ошибка получения популярных: {e}")
            return {"results": []}

    async def discover_movies(self, genre_id: int = None, year: int = None, page: int = 1) -> Dict:
        """
        Поиск фильмов с фильтрацией (для настроения)

        Args:
            genre_id: ID жанра
            year: год выпуска
            page: страница

        Returns:
            Dict с фильмами
        """
        session = await self.get_session()

        url = f"{BASE_URL}/discover/movie"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
            "page": page,
            "sort_by": "popularity.desc",
            "include_adult": "false"  # ← ИСПРАВЛЕНО: строка вместо булева
        }

        if genre_id:
            params["with_genres"] = genre_id
        if year:
            params["primary_release_year"] = year

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return {"results": []}
        except Exception as e:
            print(f"Ошибка discover: {e}")
            return {"results": []}

    async def get_movie_details(self, movie_id: int) -> Optional[Dict]:
        """
        Получить детальную информацию о фильме

        Args:
            movie_id: ID фильма в TMDb

        Returns:
            Dict с деталями фильма
        """
        session = await self.get_session()

        url = f"{BASE_URL}/movie/{movie_id}"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
            "append_to_response": "videos,credits,similar"
        }

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            print(f"Ошибка получения деталей: {e}")
            return None

    async def get_random_movie(self) -> Optional[Dict]:
        """
        Получить случайный популярный фильм
        Теперь выбирает со случайной страницы для разнообразия

        Returns:
            Dict с данными фильма
        """
        # Выбираем случайную страницу (1-5)
        page = random.randint(1, 5)

        # Получаем популярные фильмы
        popular = await self.get_popular_movies(page)

        if not popular or not popular.get("results"):
            # Если не получилось, пробуем поиск
            search_result = await self.search_movies("")
            if search_result and search_result.get("results"):
                movies = search_result["results"]
            else:
                return None
        else:
            movies = popular["results"]

        if not movies:
            return None

        # Выбираем случайный фильм
        movie = random.choice(movies)

        # Получаем полные детали
        return await self.get_movie_details(movie["id"])

    def format_movie_for_display(self, movie_data: Dict) -> Dict:
        """
        Форматирует данные фильма для красивого отображения

        Args:
            movie_data: сырые данные из API

        Returns:
            Dict с отформатированными данными
        """
        # Основная информация
        title = movie_data.get("title", "Без названия")
        original_title = movie_data.get("original_title", "")
        year = movie_data.get("release_date", "")[:4] if movie_data.get("release_date") else "Неизвестно"

        # Рейтинг
        vote_average = movie_data.get("vote_average", 0)
        vote_count = movie_data.get("vote_count", 0)

        # Форматируем рейтинг
        if vote_average > 0:
            rating_stars = "⭐" * int(round(vote_average / 2))
            rating_text = f"{rating_stars} {vote_average:.1f}/10 ({vote_count} голосов)"
        else:
            rating_text = "⭐ Нет оценок"

        # Описание (оставляем полным для деталей)
        overview = movie_data.get("overview", "Описание отсутствует")

        # Жанры (исправлено!)
        genres = movie_data.get("genres", [])
        if isinstance(genres, str):
            # Если жанры пришли как строка - пытаемся распарсить
            try:
                import json
                genres = json.loads(genres)
            except:
                genres = []

        genre_names = []
        if isinstance(genres, list):
            for g in genres:
                if isinstance(g, dict):
                    genre_names.append(g.get("name", "Неизвестно"))
                elif isinstance(g, (int, str)):
                    # Если пришёл ID жанра
                    genre_names.append(GENRE_MAP.get(int(g) if str(g).isdigit() else g, str(g)))

        genre_text = ", ".join(genre_names) if genre_names else "Неизвестно"

        # Постер
        poster_path = movie_data.get("poster_path")
        poster_url = f"{IMAGE_BASE_URL}{poster_path}" if poster_path else None

        # Большой постер
        backdrop_path = movie_data.get("backdrop_path")
        backdrop_url = f"{LARGE_IMAGE_URL}{backdrop_path}" if backdrop_path else poster_url

        # Режиссер
        director = "Неизвестно"
        if "credits" in movie_data:
            crew = movie_data["credits"].get("crew", [])
            for person in crew:
                if person.get("job") == "Director":
                    director = person.get("name", "Неизвестно")
                    break

        # Актеры (первые 5)
        cast = []
        if "credits" in movie_data:
            for actor in movie_data["credits"].get("cast", [])[:5]:
                cast.append(actor.get("name", "Неизвестно"))

        cast_text = ", ".join(cast) if cast else "Информация отсутствует"

        # Трейлер
        trailer_key = None
        if "videos" in movie_data:
            videos = movie_data["videos"].get("results", [])
            for video in videos:
                if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                    trailer_key = video.get("key")
                    break

        return {
            "id": movie_data.get("id"),
            "title": title,
            "original_title": original_title,
            "year": year,
            "rating": vote_average,
            "rating_text": rating_text,
            "description": overview,
            "genres": genre_text,
            "director": director,
            "cast": cast_text,
            "poster_url": poster_url,
            "backdrop_url": backdrop_url,
            "trailer_key": trailer_key,
            "vote_count": vote_count
        }


# Создаем глобальный экземпляр клиента
tmdb_client = TMDBClient()


async def get_tmdb_client() -> TMDBClient:
    """Получить клиент TMDb"""
    return tmdb_client


async def close_tmdb_client():
    """Закрыть клиент TMDb"""
    await tmdb_client.close()