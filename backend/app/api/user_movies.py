from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.models import User, UserMovie
from app.api.schemas import MovieActionSchema, UserMovieResponse, UserStatsResponse
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
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить личную библиотеку фильмов с пагинацией"""
    query = select(UserMovie).where(UserMovie.user_id == current_user.id)
    if is_watched is not None:
        query = query.where(UserMovie.is_watched == is_watched)

    
    query = query.order_by(UserMovie.updated_at.desc()).limit(limit).offset(offset)
    res = await db.execute(query)
    return res.scalars().all()


@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить статистику пользователя для экрана профиля"""
    total_q = select(func.count(UserMovie.id)).where(UserMovie.user_id == current_user.id)
    watched_q = select(func.count(UserMovie.id)).where(
        UserMovie.user_id == current_user.id, UserMovie.is_watched.is_(True)
    )
    rating_q = select(func.avg(UserMovie.rating)).where(
        UserMovie.user_id == current_user.id, UserMovie.rating.isnot(None)
    )

    total_res = await db.execute(total_q)
    watched_res = await db.execute(watched_q)
    rating_res = await db.execute(rating_q)

    total_count = total_res.scalar_one() or 0
    watched_count = watched_res.scalar_one() or 0
    avg_rating = rating_res.scalar_one()

    return UserStatsResponse(
        total_saved = total_count,
        watched_count=watched_count,
        planned_count = total_count - watched_count,
        average_rating = round(float(avg_rating), 1) if avg_rating is not None else None,
    )

@router.delete("/{tmdb_movie_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_movie(
    tmdb_movie_id: int,
    current_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Удалить фильм из библиотеки"""
    res = await db.execute(
        select(UserMovie).where(
            UserMovie.user_id == current_user.id,
            UserMovie.tmdb_movie_id == tmdb_movie_id,
        )
    )
    item = res.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Фильм не найден в библиотеке",
        )
    
    await db.delete(item)
    await db.commit()
    return None


