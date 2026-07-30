"""Vehículos, cupos y solicitudes de viaje.

Revision ID: 20260729_0002
Revises: 20260729_0001
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0002"
down_revision: str | None = "20260729_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vehiculos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("propietario_id", sa.Integer(), nullable=False),
        sa.Column("marca", sa.String(80), nullable=False),
        sa.Column("modelo", sa.String(80), nullable=False),
        sa.Column("color", sa.String(50), nullable=False),
        sa.Column("matricula", sa.String(20), nullable=False),
        sa.Column("capacidad", sa.Integer(), nullable=False),
        sa.Column(
            "activo",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "capacidad BETWEEN 1 AND 8",
            name="ck_vehiculos_capacidad",
        ),
        sa.ForeignKeyConstraint(["propietario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehiculos_id", "vehiculos", ["id"])
    op.create_index(
        "ix_vehiculos_propietario_id",
        "vehiculos",
        ["propietario_id"],
    )
    op.create_index(
        "ix_vehiculos_matricula",
        "vehiculos",
        ["matricula"],
        unique=True,
    )

    op.add_column("viajes", sa.Column("vehiculo_id", sa.Integer()))
    op.add_column(
        "viajes",
        sa.Column("cupos_totales", sa.Integer(), server_default="1"),
    )
    op.add_column(
        "viajes",
        sa.Column("cupos_disponibles", sa.Integer(), server_default="1"),
    )
    op.add_column("viajes", sa.Column("descripcion", sa.Text()))
    op.add_column("viajes", sa.Column("punto_salida", sa.String(200)))
    op.add_column("viajes", sa.Column("punto_llegada", sa.String(200)))
    op.add_column("viajes", sa.Column("origen_latitud", sa.Numeric(9, 6)))
    op.add_column("viajes", sa.Column("origen_longitud", sa.Numeric(9, 6)))
    op.add_column("viajes", sa.Column("destino_latitud", sa.Numeric(9, 6)))
    op.add_column("viajes", sa.Column("destino_longitud", sa.Numeric(9, 6)))
    op.add_column(
        "viajes",
        sa.Column("estado", sa.String(20), server_default="publicado"),
    )
    op.add_column(
        "viajes",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.execute(
        """
        UPDATE viajes
        SET punto_salida = origen,
            punto_llegada = destino,
            estado = CASE WHEN cancelado THEN 'cancelado' ELSE 'publicado' END
        """
    )
    op.alter_column("viajes", "cupos_totales", nullable=False)
    op.alter_column("viajes", "cupos_disponibles", nullable=False)
    op.alter_column("viajes", "punto_salida", nullable=False)
    op.alter_column("viajes", "punto_llegada", nullable=False)
    op.alter_column("viajes", "estado", nullable=False)
    op.alter_column("viajes", "updated_at", nullable=False)
    op.create_foreign_key(
        "fk_viajes_vehiculo_id",
        "viajes",
        "vehiculos",
        ["vehiculo_id"],
        ["id"],
    )
    op.create_index("ix_viajes_vehiculo_id", "viajes", ["vehiculo_id"])
    op.create_check_constraint(
        "ck_viajes_cupos",
        "viajes",
        "cupos_totales BETWEEN 1 AND 8 AND "
        "cupos_disponibles BETWEEN 0 AND cupos_totales",
    )
    op.create_check_constraint(
        "ck_viajes_estado",
        "viajes",
        "estado IN ('publicado','completo','en_curso','finalizado','cancelado')",
    )

    op.create_table(
        "solicitudes_viaje",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("viaje_id", sa.Integer(), nullable=False),
        sa.Column("pasajero_id", sa.Integer(), nullable=False),
        sa.Column(
            "estado",
            sa.String(20),
            server_default="pendiente",
            nullable=False,
        ),
        sa.Column("mensaje_inicial", sa.Text()),
        sa.Column("punto_encuentro_propuesto", sa.String(200)),
        sa.Column("punto_encuentro_latitud", sa.Numeric(9, 6)),
        sa.Column("punto_encuentro_longitud", sa.Numeric(9, 6)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "estado IN "
            "('pendiente','aceptada','rechazada','cancelada','finalizada')",
            name="ck_solicitudes_estado",
        ),
        sa.ForeignKeyConstraint(["pasajero_id"], ["usuarios.id"]),
        sa.ForeignKeyConstraint(["viaje_id"], ["viajes.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_solicitudes_viaje_id",
        "solicitudes_viaje",
        ["id"],
    )
    op.create_index(
        "ix_solicitudes_viaje_viaje_id",
        "solicitudes_viaje",
        ["viaje_id"],
    )
    op.create_index(
        "ix_solicitudes_viaje_pasajero_id",
        "solicitudes_viaje",
        ["pasajero_id"],
    )
    op.create_index(
        "uq_solicitud_activa_pasajero_viaje",
        "solicitudes_viaje",
        ["viaje_id", "pasajero_id"],
        unique=True,
        postgresql_where=sa.text("estado IN ('pendiente', 'aceptada')"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_solicitud_activa_pasajero_viaje",
        table_name="solicitudes_viaje",
    )
    op.drop_index(
        "ix_solicitudes_viaje_pasajero_id",
        table_name="solicitudes_viaje",
    )
    op.drop_index(
        "ix_solicitudes_viaje_viaje_id",
        table_name="solicitudes_viaje",
    )
    op.drop_index(
        "ix_solicitudes_viaje_id",
        table_name="solicitudes_viaje",
    )
    op.drop_table("solicitudes_viaje")

    op.drop_constraint("ck_viajes_estado", "viajes", type_="check")
    op.drop_constraint("ck_viajes_cupos", "viajes", type_="check")
    op.drop_index("ix_viajes_vehiculo_id", table_name="viajes")
    op.drop_constraint(
        "fk_viajes_vehiculo_id",
        "viajes",
        type_="foreignkey",
    )
    for column in (
        "updated_at",
        "estado",
        "destino_longitud",
        "destino_latitud",
        "origen_longitud",
        "origen_latitud",
        "punto_llegada",
        "punto_salida",
        "descripcion",
        "cupos_disponibles",
        "cupos_totales",
        "vehiculo_id",
    ):
        op.drop_column("viajes", column)

    op.drop_index("ix_vehiculos_matricula", table_name="vehiculos")
    op.drop_index("ix_vehiculos_propietario_id", table_name="vehiculos")
    op.drop_index("ix_vehiculos_id", table_name="vehiculos")
    op.drop_table("vehiculos")
