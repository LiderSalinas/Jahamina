from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.solicitud_schema import SolicitudCreate, SolicitudResponse
from app.services import solicitud_service

router = APIRouter()


@router.post(
    "/viajes/{viaje_id}/solicitudes",
    response_model=SolicitudResponse,
    status_code=status.HTTP_201_CREATED,
)
def crear_solicitud(
    viaje_id: int,
    data: SolicitudCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return solicitud_service.crear_solicitud(db, viaje_id, usuario.id, data)


@router.get("/solicitudes/mias", response_model=list[SolicitudResponse])
def listar_mis_solicitudes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return solicitud_service.listar_mias(db, usuario.id)


@router.get(
    "/viajes/{viaje_id}/solicitudes",
    response_model=list[SolicitudResponse],
)
def listar_solicitudes_viaje(
    viaje_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return solicitud_service.listar_del_viaje(db, viaje_id, usuario.id)


@router.get(
    "/solicitudes/{solicitud_id}",
    response_model=SolicitudResponse,
)
def obtener_solicitud(
    solicitud_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return solicitud_service.obtener_solicitud(db, solicitud_id, usuario.id)


@router.patch(
    "/solicitudes/{solicitud_id}/aceptar",
    response_model=SolicitudResponse,
)
def aceptar_solicitud(
    solicitud_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return solicitud_service.responder_solicitud(
        db,
        solicitud_id,
        usuario.id,
        True,
    )


@router.patch(
    "/solicitudes/{solicitud_id}/rechazar",
    response_model=SolicitudResponse,
)
def rechazar_solicitud(
    solicitud_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return solicitud_service.responder_solicitud(
        db,
        solicitud_id,
        usuario.id,
        False,
    )


@router.patch(
    "/solicitudes/{solicitud_id}/cancelar",
    response_model=SolicitudResponse,
)
def cancelar_solicitud(
    solicitud_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return solicitud_service.cancelar_solicitud(
        db,
        solicitud_id,
        usuario.id,
    )
