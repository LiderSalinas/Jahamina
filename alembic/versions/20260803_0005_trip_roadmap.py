"""trip roadmap states, stops and events

Revision ID: 20260803_0005
Revises: 20260731_0004
"""
from alembic import op
import sqlalchemy as sa

revision = "20260803_0005"
down_revision = "20260731_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_viajes_estado", "viajes", type_="check")
    op.create_check_constraint(
        "ck_viajes_estado", "viajes",
        "estado IN ('publicado','completo','programado','preparando_salida','conductor_en_camino','conductor_en_punto','abordaje','en_curso','pausado','finalizado','cancelado')",
    )
    op.add_column("solicitudes_viaje", sa.Column("estado_pasajero", sa.String(20), server_default="confirmado", nullable=False))
    op.create_check_constraint(
        "ck_solicitudes_estado_pasajero", "solicitudes_viaje",
        "estado_pasajero IN ('confirmado','listo','esperando','recogido','abordo','completado','ausente','cancelado')",
    )
    op.create_table(
        "paradas_viaje",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("viaje_id", sa.Integer(), sa.ForeignKey("viajes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reserva_id", sa.Integer(), sa.ForeignKey("solicitudes_viaje.id", ondelete="SET NULL"), nullable=True),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("nombre_publico", sa.String(160), nullable=False),
        sa.Column("zona_general", sa.String(160), nullable=True),
        sa.Column("latitud", sa.Numeric(9, 6), nullable=True),
        sa.Column("longitud", sa.Numeric(9, 6), nullable=True),
        sa.Column("hora_estimada", sa.DateTime(timezone=True), nullable=True),
        sa.Column("hora_real", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estado", sa.String(20), server_default="pendiente", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("viaje_id", "orden", name="uq_paradas_viaje_orden"),
        sa.CheckConstraint("tipo IN ('origen','recogida','parada','descenso','destino')", name="ck_paradas_tipo"),
        sa.CheckConstraint("estado IN ('pendiente','actual','completada','cancelada')", name="ck_paradas_estado"),
    )
    op.create_index("ix_paradas_viaje_viaje_id", "paradas_viaje", ["viaje_id"])
    op.create_index("ix_paradas_viaje_reserva_id", "paradas_viaje", ["reserva_id"])
    op.create_index("ix_paradas_viaje_estado", "paradas_viaje", ["viaje_id", "estado"])
    op.create_table(
        "eventos_viaje",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("viaje_id", sa.Integer(), sa.ForeignKey("viajes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reserva_id", sa.Integer(), sa.ForeignKey("solicitudes_viaje.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("descripcion_publica", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("idempotency_key", sa.String(150), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_eventos_viaje_idempotency"),
    )
    op.create_index("ix_eventos_viaje_viaje_id", "eventos_viaje", ["viaje_id"])
    op.create_index("ix_eventos_viaje_reserva_id", "eventos_viaje", ["reserva_id"])
    op.create_index("ix_eventos_viaje_created", "eventos_viaje", ["viaje_id", "created_at"])


def downgrade() -> None:
    op.drop_table("eventos_viaje")
    op.drop_table("paradas_viaje")
    op.drop_constraint("ck_solicitudes_estado_pasajero", "solicitudes_viaje", type_="check")
    op.drop_column("solicitudes_viaje", "estado_pasajero")
    op.execute("UPDATE viajes SET estado='publicado' WHERE estado IN ('programado','preparando_salida','conductor_en_camino','conductor_en_punto','abordaje','pausado')")
    op.drop_constraint("ck_viajes_estado", "viajes", type_="check")
    op.create_check_constraint("ck_viajes_estado", "viajes", "estado IN ('publicado','completo','en_curso','finalizado','cancelado')")
