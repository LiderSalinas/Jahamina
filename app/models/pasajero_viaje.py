from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base

class ViajeUnido(Base):
    __tablename__ = "viajes_unidos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    viaje_id = Column(Integer, ForeignKey("viajes.id"), nullable=False)

    usuario = relationship("Usuario", back_populates="viajes_unidos")
    viaje = relationship("Viaje", back_populates="pasajeros")
