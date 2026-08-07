from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.vehiculo_schema import (
    VehiculoCreate,
    VehiculoResponse,
    VehiculoUpdate,
)
from app.services import media_service, vehiculo_service

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


def _media_http_error(error: media_service.MediaError) -> HTTPException:
    if isinstance(error, media_service.MediaValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))
    if isinstance(error, media_service.MediaConfigurationError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error))


@router.post("/{vehiculo_id}/imagen", response_model=VehiculoResponse)
async def upload_vehicle_image(
    vehiculo_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    vehiculo = vehiculo_service.obtener_vehiculo(db, vehiculo_id, usuario.id)
    try:
        previous_public_id = vehiculo.imagen_public_id
        asset = await media_service.upload_image(file, owner="vehicles", owner_id=vehiculo.id)
        vehiculo.imagen_url = asset.secure_url
        vehiculo.imagen_public_id = asset.public_id
    except media_service.MediaError as error:
        raise _media_http_error(error) from error
    db.commit()
    db.refresh(vehiculo)
    if previous_public_id and previous_public_id != vehiculo.imagen_public_id:
        try:
            await media_service.delete_image(public_id=previous_public_id)
        except media_service.MediaError:
            pass
    return vehiculo


@router.delete("/{vehiculo_id}/imagen", response_model=VehiculoResponse)
async def delete_vehicle_image(
    vehiculo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    vehiculo = vehiculo_service.obtener_vehiculo(db, vehiculo_id, usuario.id)
    previous_public_id = vehiculo.imagen_public_id
    vehiculo.imagen_url = None
    vehiculo.imagen_public_id = None
    db.commit()
    db.refresh(vehiculo)
    if previous_public_id:
        try:
            await media_service.delete_image(public_id=previous_public_id)
        except media_service.MediaError:
            pass
    return vehiculo
