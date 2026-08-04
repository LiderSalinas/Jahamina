"""add explicit passenger arrival state

Revision ID: 20260804_0006
Revises: 20260803_0005
"""
from alembic import op

revision = "20260804_0006"
down_revision = "20260803_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_solicitudes_estado_pasajero", "solicitudes_viaje", type_="check")
    op.create_check_constraint(
        "ck_solicitudes_estado_pasajero", "solicitudes_viaje",
        "estado_pasajero IN ('confirmado','listo','esperando','llego_al_punto','recogido','abordo','completado','ausente','cancelado')",
    )


def downgrade() -> None:
    op.execute("UPDATE solicitudes_viaje SET estado_pasajero='esperando' WHERE estado_pasajero='llego_al_punto'")
    op.drop_constraint("ck_solicitudes_estado_pasajero", "solicitudes_viaje", type_="check")
    op.create_check_constraint(
        "ck_solicitudes_estado_pasajero", "solicitudes_viaje",
        "estado_pasajero IN ('confirmado','listo','esperando','recogido','abordo','completado','ausente','cancelado')",
    )
