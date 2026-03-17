import aiosqlite
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv()

# Путь к базе данных из .env или по умолчанию
DB_PATH = os.getenv("DATABASE_PATH", "data/kinobot.db")


async def init_db():
    """Создает таблицы, если их нет"""
    # Убедимся, что папка data существует
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Путь к файлу schema.sql
    schema_path = Path(__file__).parent / "schema.sql"

    try:
        async with aiosqlite.connect(DB_PATH) as db:
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
            await db.executescript(schema)
            await db.commit()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        raise


# ========== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ==========

async def get_user(telegram_id: int):
    """Получить пользователя по telegram_id"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


async def create_user(telegram_id: int, username: str = None, first_name: str = None):
    """Создать нового пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO users 
               (telegram_id, username, first_name) 
               VALUES (?, ?, ?)""",
            (telegram_id, username, first_name)
        )
        await db.commit()


async def update_user_level(telegram_id: int, new_level: int):
    """Обновить уровень пользователя"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET level = ? WHERE telegram_id = ?",
            (new_level, telegram_id)
        )
        await db.commit()


async def save_movie(movie_data: dict):
    """Сохранить фильм в кэш"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Убеждаемся, что жанры сохраняются как JSON
        genres_json = movie_data.get('genres')
        if isinstance(genres_json, list):
            genres_json = json.dumps(genres_json)
        elif not isinstance(genres_json, str):
            genres_json = '[]'

        await db.execute("""
            INSERT OR REPLACE INTO movies 
            (tmdb_id, title, original_title, description, rating, 
             poster_path, release_year, genres)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            movie_data['tmdb_id'],
            movie_data['title'],
            movie_data.get('original_title'),
            movie_data.get('description'),
            movie_data.get('rating'),
            movie_data.get('poster_path'),
            movie_data.get('release_year'),
            genres_json  # ← используем обработанные жанры
        ))
        await db.commit()
        return True


async def get_movie(tmdb_id: int):
    """Получить фильм по tmdb_id"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                "SELECT * FROM movies WHERE tmdb_id = ?",
                (tmdb_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                result = dict(row)
                # Преобразуем JSON обратно в список
                if result['genres']:
                    result['genres'] = json.loads(result['genres'])
                return result
            return None


async def search_movies_by_title(title: str, limit: int = 10):
    """Поиск фильмов по названию (частичное совпадение)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                """SELECT * FROM movies 
                   WHERE title LIKE ? OR original_title LIKE ?
                   ORDER BY rating DESC
                   LIMIT ?""",
                (f'%{title}%', f'%{title}%', limit)
        ) as cursor:
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                movie = dict(row)
                if movie['genres']:
                    movie['genres'] = json.loads(movie['genres'])
                return result


# ========== РАБОТА С ИЗБРАННЫМ ==========

async def add_to_favorites(telegram_id: int, tmdb_id: int, folder: str = "Избранное"):
    """Добавить фильм в избранное"""
    # Получаем пользователя
    user = await get_user(telegram_id)
    if not user:
        return False

    # Получаем фильм
    movie = await get_movie(tmdb_id)
    if not movie:
        return False

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO favorites (user_id, movie_id, folder)
            VALUES (?, ?, ?)
        """, (user['id'], movie['id'], folder))
        await db.commit()
        return True


async def remove_from_favorites(telegram_id: int, tmdb_id: int, folder: str = "Избранное"):
    """Удалить фильм из избранного"""
    user = await get_user(telegram_id)
    if not user:
        return False

    movie = await get_movie(tmdb_id)
    if not movie:
        return False

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            DELETE FROM favorites 
            WHERE user_id = ? AND movie_id = ? AND folder = ?
        """, (user['id'], movie['id'], folder))
        await db.commit()
        return True


async def get_favorites(telegram_id: int, folder: str = "Избранное"):
    """Получить список избранного пользователя"""
    user = await get_user(telegram_id)
    if not user:
        return []

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT m.* FROM favorites f
            JOIN movies m ON f.movie_id = m.id
            WHERE f.user_id = ? AND f.folder = ?
            ORDER BY f.added_at DESC
        """, (user['id'], folder)) as cursor:
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                movie = dict(row)
                if movie['genres']:
                    movie['genres'] = json.loads(movie['genres'])
                result.append(movie)
            return result


# ========== РАБОТА С ИСТОРИЕЙ ==========

async def add_search_history(telegram_id: int, query: str):
    """Добавить запрос в историю поиска"""
    user = await get_user(telegram_id)
    if not user:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO search_history (user_id, query) VALUES (?, ?)",
            (user['id'], query)
        )
        await db.commit()


async def get_search_history(telegram_id: int, limit: int = 10):
    """Получить историю поиска пользователя"""
    user = await get_user(telegram_id)
    if not user:
        return []

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT query, created_at FROM search_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user['id'], limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def add_experience(telegram_id: int, exp_points: int):
    """
    Добавить опыт пользователю
    При достижении определенного количества опыта - повышает уровень
    """
    user = await get_user(telegram_id)
    if not user:
        return

    new_exp = user['experience'] + exp_points
    current_level = user['level']

    # Проверяем, нужно ли повысить уровень (каждый уровень требует level * 100 опыта)
    exp_needed_for_next_level = current_level * 100

    while new_exp >= exp_needed_for_next_level and current_level < 10:
        new_exp -= exp_needed_for_next_level
        current_level += 1
        exp_needed_for_next_level = current_level * 100

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET level = ?, experience = ? WHERE telegram_id = ?",
            (current_level, new_exp, telegram_id)
        )
        await db.commit()

    return current_level, new_exp


async def get_user_stats(telegram_id: int) -> Dict:
    """Получить полную статистику пользователя"""
    user = await get_user(telegram_id)
    if not user:
        return {}

    # Получаем дополнительную статистику
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Количество в избранном
        async with db.execute("""
            SELECT COUNT(*) as count FROM favorites f
            JOIN users u ON f.user_id = u.id
            WHERE u.telegram_id = ?
        """, (telegram_id,)) as cursor:
            fav_count = (await cursor.fetchone())['count']

        # Количество поисков
        async with db.execute("""
            SELECT COUNT(*) as count FROM search_history sh
            JOIN users u ON sh.user_id = u.id
            WHERE u.telegram_id = ?
        """, (telegram_id,)) as cursor:
            search_count = (await cursor.fetchone())['count']

        return {
            'level': user['level'],
            'experience': user['experience'],
            'fav_count': fav_count,
            'search_count': search_count,
            'created_at': user['created_at']
        }


async def add_search_history(telegram_id: int, query: str):
    """Добавить запрос в историю поиска (с сохранением в БД)"""
    user = await get_user(telegram_id)
    if not user:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO search_history (user_id, query) VALUES (?, ?)",
            (user['id'], query)
        )
        await db.commit()

    # Добавляем опыт за поиск
    await add_experience(telegram_id, 3)  # +3 опыта за поиск


async def add_favorite_experience(telegram_id: int):
    """Добавить опыт за добавление в избранное"""
    await add_experience(telegram_id, 5)  # +5 опыта за добавление


async def get_search_history(telegram_id: int, limit: int = 10) -> List[Dict]:
    """Получить историю поиска пользователя из БД"""
    user = await get_user(telegram_id)
    if not user:
        return []

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT query, created_at FROM search_history
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (user['id'], limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]