from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.services import viaje_service
from app.schemas.viaje_schema import ViajeCreate, ViajeResponse, ViajeUnidoResponse

router = APIRouter()

@router.post("/", response_model=ViajeResponse)
def crear_viaje(
    viaje_data: ViajeCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    return viaje_service.crear_viaje(db, viaje_data, usuario.id)

@router.get("/disponibles", response_model=List[ViajeResponse])
def obtener_viajes_disponibles(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return viaje_service.obtener_viajes_disponibles(db)

@router.get("/mis-viajes", response_model=List[ViajeResponse])
def obtener_mis_viajes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    return viaje_service.obtener_mis_viajes(db, usuario.id)

@router.put("/cancelar/{viaje_id}", response_model=ViajeResponse)
def cancelar_viaje(
    viaje_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    return viaje_service.cancelar_viaje(db, viaje_id, usuario.id)

@router.put("/unirse/{viaje_id}", response_model=ViajeUnidoResponse)
def unirse_a_viaje(
    viaje_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    return viaje_service.unirse_a_viaje(db, viaje_id, usuario.id)

@router.get("/unidos", response_model=List[ViajeResponse])
def ver_viajes_unidos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    return viaje_service.obtener_viajes_unidos(db, usuario.id)
