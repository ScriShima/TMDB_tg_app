from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.services.tmdb import tmdb_service

router = APIRouter(prefix="/api/movies", tags=["Movies"])

@router.get("/popular")
async def get_popular(page: int = Query(1, ge=1)):
    """Каталог популярных фильмов"""
    return await tmdb_service.get_popular_movies(page=page)

@router.get("/genres")
async def get_genres():
    """Список жанров"""
    return await tmdb_service.get_genres()

@router.get("/random")
async def get_random(
    genre_id: Optional[int] = None,
    min_rating: float = Query(6.0, ge=0, le=10),
    year: Optional[int] = None,
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
    except Exception:
        raise HTTPException(status_code=404, detail="Фильм не найден")
