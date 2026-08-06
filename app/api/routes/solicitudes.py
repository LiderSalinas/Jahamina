from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.solicitud_schema import (
    ReservaRelacionadaResponse,
    SolicitudCreate,
    SolicitudResponse,
)
from app.services import solicitud_service
from app.services import notification_service

router = APIRouter()


@router.post(
    "/viajes/{viaje_id}/solicitudes",
    response_model=SolicitudResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crear_solicitud(
    viaje_id: int,
    data: SolicitudCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    solicitud = solicitud_service.crear_solicitud(db, viaje_id, usuario.id, data)
    await notification_service.notify(
        db, user_id=solicitud.viaje.creador_id, actor_id=usuario.id,
        notification_type="solicitud_nueva", title="Nueva solicitud de lugar",
        body=f"{usuario.nombre} quiere sumarse a tu viaje.",
        idempotency_key=f"request:{solicitud.id}:created", destination_url=f"/reservas/{solicitud.id}",
        reservation_id=solicitud.id, trip_id=solicitud.viaje_id,
    )
    return solicitud


@router.get("/solicitudes/mias", response_model=list[SolicitudResponse])
def listar_mis_solicitudes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return solicitud_service.listar_mias(db, usuario.id)


@router.get(
    "/reservas/relacionadas",
    response_model=list[ReservaRelacionadaResponse],
)
def listar_reservas_relacionadas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    return solicitud_service.listar_relacionadas(db, usuario.id)


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
async def aceptar_solicitud(
    solicitud_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    solicitud = solicitud_service.responder_solicitud(
        db,
        solicitud_id,
        usuario.id,
        True,
    )
    await notification_service.notify(
        db, user_id=solicitud.pasajero_id, actor_id=usuario.id,
        notification_type="solicitud_aceptada", title="Solicitud aceptada",
        body="Tu lugar fue confirmado. Ya podés coordinar el viaje.",
        idempotency_key=f"request:{solicitud.id}:accepted", destination_url=f"/reservas/{solicitud.id}",
        reservation_id=solicitud.id, trip_id=solicitud.viaje_id,
        conversation_id=solicitud.conversacion.id if solicitud.conversacion else None,
    )
    return solicitud


@router.patch(
    "/solicitudes/{solicitud_id}/rechazar",
    response_model=SolicitudResponse,
)
async def rechazar_solicitud(
    solicitud_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    solicitud = solicitud_service.responder_solicitud(
        db,
        solicitud_id,
        usuario.id,
        False,
    )
    await notification_service.notify(
        db, user_id=solicitud.pasajero_id, actor_id=usuario.id,
        notification_type="solicitud_rechazada", title="Solicitud no aceptada",
        body="El conductor no pudo aceptar tu solicitud para este viaje.",
        idempotency_key=f"request:{solicitud.id}:rejected", destination_url="/reservas",
        reservation_id=solicitud.id, trip_id=solicitud.viaje_id,
    )
    return solicitud


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
