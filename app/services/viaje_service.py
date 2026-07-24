from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.viaje_model import Viaje
from app.models.pasajero_viaje import ViajeUnido
from app.schemas.viaje_schema import ViajeCreate
from datetime import datetime

def crear_viaje(db: Session, viaje_data: ViajeCreate, usuario_id: int):
    nuevo_viaje = Viaje(**viaje_data.dict(), creador_id=usuario_id)
    db.add(nuevo_viaje)
    db.commit()
    db.refresh(nuevo_viaje)
    return nuevo_viaje

def obtener_viajes_disponibles(db: Session):
    return db.query(Viaje).filter(Viaje.cancelado == False).all()

def obtener_mis_viajes(db: Session, usuario_id: int):
    return db.query(Viaje).filter(Viaje.creador_id == usuario_id).all()

def cancelar_viaje(db: Session, viaje_id: int, usuario_id: int):
    viaje = db.query(Viaje).filter(Viaje.id == viaje_id, Viaje.creador_id == usuario_id).first()
    if not viaje:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    viaje.cancelado = True
    db.commit()
    return viaje

def unirse_a_viaje(db: Session, viaje_id: int, usuario_id: int):
    viaje = db.query(Viaje).filter(Viaje.id == viaje_id, Viaje.cancelado == False).first()
    if not viaje:
        raise HTTPException(status_code=404, detail="Viaje no disponible o fue cancelado")

    ya_unido = db.query(ViajeUnido).filter(
        ViajeUnido.viaje_id == viaje_id,
        ViajeUnido.usuario_id == usuario_id
    ).first()

    if ya_unido:
        raise HTTPException(status_code=400, detail="Ya estás unido a este viaje")

    nuevo_registro = ViajeUnido(viaje_id=viaje_id, usuario_id=usuario_id)
    db.add(nuevo_registro)
    db.commit()
    db.refresh(nuevo_registro)
    return nuevo_registro

def obtener_viajes_unidos(db: Session, usuario_id: int):
    return (
        db.query(Viaje)
        .join(ViajeUnido)
        .filter(ViajeUnido.usuario_id == usuario_id)
        .filter(Viaje.cancelado == False)
        .all()
    )
