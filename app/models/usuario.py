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
