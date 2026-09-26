from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import User, UserMovie, utc_now
from app.api.schemas import (
    MovieActionSchema,
    MoviePatchSchema,
    UserMovieResponse,
    UserMovieListResponse,
    UserStatsResponse,
)
from app.core.security import get_current_user, TelegramUser
from app.services.tmdb import tmdb_service

router = APIRouter(prefix="/api/user-movies", tags=["User Movies"])

async def _movie_snapshot(movie_id: int) -> dict:
    try:
        data = await tmdb_service.get_movie_details(movie_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фильм не найден")
        raise
    return {"title": data.get("title"), "poster_path": data.get("poster_path")}

async def _ensure_user(db: AsyncSession, current_user: TelegramUser) -> User:
    res = await db.execute(select(User).where(User.id == current_user.id))
    user = res.scalar_one_or_none()
    if user is None:
        user = User(
            id=current_user.id,
            first_name=current_user.first_name,
            username=current_user.username,
        )
        db.add(user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            res = await db.execute(select(User).where(User.id == current_user.id))
            user = res.scalar_one()
        return user

    changed = False
    if user.first_name != current_user.first_name:
        user.first_name = current_user.first_name
        changed = True
    if user.username != current_user.username:
        user.username = current_user.username
        changed = True
    if changed:
        await db.commit()
    return user

def _apply_fields(item: UserMovie, data: dict) -> None:
    for key, value in data.items():
        setattr(item, key, value)
    item.updated_at = utc_now()

@router.post("/", response_model=UserMovieResponse)
async def set_user_movie(
    payload: MovieActionSchema,
    current_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Добавить фильм в библиотеку или обновить только переданные поля"""
    await _ensure_user(db, current_user)
    data = payload.model_dump(exclude_unset=True)
    data.pop("tmdb_movie_id")

    if "title" not in data or "poster_path" not in data:
        snapshot = await _movie_snapshot(payload.tmdb_movie_id)
        data.setdefault("title", snapshot["title"])
        data.setdefault("poster_path", snapshot["poster_path"])

    res = await db.execute(
        select(UserMovie).where(
            UserMovie.user_id == current_user.id,
            UserMovie.tmdb_movie_id == payload.tmdb_movie_id,
        )
    )
    item = res.scalar_one_or_none()

    if item is None:
        item = UserMovie(user_id=current_user.id, tmdb_movie_id=payload.tmdb_movie_id)
        _apply_fields(item, data)
        db.add(item)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            res = await db.execute(
                select(UserMovie).where(
                    UserMovie.user_id == current_user.id,
                    UserMovie.tmdb_movie_id == payload.tmdb_movie_id,
                )
            )
            item = res.scalar_one()
            _apply_fields(item, data)
            await db.commit()
    else:
        _apply_fields(item, data)
        await db.commit()

    await db.refresh(item)
    return item

@router.patch("/{tmdb_movie_id}", response_model=UserMovieResponse)
async def patch_user_movie(
    tmdb_movie_id: int,
    payload: MoviePatchSchema,
    current_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Изменить только переданные поля записи"""
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нет полей для обновления")

    res = await db.execute(
        select(UserMovie).where(
            UserMovie.user_id == current_user.id,
            UserMovie.tmdb_movie_id == tmdb_movie_id,
        )
    )
    item = res.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Фильм не найден в библиотеке")

    _apply_fields(item, data)
    await db.commit()
    await db.refresh(item)
    return item

@router.get("/my", response_model=UserMovieListResponse)
async def get_my_movies(
    is_watched: Optional[bool] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Личная библиотека фильмов с общим числом записей"""
    filters = [UserMovie.user_id == current_user.id]
    if is_watched is not None:
        filters.append(UserMovie.is_watched == is_watched)

    total = await db.scalar(select(func.count(UserMovie.id)).where(*filters))
    res = await db.execute(
        select(UserMovie)
        .where(*filters)
        .order_by(UserMovie.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return UserMovieListResponse(
        items=list(res.scalars().all()),
        total=total or 0,
        limit=limit,
        offset=offset,
    )

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    current_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Статистика пользователя для экрана профиля"""
    row = await db.execute(
        select(
            func.count(UserMovie.id),
            func.count(UserMovie.id).filter(UserMovie.is_watched.is_(True)),
            func.avg(UserMovie.rating),
        ).where(UserMovie.user_id == current_user.id)
    )
    total_count, watched_count, avg_rating = row.one()
    total_count = total_count or 0
    watched_count = watched_count or 0

    return UserStatsResponse(
        total_saved=total_count,
        watched_count=watched_count,
        planned_count=total_count - watched_count,
        average_rating=round(float(avg_rating), 1) if avg_rating is not None else None,
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
