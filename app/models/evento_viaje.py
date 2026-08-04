from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class EventoViaje(Base):
    __tablename__ = "eventos_viaje"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_eventos_viaje_idempotency"),
        Index("ix_eventos_viaje_created", "viaje_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    viaje_id: Mapped[int] = mapped_column(ForeignKey("viajes.id", ondelete="CASCADE"), index=True)
    reserva_id: Mapped[int | None] = mapped_column(ForeignKey("solicitudes_viaje.id", ondelete="SET NULL"), index=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    tipo: Mapped[str] = mapped_column(String(50))
    descripcion_publica: Mapped[str] = mapped_column(Text)
    metadata_evento: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict, server_default="{}")
    idempotency_key: Mapped[str] = mapped_column(String(150))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    viaje = relationship("Viaje", back_populates="eventos")
    reserva = relationship("SolicitudViaje", back_populates="eventos_viaje")
    actor = relationship("Usuario", back_populates="eventos_viaje")
