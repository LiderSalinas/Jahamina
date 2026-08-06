from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Notificacion(Base):
    __tablename__ = "notificaciones"
    __table_args__ = (
        UniqueConstraint("clave_idempotencia", name="uq_notificaciones_clave_idempotencia"),
        Index("ix_notificaciones_usuario_leida_creada", "usuario_id", "leida", "creada_en"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    tipo: Mapped[str] = mapped_column(String(40), nullable=False)
    titulo: Mapped[str] = mapped_column(String(120), nullable=False)
    cuerpo: Mapped[str] = mapped_column(String(300), nullable=False)
    reserva_id: Mapped[int | None] = mapped_column(ForeignKey("solicitudes_viaje.id"))
    viaje_id: Mapped[int | None] = mapped_column(ForeignKey("viajes.id"))
    conversacion_id: Mapped[int | None] = mapped_column(ForeignKey("conversaciones.id"))
    url_destino: Mapped[str] = mapped_column(String(300), nullable=False)
    leida: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    leida_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clave_idempotencia: Mapped[str] = mapped_column(String(180), nullable=False)

    usuario = relationship("Usuario", back_populates="notificaciones")


class SuscripcionPush(Base):
    __tablename__ = "suscripciones_push"
    __table_args__ = (UniqueConstraint("endpoint", name="uq_suscripciones_push_endpoint"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    p256dh: Mapped[str] = mapped_column(String(255), nullable=False)
    auth: Mapped[str] = mapped_column(String(255), nullable=False)
    dispositivo_nombre: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(160))
    activa: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    mensajes: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    reservas: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    viaje: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ultima_utilizacion_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revocada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    usuario = relationship("Usuario", back_populates="suscripciones_push")
