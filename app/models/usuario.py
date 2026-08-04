from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.db import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    viajes = relationship("Viaje", back_populates="creador")
    viajes_unidos = relationship("ViajeUnido", back_populates="usuario", cascade="all, delete-orphan")
    vehiculos = relationship(
        "Vehiculo",
        back_populates="propietario",
        cascade="all, delete-orphan",
    )
    solicitudes_viaje = relationship(
        "SolicitudViaje",
        back_populates="pasajero",
        foreign_keys="SolicitudViaje.pasajero_id",
    )
    mensajes_chat = relationship("Mensaje", back_populates="remitente")
