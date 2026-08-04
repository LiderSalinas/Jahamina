"""Mapas, punto de encuentro y seguimiento.

Revision ID: 20260731_0004
Revises: 20260730_0003
"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op

revision: str = "20260731_0004"
down_revision: str | None = "20260730_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for name, type_ in (
        ("punto_salida_latitud", sa.Numeric(9, 6)),
        ("punto_salida_longitud", sa.Numeric(9, 6)),
        ("punto_llegada_latitud", sa.Numeric(9, 6)),
        ("punto_llegada_longitud", sa.Numeric(9, 6)),
        ("distancia_estimada_km", sa.Numeric(8, 2)),
        ("duracion_estimada_minutos", sa.Integer()),
        ("ruta_codificada", sa.Text()),
    ):
        op.add_column("viajes", sa.Column(name, type_))

    op.add_column("solicitudes_viaje", sa.Column("estado_punto_encuentro", sa.String(20), server_default="sin_definir", nullable=False))
    op.add_column("solicitudes_viaje", sa.Column("propuesto_por_id", sa.Integer()))
    op.add_column("solicitudes_viaje", sa.Column("propuesto_en", sa.DateTime(timezone=True)))
    op.add_column("solicitudes_viaje", sa.Column("confirmado_por_conductor_en", sa.DateTime(timezone=True)))
    op.add_column("solicitudes_viaje", sa.Column("confirmado_por_pasajero_en", sa.DateTime(timezone=True)))
    op.add_column("solicitudes_viaje", sa.Column("punto_encuentro_actualizado_en", sa.DateTime(timezone=True)))
    op.create_foreign_key("fk_solicitud_propuesto_por", "solicitudes_viaje", "usuarios", ["propuesto_por_id"], ["id"])
    op.create_check_constraint("ck_solicitudes_punto_estado", "solicitudes_viaje", "estado_punto_encuentro IN ('sin_definir','propuesto','confirmado','rechazado','reemplazado')")

    op.create_table(
        "seguimientos_viaje",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("viaje_id", sa.Integer(), nullable=False),
        sa.Column("conductor_id", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(20), server_default="inactivo", nullable=False),
        sa.Column("iniciado_en", sa.DateTime(timezone=True)),
        sa.Column("pausado_en", sa.DateTime(timezone=True)),
        sa.Column("finalizado_en", sa.DateTime(timezone=True)),
        sa.Column("ultima_latitud", sa.Numeric(9, 6)),
        sa.Column("ultima_longitud", sa.Numeric(9, 6)),
        sa.Column("ultima_precision_metros", sa.Numeric(8, 2)),
        sa.Column("ultima_velocidad_mps", sa.Numeric(8, 2)),
        sa.Column("ultima_direccion_grados", sa.Numeric(6, 2)),
        sa.Column("ultima_actualizacion_en", sa.DateTime(timezone=True)),
        sa.Column("compartir_ubicacion", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("estado IN ('inactivo','activo','pausado','finalizado','cancelado')", name="ck_seguimientos_estado"),
        sa.ForeignKeyConstraint(["viaje_id"], ["viajes.id"]),
        sa.ForeignKeyConstraint(["conductor_id"], ["usuarios.id"]),
    )
    op.create_index("ix_seguimientos_viaje_viaje_id", "seguimientos_viaje", ["viaje_id"])
    op.create_index("ix_seguimientos_viaje_conductor_id", "seguimientos_viaje", ["conductor_id"])
    op.create_index("uq_seguimiento_activo_viaje", "seguimientos_viaje", ["viaje_id"], unique=True, postgresql_where=sa.text("estado IN ('activo','pausado')"))


def downgrade() -> None:
    op.drop_index("uq_seguimiento_activo_viaje", table_name="seguimientos_viaje")
    op.drop_index("ix_seguimientos_viaje_conductor_id", table_name="seguimientos_viaje")
    op.drop_index("ix_seguimientos_viaje_viaje_id", table_name="seguimientos_viaje")
    op.drop_table("seguimientos_viaje")
    op.drop_constraint("ck_solicitudes_punto_estado", "solicitudes_viaje", type_="check")
    op.drop_constraint("fk_solicitud_propuesto_por", "solicitudes_viaje", type_="foreignkey")
    for column in ("punto_encuentro_actualizado_en", "confirmado_por_pasajero_en", "confirmado_por_conductor_en", "propuesto_en", "propuesto_por_id", "estado_punto_encuentro"):
        op.drop_column("solicitudes_viaje", column)
    for column in ("ruta_codificada", "duracion_estimada_minutos", "distancia_estimada_km", "punto_llegada_longitud", "punto_llegada_latitud", "punto_salida_longitud", "punto_salida_latitud"):
        op.drop_column("viajes", column)
