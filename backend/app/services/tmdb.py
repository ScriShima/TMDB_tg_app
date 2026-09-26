import asyncio
from typing import Optional

import httpx
import random
from asyncache import cached
from cachetools import TTLCache

from app.core.config import settings

TMDB_BASE_URL = "https://api.themoviedb.org/3"

genres_cache = TTLCache(maxsize=10, ttl=86400)
popular_cache = TTLCache(maxsize=50, ttl=3600)

class TMDBService:
    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None
        self._genres_lock = asyncio.Lock()
        self._popular_lock = asyncio.Lock()

    def start(self) -> None:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _auth(self, params: Optional[dict]) -> tuple[dict, dict]:
        headers = {"accept": "application/json"}
        query_params = {"language": "ru-RU"}
        if settings.tmdb_api_key.startswith("eyJ"):
            headers["Authorization"] = f"Bearer {settings.tmdb_api_key}"
        else:
            query_params["api_key"] = settings.tmdb_api_key
        if params:
            query_params.update(params)
        return headers, query_params

    async def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        self.start()
        headers, query_params = self._auth(params)
        response = await self._client.get(
            f"{TMDB_BASE_URL}{endpoint}",
            headers=headers,
            params=query_params,
        )
        response.raise_for_status()
        return response.json()

    async def get_popular_movies(self, page: int = 1) -> dict:
        """Популярные фильмы. Повторные одновременные промахи ждут один запрос."""
        async with self._popular_lock:
            return await self._cached_popular(page)

    @cached(popular_cache)
    async def _cached_popular(self, page: int = 1) -> dict:
        return await self._get("/movie/popular", {"page": page})

    async def get_movie_details(self, movie_id: int) -> dict:
        """Подробная информация о фильме"""
        return await self._get(f"/movie/{movie_id}")

    async def search_movies(self, query: str, page: int = 1) -> dict:
        """Поиск фильмов по названию"""
        return await self._get(
            "/search/movie",
            {"query": query, "page": page, "include_adult": "false"},
        )

    async def get_genres(self) -> list[dict]:
        """Жанры. Повторные одновременные промахи ждут один запрос."""
        async with self._genres_lock:
            return await self._cached_genres()

    @cached(genres_cache)
    async def _cached_genres(self) -> list[dict]:
        data = await self._get("/genre/movie/list")
        return data.get("genres", [])

    async def get_random_movie(
        self,
        genre_id: Optional[int] = None,
        min_rating: float = 6.0,
        year: Optional[int] = None,
    ) -> Optional[dict]:
        """Случайный фильм по заданным параметрам"""
        params = {
            "sort_by": "popularity.desc",
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
        if random_page == 1:
            page_data = first_page
        else:
            params["page"] = random_page
            page_data = await self._get("/discover/movie", params)
        results = page_data.get("results", [])

        if not results:
            return None

        return random.choice(results)

tmdb_service = TMDBService()
