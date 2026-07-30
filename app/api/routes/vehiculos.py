from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.vehiculo_schema import (
    VehiculoCreate,
    VehiculoResponse,
    VehiculoUpdate,
)
from app.services import vehiculo_service

router = APIRouter()


@router.post(
    "",
    response_model=VehiculoResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_vehiculo(
    data: VehiculoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return vehiculo_service.crear_vehiculo(db, data, usuario.id)


@router.get("", response_model=list[VehiculoResponse])
def listar_vehiculos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return vehiculo_service.listar_vehiculos(db, usuario.id)


@router.get("/{vehiculo_id}", response_model=VehiculoResponse)
def obtener_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return vehiculo_service.obtener_vehiculo(db, vehiculo_id, usuario.id)


@router.patch("/{vehiculo_id}", response_model=VehiculoResponse)
def actualizar_vehiculo(
    vehiculo_id: int,
    data: VehiculoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return vehiculo_service.actualizar_vehiculo(
        db,
        vehiculo_id,
        usuario.id,
        data,
    )


@router.patch("/{vehiculo_id}/desactivar", response_model=VehiculoResponse)
def desactivar_vehiculo(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return vehiculo_service.desactivar_vehiculo(
        db,
        vehiculo_id,
        usuario.id,
    )
