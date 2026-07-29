from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base

class Viaje(Base):
    __tablename__ = "viajes"

    id = Column(Integer, primary_key=True, index=True)
    origen = Column(String, nullable=False)
    destino = Column(String, nullable=False)
    fecha = Column(DateTime, nullable=False)
    creador_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    cancelado = Column(Boolean, nullable=False, default=False)

    creador = relationship("Usuario", back_populates="viajes")
    pasajeros = relationship("ViajeUnido", back_populates="viaje", cascade="all, delete-orphan")
