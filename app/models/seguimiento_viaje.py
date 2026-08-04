from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class SeguimientoViaje(Base):
    __tablename__ = "seguimientos_viaje"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('inactivo','activo','pausado','finalizado','cancelado')",
            name="ck_seguimientos_estado",
        ),
        Index(
            "uq_seguimiento_activo_viaje",
            "viaje_id",
            unique=True,
            postgresql_where=text("estado IN ('activo','pausado')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    viaje_id: Mapped[int] = mapped_column(ForeignKey("viajes.id"), nullable=False, index=True)
    conductor_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(20), default="inactivo", server_default="inactivo", nullable=False)
    iniciado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pausado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finalizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultima_latitud: Mapped[float | None] = mapped_column(Numeric(9, 6))
    ultima_longitud: Mapped[float | None] = mapped_column(Numeric(9, 6))
    ultima_precision_metros: Mapped[float | None] = mapped_column(Numeric(8, 2))
    ultima_velocidad_mps: Mapped[float | None] = mapped_column(Numeric(8, 2))
    ultima_direccion_grados: Mapped[float | None] = mapped_column(Numeric(6, 2))
    ultima_actualizacion_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    compartir_ubicacion: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    viaje = relationship("Viaje", back_populates="seguimientos")
    conductor = relationship("Usuario")
