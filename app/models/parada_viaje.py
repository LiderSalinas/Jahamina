from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class ParadaViaje(Base):
    __tablename__ = "paradas_viaje"
    __table_args__ = (
        UniqueConstraint("viaje_id", "orden", name="uq_paradas_viaje_orden"),
        CheckConstraint("tipo IN ('origen','recogida','parada','descenso','destino')", name="ck_paradas_tipo"),
        CheckConstraint("estado IN ('pendiente','actual','completada','cancelada')", name="ck_paradas_estado"),
        Index("ix_paradas_viaje_estado", "viaje_id", "estado"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    viaje_id: Mapped[int] = mapped_column(ForeignKey("viajes.id", ondelete="CASCADE"), index=True)
    reserva_id: Mapped[int | None] = mapped_column(ForeignKey("solicitudes_viaje.id", ondelete="SET NULL"), index=True)
    orden: Mapped[int]
    tipo: Mapped[str] = mapped_column(String(20))
    nombre_publico: Mapped[str] = mapped_column(String(160))
    zona_general: Mapped[str | None] = mapped_column(String(160))
    latitud: Mapped[float | None] = mapped_column(Numeric(9, 6))
    longitud: Mapped[float | None] = mapped_column(Numeric(9, 6))
    hora_estimada: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hora_real: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente", server_default="pendiente")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    viaje = relationship("Viaje", back_populates="paradas")
    reserva = relationship("SolicitudViaje", back_populates="paradas")
