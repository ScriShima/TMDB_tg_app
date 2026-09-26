import httpx
import random
from app.core.config import settings
from typing import Optional
from app.core.config import settings
from asyncache import cached
from cachetools import TTLCache


TMDB_BASE_URL = "https://api.themoviedb.org/3"

genres_cache = TTLCache(maxsize=10, ttl=86400)
popular_cache = TTLCache(maxsize=50, ttl=3600)

class TMDBService:
    def __init__(self):
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {settings.tmdb_api_key}",
        }

    async def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{TMDB_BASE_URL}{endpoint}"
            query_params = {
                "language": "ru-RU",
                "api_key": settings.tmdb_api_key,
            }
            if params:
                query_params.update(params)
            response = await client.get(url, headers=self.headers, params=query_params)
            response.raise_for_status()
            return response.json()

    @cached(popular_cache)
    async def get_popular_movies(self, page:int = 1) -> dict:
        """Популярные фильмы"""
        return await self._get("/movie/popular", {"page": page})
    
    async def get_movie_details(self, movie_id: int) -> dict:
        """Подробная информация о фильме"""
        return await self._get(f"/movie/{movie_id}")

    @cached(genres_cache)
    async def get_genres(self) -> list[dict]:
        """Жанры"""
        data = await self._get("/genre/movie/list")
        return data.get("genres", [])

    async def get_random_movie(
        self,
        genre_id: Optional[int] = None,
        min_rating: float = 6.0,
        year: Optional[int] = None,) -> Optional[dict]:
        """Случайный фильм по заданным параметрам"""
        params = {
            "sort_by": 'popularity.desc',
            "vote_count.gte": 100,
            "vote_average.gte": min_rating,
        }
        if genre_id:
            params["with_genres"] = str(genre_id)
        if year:
            params["primary_release_year"] = str(year)
        

        first_page = await self._get("/discover/movie", params)
        total_pages = min(first_page.get("total_pages", 1), 20)

        if total_pages == 0:
            return None
        
        random_page = random.randint(1, total_pages)
        params["page"] = random_page
        page_data = await self._get("/discover/movie", params)
        results = page_data.get("results", [])

        if not results:
            return None

        return random.choice(results)

tmdb_service = TMDBService()