from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class SolicitudViaje(Base):
    __tablename__ = "solicitudes_viaje"
    __table_args__ = (
        CheckConstraint(
            "estado IN "
            "('pendiente','aceptada','rechazada','cancelada','finalizada')",
            name="ck_solicitudes_estado",
        ),
        CheckConstraint(
            "estado_punto_encuentro IN "
            "('sin_definir','propuesto','confirmado','rechazado','reemplazado')",
            name="ck_solicitudes_punto_estado",
        ),
        Index(
            "uq_solicitud_activa_pasajero_viaje",
            "viaje_id",
            "pasajero_id",
            unique=True,
            postgresql_where=text("estado IN ('pendiente', 'aceptada')"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    viaje_id: Mapped[int] = mapped_column(
        ForeignKey("viajes.id"),
        nullable=False,
        index=True,
    )
    pasajero_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id"),
        nullable=False,
        index=True,
    )
    estado: Mapped[str] = mapped_column(
        String(20),
        default="pendiente",
        server_default="pendiente",
        nullable=False,
    )
    mensaje_inicial: Mapped[str | None] = mapped_column(Text)
    punto_encuentro_propuesto: Mapped[str | None] = mapped_column(String(200))
    punto_encuentro_latitud: Mapped[float | None] = mapped_column(
        Numeric(9, 6)
    )
    punto_encuentro_longitud: Mapped[float | None] = mapped_column(
        Numeric(9, 6)
    )
    estado_punto_encuentro: Mapped[str] = mapped_column(
        String(20), default="sin_definir", server_default="sin_definir", nullable=False
    )
    propuesto_por_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    propuesto_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmado_por_conductor_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confirmado_por_pasajero_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    punto_encuentro_actualizado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    viaje = relationship("Viaje", back_populates="solicitudes")
    pasajero = relationship(
        "Usuario",
        back_populates="solicitudes_viaje",
        foreign_keys=[pasajero_id],
    )
    conversacion = relationship(
        "Conversacion", back_populates="solicitud", uselist=False
    )
