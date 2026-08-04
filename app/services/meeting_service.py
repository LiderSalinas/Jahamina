from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.solicitud_viaje import SolicitudViaje
from app.schemas.meeting_schema import MeetingPointProposal, MeetingPointResponse
from app.services.chat_service import add_system_message


def _authorized(db: Session, request_id: int, user_id: int) -> SolicitudViaje:
    request = db.get(SolicitudViaje, request_id)
    if not request or user_id not in {request.pasajero_id, request.viaje.creador_id}:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    if request.estado != "aceptada":
        raise HTTPException(status_code=409, detail="La reserva no está aceptada")
    return request


def _response(request: SolicitudViaje) -> MeetingPointResponse:
    return MeetingPointResponse(
        reserva_id=request.id,
        texto=request.punto_encuentro_propuesto,
        latitude=float(request.punto_encuentro_latitud) if request.punto_encuentro_latitud is not None else None,
        longitude=float(request.punto_encuentro_longitud) if request.punto_encuentro_longitud is not None else None,
        estado=request.estado_punto_encuentro,
        propuesto_por_id=request.propuesto_por_id,
        propuesto_en=request.propuesto_en,
        confirmado_por_conductor_en=request.confirmado_por_conductor_en,
        confirmado_por_pasajero_en=request.confirmado_por_pasajero_en,
        actualizado_en=request.punto_encuentro_actualizado_en,
    )


def get(db: Session, request_id: int, user_id: int) -> MeetingPointResponse:
    return _response(_authorized(db, request_id, user_id))


def propose(db: Session, request_id: int, user_id: int, data: MeetingPointProposal) -> MeetingPointResponse:
    request = _authorized(db, request_id, user_id)
    if request.viaje.estado in {"en_curso", "finalizado", "cancelado"}:
        raise HTTPException(status_code=409, detail="El viaje ya no permite cambiar el punto")
    now = datetime.now(timezone.utc)
    request.punto_encuentro_propuesto = data.texto
    request.punto_encuentro_latitud = data.latitude
    request.punto_encuentro_longitud = data.longitude
    request.estado_punto_encuentro = "propuesto"
    request.propuesto_por_id = user_id
    request.propuesto_en = now
    request.punto_encuentro_actualizado_en = now
    request.confirmado_por_conductor_en = now if user_id == request.viaje.creador_id else None
    request.confirmado_por_pasajero_en = now if user_id == request.pasajero_id else None
    if request.conversacion:
        add_system_message(db, request.conversacion, f"Se propuso el punto de encuentro: {data.texto}.", f"system:meeting:{request.id}:proposal:{now.isoformat()}")
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return _response(request)


def confirm(db: Session, request_id: int, user_id: int) -> MeetingPointResponse:
    request = _authorized(db, request_id, user_id)
    if request.estado_punto_encuentro not in {"propuesto", "confirmado"}:
        raise HTTPException(status_code=409, detail="No existe un punto por confirmar")
    now = datetime.now(timezone.utc)
    if user_id == request.viaje.creador_id:
        request.confirmado_por_conductor_en = request.confirmado_por_conductor_en or now
    else:
        request.confirmado_por_pasajero_en = request.confirmado_por_pasajero_en or now
    if request.confirmado_por_conductor_en and request.confirmado_por_pasajero_en:
        request.estado_punto_encuentro = "confirmado"
        if request.conversacion:
            add_system_message(db, request.conversacion, "El punto de encuentro quedó confirmado.", f"system:meeting:{request.id}:confirmed")
    request.punto_encuentro_actualizado_en = now
    db.commit()
    return _response(request)


def reject(db: Session, request_id: int, user_id: int) -> MeetingPointResponse:
    request = _authorized(db, request_id, user_id)
    request.estado_punto_encuentro = "rechazado"
    request.punto_encuentro_actualizado_en = datetime.now(timezone.utc)
    db.commit()
    return _response(request)
