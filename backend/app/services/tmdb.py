import httpx
from app.core.config import settings

TMDB_BASE_URL = "https://api.themoviedb.org/3"

class TMDBService:
    def __init__(self):
        self.headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {settings.tmdb_api_key}",
        }

    async def get_popular_movies(self, page: int = 1, language: str = "ru-RU") -> dict:
        """Получение популярных фильмов"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{TMDB_BASE_URL}/movie/popular"
            params = {
                "language": language,
                "page": page,
                "api_key": settings.tmdb_api_key,
            }
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

tmdb_service = TMDBService()