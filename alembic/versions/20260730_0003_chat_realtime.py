"""Chat seguro para reservas.

Revision ID: 20260730_0003
Revises: 20260729_0002
Create Date: 2026-07-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260730_0003"
down_revision: str | None = "20260729_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversaciones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("solicitud_id", sa.Integer(), nullable=False),
        sa.Column(
            "creada_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "actualizada_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ultimo_mensaje_en", sa.DateTime(timezone=True)),
        sa.Column("cerrada_en", sa.DateTime(timezone=True)),
        sa.Column(
            "activa", sa.Boolean(), server_default=sa.true(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["solicitud_id"], ["solicitudes_viaje.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_conversaciones_id", "conversaciones", ["id"])
    op.create_index(
        "ix_conversaciones_solicitud_id",
        "conversaciones",
        ["solicitud_id"],
        unique=True,
    )

    op.create_table(
        "mensajes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversacion_id", sa.Integer(), nullable=False),
        sa.Column("remitente_id", sa.Integer()),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column(
            "tipo",
            sa.String(20),
            server_default="texto",
            nullable=False,
        ),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("editado_en", sa.DateTime(timezone=True)),
        sa.Column("leido_en", sa.DateTime(timezone=True)),
        sa.Column(
            "eliminado",
            sa.Boolean(),
            server_default=sa.false(),
            nullable=False,
        ),
        sa.Column("client_message_id", sa.String(100)),
        sa.CheckConstraint(
            "tipo IN ('texto','sistema')", name="ck_mensajes_tipo"
        ),
        sa.CheckConstraint(
            "char_length(contenido) BETWEEN 1 AND 1000",
            name="ck_mensajes_contenido",
        ),
        sa.ForeignKeyConstraint(
            ["conversacion_id"], ["conversaciones.id"]
        ),
        sa.ForeignKeyConstraint(["remitente_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mensajes_historial",
        "mensajes",
        ["conversacion_id", "id"],
    )
    op.create_index(
        "ix_mensajes_no_leidos",
        "mensajes",
        ["conversacion_id", "remitente_id"],
        postgresql_where=sa.text(
            "leido_en IS NULL AND eliminado = false"
        ),
    )
    op.create_index(
        "uq_mensaje_client_id",
        "mensajes",
        ["conversacion_id", "remitente_id", "client_message_id"],
        unique=True,
        postgresql_where=sa.text("client_message_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_mensaje_client_id", table_name="mensajes")
    op.drop_index("ix_mensajes_no_leidos", table_name="mensajes")
    op.drop_index("ix_mensajes_historial", table_name="mensajes")
    op.drop_table("mensajes")
    op.drop_index(
        "ix_conversaciones_solicitud_id", table_name="conversaciones"
    )
    op.drop_index("ix_conversaciones_id", table_name="conversaciones")
    op.drop_table("conversaciones")
