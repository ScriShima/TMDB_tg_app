from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.services.tmdb import tmdb_service

router = APIRouter(prefix="/api/movies", tags=["Movies"])

@router.get("/popular")
async def get_popular(page: int = Query(1, ge=1, le=500)):
    """Каталог популярных фильмов"""
    return await tmdb_service.get_popular_movies(page=page)

@router.get("/genres")
async def get_genres():
    """Список жанров"""
    return await tmdb_service.get_genres()

@router.get("/search")
async def search_movies(
    query: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1, le=500),
):
    """Поиск фильмов по названию"""
    return await tmdb_service.search_movies(query=query, page=page)

@router.get("/random")
async def get_random(
    genre_id: Optional[int] = None,
    min_rating: float = Query(6.0, ge=0, le=10),
    year: Optional[int] = Query(None, ge=1900, le=2100),
):
    """Случайный фильм по заданным параметрам"""
    movie = await tmdb_service.get_random_movie(
        genre_id=genre_id, min_rating=min_rating, year=year
    )
    if not movie:
        raise HTTPException(status_code=404, detail="Фильмы не найдены")
    return movie

@router.get("/{movie_id}")
async def get_details(movie_id: int):
    """Подробная информация о фильме"""
    try:
        return await tmdb_service.get_movie_details(movie_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Фильм не найден")
        raise
