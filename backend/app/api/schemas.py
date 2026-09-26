from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class MovieActionSchema(BaseModel):
    tmdb_movie_id: int
    is_watched: bool = False
    rating: Optional[int] = Field(None, ge=1, le=10)
    comment: Optional[str] = Field(None, max_length=500)
    title: Optional[str] = Field(None, max_length=300)
    poster_path: Optional[str] = Field(None, max_length=300)

class MoviePatchSchema(BaseModel):
    is_watched: Optional[bool] = None
    rating: Optional[int] = Field(None, ge=1, le=10)
    comment: Optional[str] = Field(None, max_length=500)
    title: Optional[str] = Field(None, max_length=300)
    poster_path: Optional[str] = Field(None, max_length=300)

class UserMovieResponse(BaseModel):
    id: int
    user_id: int
    tmdb_movie_id: int
    title: Optional[str]
    poster_path: Optional[str]
    is_watched: bool
    rating: Optional[int]
    comment: Optional[str]
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserMovieListResponse(BaseModel):
    items: list[UserMovieResponse]
    total: int
    limit: int
    offset: int

class UserStatsResponse(BaseModel):
    total_saved: int
    watched_count: int
    planned_count: int
    average_rating: Optional[float] = None
