from sqlalchemy.orm import Session

from app.schemas.viaje_schema import ViajeCreate
from app.services.viaje_service import crear_viaje as crear_viaje_service


def crear_viaje(db: Session, viaje: ViajeCreate, usuario_id: int):
    return crear_viaje_service(db, viaje, usuario_id)
