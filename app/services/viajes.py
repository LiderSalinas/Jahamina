from sqlalchemy.orm import Session
from app.models.viaje_model import Viaje
from app.schemas.viaje_schema import ViajeCreate


def crear_viaje(db: Session, viaje: ViajeCreate, conductor: str):
    nuevo_viaje = Viaje(**viaje.model_dump(), conductor=conductor)
    db.add(nuevo_viaje)
    db.commit()
    db.refresh(nuevo_viaje)
    return nuevo_viaje
