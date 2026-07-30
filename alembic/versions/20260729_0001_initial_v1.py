"""Esquema inicial de Jahamina v1.

Revision ID: 20260729_0001
Revises:
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_usuarios_id", "usuarios", ["id"])
    op.create_index("ix_usuarios_email", "usuarios", ["email"], unique=True)

    op.create_table(
        "viajes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("origen", sa.String(), nullable=False),
        sa.Column("destino", sa.String(), nullable=False),
        sa.Column("fecha", sa.DateTime(), nullable=False),
        sa.Column("creador_id", sa.Integer(), nullable=False),
        sa.Column(
            "cancelado",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["creador_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_viajes_id", "viajes", ["id"])

    op.create_table(
        "viajes_unidos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("viaje_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["viaje_id"], ["viajes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "usuario_id",
            "viaje_id",
            name="uq_usuario_viaje",
        ),
    )
    op.create_index("ix_viajes_unidos_id", "viajes_unidos", ["id"])


def downgrade() -> None:
    op.drop_index("ix_viajes_unidos_id", table_name="viajes_unidos")
    op.drop_table("viajes_unidos")
    op.drop_index("ix_viajes_id", table_name="viajes")
    op.drop_table("viajes")
    op.drop_index("ix_usuarios_email", table_name="usuarios")
    op.drop_index("ix_usuarios_id", table_name="usuarios")
    op.drop_table("usuarios")
