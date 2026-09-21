from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(255))
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    movies: Mapped[list["UserMovie"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class UserMovie(Base):
    __tablename__ = "user_movies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    tmdb_movie_id: Mapped[int] = mapped_column(Integer, index=True)

    is_watched: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="movies")

    __table_args__ = (UniqueConstraint("user_id", "tmdb_movie_id", name="uq_user_movie"),)