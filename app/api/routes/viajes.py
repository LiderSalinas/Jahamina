from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.services import viaje_service
from app.schemas.solicitud_schema import SolicitudResponse
from app.schemas.viaje_schema import ViajeCreate, ViajeResponse

router = APIRouter()

@router.post(
    "/",
    response_model=ViajeResponse,
    status_code=status.HTTP_201_CREATED,
)
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

@router.put(
    "/unirse/{viaje_id}",
    response_model=SolicitudResponse,
    status_code=status.HTTP_201_CREATED,
    deprecated=True,
)
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


@router.patch("/{viaje_id}/iniciar", response_model=ViajeResponse)
def iniciar_viaje(
    viaje_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return viaje_service.cambiar_estado_viaje(
        db,
        viaje_id,
        usuario.id,
        "en_curso",
    )


@router.patch("/{viaje_id}/finalizar", response_model=ViajeResponse)
def finalizar_viaje(
    viaje_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return viaje_service.cambiar_estado_viaje(
        db,
        viaje_id,
        usuario.id,
        "finalizado",
    )
