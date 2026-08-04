import json
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.redis import enforce_rate_limit, get_redis_client
from app.core.settings import settings
from app.models.seguimiento_viaje import SeguimientoViaje
from app.models.solicitud_viaje import SolicitudViaje
from app.models.viaje_model import Viaje
from app.schemas.tracking_schema import CurrentLocation, LocationUpdate
from app.services.chat_service import add_system_message


def _system_for_trip(db: Session, trip: Viaje, content: str, event: str) -> None:
    for request in trip.solicitudes:
        if request.conversacion and request.estado == "aceptada":
            add_system_message(
                db,
                request.conversacion,
                content,
                f"system:tracking:{trip.id}:{event}:request:{request.id}",
            )


def can_view(db: Session, trip: Viaje, user_id: int) -> bool:
    if trip.creador_id == user_id:
        return True
    return db.scalar(
        select(SolicitudViaje.id).where(
            SolicitudViaje.viaje_id == trip.id,
            SolicitudViaje.pasajero_id == user_id,
            SolicitudViaje.estado == "aceptada",
        )
    ) is not None


def authorized_trip(db: Session, trip_id: int, user_id: int) -> Viaje:
    trip = db.get(Viaje, trip_id)
    if not trip or not can_view(db, trip, user_id):
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    return trip


def current_session(db: Session, trip_id: int) -> SeguimientoViaje | None:
    return db.scalar(
        select(SeguimientoViaje)
        .where(SeguimientoViaje.viaje_id == trip_id)
        .order_by(SeguimientoViaje.id.desc())
        .limit(1)
    )


def start(db: Session, trip_id: int, user_id: int) -> SeguimientoViaje:
    trip = db.get(Viaje, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    if trip.creador_id != user_id:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    if trip.estado not in {"conductor_en_camino", "conductor_en_punto", "abordaje", "en_curso", "pausado"}:
        raise HTTPException(status_code=409, detail="El viaje no puede iniciar seguimiento")
    existing = current_session(db, trip_id)
    if existing and existing.estado in {"activo", "pausado"}:
        raise HTTPException(status_code=409, detail="Ya existe un seguimiento activo")
    now = datetime.now(timezone.utc)
    tracking = SeguimientoViaje(viaje_id=trip_id, conductor_id=user_id, estado="activo", iniciado_en=now, compartir_ubicacion=False)
    try:
        db.add(tracking)
        db.commit()
        db.refresh(tracking)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un seguimiento activo") from error
    return tracking


def transition(db: Session, trip_id: int, user_id: int, action: str) -> SeguimientoViaje:
    trip = db.get(Viaje, trip_id)
    if not trip or trip.creador_id != user_id:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    tracking = current_session(db, trip_id)
    if not tracking:
        raise HTTPException(status_code=404, detail="Seguimiento no encontrado")
    now = datetime.now(timezone.utc)
    if action == "pausar" and tracking.estado == "activo":
        tracking.estado, tracking.pausado_en = "pausado", now
        _system_for_trip(db, trip, "El conductor pausó la ubicación.", "paused")
    elif action == "reanudar" and tracking.estado == "pausado":
        tracking.estado, tracking.pausado_en = "activo", None
        _system_for_trip(db, trip, "El conductor reanudó la ubicación.", "resumed")
    elif action == "finalizar" and tracking.estado in {"activo", "pausado"}:
        tracking.estado, tracking.finalizado_en = "finalizado", now
        tracking.compartir_ubicacion = False
        trip.estado = "finalizado"
        _system_for_trip(db, trip, "El viaje finalizó y se detuvo la ubicación.", "finished")
        for request in trip.solicitudes:
            if request.estado == "aceptada":
                request.estado = "finalizada"
    else:
        raise HTTPException(status_code=409, detail="Transición de seguimiento inválida")
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return tracking


def set_sharing(db: Session, trip_id: int, user_id: int, enabled: bool) -> SeguimientoViaje:
    trip = db.get(Viaje, trip_id)
    tracking = current_session(db, trip_id)
    if not trip or trip.creador_id != user_id or not tracking:
        raise HTTPException(status_code=404, detail="Seguimiento no encontrado")
    if tracking.estado != "activo" and enabled:
        raise HTTPException(status_code=409, detail="El seguimiento no está activo")
    tracking.compartir_ubicacion = enabled
    _system_for_trip(
        db,
        trip,
        "El conductor activó la ubicación en tiempo real."
        if enabled
        else "El conductor dejó de compartir la ubicación.",
        "sharing-on" if enabled else "sharing-off",
    )
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return tracking


async def save_location(db: Session, trip_id: int, user_id: int, data: LocationUpdate) -> CurrentLocation:
    trip = db.get(Viaje, trip_id)
    tracking = current_session(db, trip_id)
    if not trip or trip.creador_id != user_id or not tracking:
        raise HTTPException(status_code=404, detail="Seguimiento no encontrado")
    if tracking.estado != "activo" or not tracking.compartir_ubicacion:
        raise HTTPException(status_code=409, detail="La ubicación no se está compartiendo")
    if data.accuracy > settings.location_max_accuracy_meters:
        raise HTTPException(status_code=422, detail="Precisión de ubicación insuficiente")
    await enforce_rate_limit(
        "location",
        user_id,
        trip_id,
        settings.location_rate_limit_updates,
        settings.location_rate_limit_window_seconds,
    )
    now = datetime.now(timezone.utc)
    tracking.ultima_latitud = data.latitude
    tracking.ultima_longitud = data.longitude
    tracking.ultima_precision_metros = data.accuracy
    tracking.ultima_velocidad_mps = data.speed
    tracking.ultima_direccion_grados = data.heading
    tracking.ultima_actualizacion_en = now
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    payload = {"latitude": data.latitude, "longitude": data.longitude, "accuracy": data.accuracy, "speed": data.speed, "heading": data.heading, "updated_at": now.isoformat(), "stale": False}
    redis = get_redis_client()
    try:
        await redis.set(f"location:current:{trip_id}", json.dumps(payload), ex=settings.location_stale_after_seconds * 3)
        await redis.publish(f"location:{trip_id}", json.dumps({"type": "location.updated", "data": payload, "timestamp": now.isoformat()}))
    finally:
        await redis.aclose()
    return CurrentLocation.model_validate(payload)


async def get_location(db: Session, trip_id: int, user_id: int) -> CurrentLocation:
    trip = authorized_trip(db, trip_id, user_id)
    tracking = current_session(db, trip_id)
    if not tracking or not tracking.compartir_ubicacion or tracking.estado not in {"activo", "pausado"}:
        raise HTTPException(status_code=404, detail="Ubicación no disponible")
    redis = get_redis_client()
    try:
        raw = await redis.get(f"location:current:{trip_id}")
    finally:
        await redis.aclose()
    if raw:
        payload = json.loads(raw)
    elif tracking.ultima_latitud is not None:
        payload = {"latitude": float(tracking.ultima_latitud), "longitude": float(tracking.ultima_longitud), "accuracy": float(tracking.ultima_precision_metros), "speed": float(tracking.ultima_velocidad_mps) if tracking.ultima_velocidad_mps is not None else None, "heading": float(tracking.ultima_direccion_grados) if tracking.ultima_direccion_grados is not None else None, "updated_at": tracking.ultima_actualizacion_en, "stale": True}
    else:
        raise HTTPException(status_code=404, detail="Ubicación no disponible")
    updated = datetime.fromisoformat(payload["updated_at"]) if isinstance(payload["updated_at"], str) else payload["updated_at"]
    payload["stale"] = tracking.estado == "pausado" or (datetime.now(timezone.utc) - updated).total_seconds() > settings.location_stale_after_seconds
    return CurrentLocation.model_validate(payload)


async def clear_location(trip_id: int) -> None:
    redis = get_redis_client()
    try:
        await redis.delete(f"location:current:{trip_id}")
    finally:
        await redis.aclose()
