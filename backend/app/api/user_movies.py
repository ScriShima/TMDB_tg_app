from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.models import User, UserMovie
from app.api.schemas import MovieActionSchema, UserMovieResponse

router = APIRouter(prefix="/api/user-movies", tags=["User Movies"])

@router.post("/", response_model=UserMovieResponse)
async def set_user_movie(
    payload: MovieActionSchema,
    db: AsyncSession = Depends(get_db),
):
    """Добавить фильм в список пользователя"""
    user_res = await db.execute(select(User).where(User.id == payload.user_id))
    if not user_res.scalar_one_or_none():
        reise: HTTPException(status_code=404, detail="Пользователь не найден")

    res = await db.execute(
        select(UserMovie).where(
            UserMovie.user_id == payload.user_id,
            UserMovie.tmdb_movie_id == payload.tmdb_movie_id,
        ))
    
    item = res.scalar_one_or_none()

    if not item:
        item = UserMovie(
            user_id = payload.user_id,
            tmdb_movie_id = payload.tmdb_movie_id,
            is_watched = payload.is_watched,
            rating = payload.rating,
            comment = payload.comment,
        )
        db.add(item)
    else:
        item.is_watched = payload.is_watched
        item.rating = payload.rating
        item.comment = payload.comment
    
    await db.commit()
    await db.refresh(item)
    return item

@router.get("/{user_id}", response_model=List[UserMovieResponse])
async def get_user_movies(
    user_id: int,
    is_watched: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """Получить список фильмов пользователя"""
    query = select(UserMovie).where(UserMovie.user_id == user_id)
    if is_watched is not None:
        query = query.where(UserMovie.is_watched == is_watched)

    res = await db.execute(query)
    return res.scalars().all()

