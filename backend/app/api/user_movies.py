from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.models import User, UserMovie
from app.api.schemas import MovieActionSchema, UserMovieResponse
from app.core.security import get_current_user, TelegramUser

router = APIRouter(prefix="/api/user-movies", tags=["User Movies"])

@router.post("/", response_model=UserMovieResponse)
async def set_user_movie(
    payload: MovieActionSchema,
    current_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Добавить фильм в список пользователя"""
    user_res = await db.execute(select(User).where(User.id == current_user.id))
    user = user_res.scalar_one_or_none()
    if not user:
        user = User(
            id=current_user.id,
            first_name=current_user.first_name,
            username=current_user.username,
        )
        db.add(user)
        await db.commit()

    res = await db.execute(
        select(UserMovie).where(
            UserMovie.user_id == current_user.id,
            UserMovie.tmdb_movie_id == payload.tmdb_movie_id,
        )
    )
    item = res.scalar_one_or_none()

    if not item:
        item = UserMovie(
            user_id = current_user.id,
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

@router.get("/my", response_model=List[UserMovieResponse])
async def get_my_movies(
    is_watched: Optional[bool] = None,
    current_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить личную библиотеку фильмов"""
    query = select(UserMovie).where(UserMovie.user_id == current_user.id)
    if is_watched is not None:
        query = query.where(UserMovie.is_watched == is_watched)

    res = await db.execute(query)
    return res.scalars().all()

