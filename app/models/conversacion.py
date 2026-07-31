from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Conversacion(Base):
    __tablename__ = "conversaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    solicitud_id: Mapped[int] = mapped_column(
        ForeignKey("solicitudes_viaje.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    ultimo_mensaje_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    cerrada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activa: Mapped[bool] = mapped_column(
        Boolean, server_default="true", default=True, nullable=False
    )

    solicitud = relationship("SolicitudViaje", back_populates="conversacion")
    mensajes = relationship(
        "Mensaje", back_populates="conversacion", order_by="Mensaje.id"
    )
