"""add optional user and vehicle image urls

Revision ID: 20260807_0008
Revises: 20260804_0007
"""
from alembic import op
import sqlalchemy as sa


revision = "20260807_0008"
down_revision = "20260804_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("imagen_url", sa.String(length=2048), nullable=True))
    op.add_column("vehiculos", sa.Column("imagen_url", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    op.drop_column("vehiculos", "imagen_url")
    op.drop_column("usuarios", "imagen_url")
