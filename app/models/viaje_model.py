from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.db import Base

class Viaje(Base):
    __tablename__ = "viajes"
    __table_args__ = (
        CheckConstraint(
            "cupos_totales BETWEEN 1 AND 8 AND "
            "cupos_disponibles BETWEEN 0 AND cupos_totales",
            name="ck_viajes_cupos",
        ),
        CheckConstraint(
            "estado IN "
            "('publicado','completo','en_curso','finalizado','cancelado')",
            name="ck_viajes_estado",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    origen = Column(String, nullable=False)
    destino = Column(String, nullable=False)
    fecha = Column(DateTime, nullable=False)
    creador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    cancelado = Column(Boolean, nullable=False, default=False)
    vehiculo_id = Column(
        Integer,
        ForeignKey("vehiculos.id"),
        nullable=True,
        index=True,
    )
    cupos_totales = Column(Integer, nullable=False, default=1)
    cupos_disponibles = Column(Integer, nullable=False, default=1)
    descripcion = Column(Text, nullable=True)
    punto_salida = Column(String(200), nullable=False)
    punto_llegada = Column(String(200), nullable=False)
    origen_latitud = Column(Numeric(9, 6), nullable=True)
    origen_longitud = Column(Numeric(9, 6), nullable=True)
    destino_latitud = Column(Numeric(9, 6), nullable=True)
    destino_longitud = Column(Numeric(9, 6), nullable=True)
    estado = Column(String(20), nullable=False, default="publicado")
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    creador = relationship("Usuario", back_populates="viajes")
    pasajeros = relationship("ViajeUnido", back_populates="viaje", cascade="all, delete-orphan")
    vehiculo = relationship("Vehiculo", back_populates="viajes")
    solicitudes = relationship(
        "SolicitudViaje",
        back_populates="viaje",
        cascade="all, delete-orphan",
    )
