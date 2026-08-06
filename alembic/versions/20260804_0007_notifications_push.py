"""add internal notifications and push subscriptions

Revision ID: 20260804_0007
Revises: 20260804_0006
"""
from alembic import op
import sqlalchemy as sa

revision = "20260804_0007"
down_revision = "20260804_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notificaciones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("tipo", sa.String(40), nullable=False),
        sa.Column("titulo", sa.String(120), nullable=False),
        sa.Column("cuerpo", sa.String(300), nullable=False),
        sa.Column("reserva_id", sa.Integer(), sa.ForeignKey("solicitudes_viaje.id")),
        sa.Column("viaje_id", sa.Integer(), sa.ForeignKey("viajes.id")),
        sa.Column("conversacion_id", sa.Integer(), sa.ForeignKey("conversaciones.id")),
        sa.Column("url_destino", sa.String(300), nullable=False),
        sa.Column("leida", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("creada_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("leida_en", sa.DateTime(timezone=True)),
        sa.Column("clave_idempotencia", sa.String(180), nullable=False),
        sa.UniqueConstraint("clave_idempotencia", name="uq_notificaciones_clave_idempotencia"),
    )
    op.create_index("ix_notificaciones_usuario_id", "notificaciones", ["usuario_id"])
    op.create_index("ix_notificaciones_creada_en", "notificaciones", ["creada_en"])
    op.create_index("ix_notificaciones_usuario_leida_creada", "notificaciones", ["usuario_id", "leida", "creada_en"])
    op.create_table(
        "suscripciones_push",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.String(255), nullable=False),
        sa.Column("auth", sa.String(255), nullable=False),
        sa.Column("dispositivo_nombre", sa.String(80)),
        sa.Column("user_agent", sa.String(160)),
        sa.Column("activa", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("mensajes", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("reservas", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("viaje", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("creada_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ultima_utilizacion_en", sa.DateTime(timezone=True)),
        sa.Column("revocada_en", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("endpoint", name="uq_suscripciones_push_endpoint"),
    )
    op.create_index("ix_suscripciones_push_usuario_id", "suscripciones_push", ["usuario_id"])


def downgrade() -> None:
    op.drop_table("suscripciones_push")
    op.drop_table("notificaciones")
