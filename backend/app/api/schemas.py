from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class MovieActionSchema(BaseModel):
    tmdb_movie_id: int
    is_watched: bool = False
    rating: Optional[int] = Field(None, ge=1, le=10)
    comment: Optional[str] = Field(None, max_length=500)

class UserMovieResponse(BaseModel):
    id: int
    user_id: int
    tmdb_movie_id: int
    is_watched: bool
    rating: Optional[int]
    comment: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True

class UserStatsResponse(BaseModel):
    total_saved: int
    watched_count: int
    planned_count: int
    average_rating: Optional[float] = None
    