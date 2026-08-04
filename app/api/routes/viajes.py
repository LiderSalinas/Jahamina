from typing import List

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.db import get_db
from app.core.security import get_current_user
from app.core.redis import publish_chat_event, publish_roadmap_event
from app.models.mensaje import Mensaje
from app.models.solicitud_viaje import SolicitudViaje
from app.models.usuario import Usuario
from app.services import viaje_service
from app.schemas.solicitud_schema import SolicitudResponse
from app.schemas.chat_schema import MessageResponse
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
async def cancelar_viaje(
    viaje_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user)
):
    viaje = viaje_service.cancelar_viaje(db, viaje_id, usuario.id)
    timestamp = datetime.now(timezone.utc).isoformat()
    for event_type in ("trip.status.changed", "trip.event.created", "roadmap.updated"):
        await publish_roadmap_event(viaje.id, {"type": event_type, "data": {"viaje_id": viaje.id, "estado": "cancelado"}, "timestamp": timestamp})
    for request in db.scalars(select(SolicitudViaje).where(SolicitudViaje.viaje_id == viaje.id)):
        if not request.conversacion:
            continue
        message = db.scalar(select(Mensaje).where(
            Mensaje.conversacion_id == request.conversacion.id,
            Mensaje.client_message_id == f"system:trip:{viaje.id}:cancelled:request:{request.id}",
        ))
        if message:
            await publish_chat_event(request.conversacion.id, {"type": "message.created", "data": MessageResponse.model_validate(message).model_dump(mode="json"), "timestamp": timestamp})
    return viaje

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
