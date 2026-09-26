"""add title and poster to user movies

Revision ID: b7e1c4a92d10
Revises: 0c6be794eb58
Create Date: 2026-09-26 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e1c4a92d10"
down_revision: Union[str, Sequence[str], None] = "0c6be794eb58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_movies", sa.Column("title", sa.String(length=300), nullable=True))
    op.add_column("user_movies", sa.Column("poster_path", sa.String(length=300), nullable=True))


def downgrade() -> None:
    op.drop_column("user_movies", "poster_path")
    op.drop_column("user_movies", "title")
