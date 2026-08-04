import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.redis import consume_location_ticket, create_location_ticket, get_redis_client
from app.core.security import get_current_user
from app.core.settings import settings
from app.models.usuario import Usuario
from app.schemas.tracking_schema import CurrentLocation, LocationEtaResponse, LocationTicketResponse, LocationUpdate, SharingUpdate, TrackingResponse
from app.services import eta_service, tracking_service

router = APIRouter()


async def _publish_location_event(trip_id: int, event_type: str, data: dict | None = None) -> None:
    redis = get_redis_client()
    try:
        await redis.publish(f"location:{trip_id}", json.dumps({"type": event_type, "data": data or {}, "timestamp": datetime.now(timezone.utc).isoformat()}))
    finally:
        await redis.aclose()


@router.post("/viajes/{trip_id}/seguimiento/iniciar", response_model=TrackingResponse)
def start(trip_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return tracking_service.start(db, trip_id, user.id)


@router.patch("/viajes/{trip_id}/seguimiento/pausar", response_model=TrackingResponse)
async def pause(trip_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    result = tracking_service.transition(db, trip_id, user.id, "pausar")
    await _publish_location_event(trip_id, "location.paused")
    return result


@router.patch("/viajes/{trip_id}/seguimiento/reanudar", response_model=TrackingResponse)
async def resume(trip_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    result = tracking_service.transition(db, trip_id, user.id, "reanudar")
    await _publish_location_event(trip_id, "location.resumed")
    return result


@router.patch("/viajes/{trip_id}/seguimiento/finalizar", response_model=TrackingResponse)
async def finish(trip_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    result = tracking_service.transition(db, trip_id, user.id, "finalizar")
    await tracking_service.clear_location(trip_id)
    redis = get_redis_client()
    try:
        await redis.publish(f"location:{trip_id}", json.dumps({"type": "tracking.finished", "data": {}, "timestamp": datetime.now(timezone.utc).isoformat()}))
    finally:
        await redis.aclose()
    return result


@router.patch("/viajes/{trip_id}/seguimiento/compartir", response_model=TrackingResponse)
async def sharing(trip_id: int, data: SharingUpdate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    result = tracking_service.set_sharing(db, trip_id, user.id, data.enabled)
    if not data.enabled:
        await tracking_service.clear_location(trip_id)
    await _publish_location_event(trip_id, "location.resumed" if data.enabled else "location.stopped")
    return result


@router.get("/viajes/{trip_id}/seguimiento", response_model=TrackingResponse)
def get_tracking(trip_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    tracking_service.authorized_trip(db, trip_id, user.id)
    result = tracking_service.current_session(db, trip_id)
    if not result:
        raise HTTPException(status_code=404, detail="Seguimiento no encontrado")
    return result


@router.get("/viajes/{trip_id}/ubicacion-actual", response_model=CurrentLocation)
async def current_location(trip_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return await tracking_service.get_location(db, trip_id, user.id)


@router.get("/reservas/{reservation_id}/ubicacion-contexto", response_model=LocationEtaResponse)
async def location_context(reservation_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return await eta_service.next_stop_eta(db, reservation_id, user.id)


@router.post("/viajes/{trip_id}/ubicacion", response_model=CurrentLocation)
async def update_location(trip_id: int, data: LocationUpdate, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return await tracking_service.save_location(db, trip_id, user.id, data)


@router.post("/viajes/{trip_id}/ubicacion/ws-ticket", response_model=LocationTicketResponse)
async def location_ticket(trip_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    trip = tracking_service.authorized_trip(db, trip_id, user.id)
    role = "publisher" if trip.creador_id == user.id else "subscriber"
    ticket = await create_location_ticket(user.id, trip_id, role)
    return LocationTicketResponse(ticket=ticket, role=role, expires_in=settings.ws_ticket_expire_seconds)


@router.websocket("/ws/ubicacion")
async def location_websocket(websocket: WebSocket, ticket: str = Query(...), db: Session = Depends(get_db)):
    await websocket.accept()
    pubsub = None
    redis = None
    receiver = None
    try:
        try:
            identity = await consume_location_ticket(ticket)
        except TimeoutError:
            await websocket.close(code=4408, reason="Ticket vencido")
            return
        if not identity:
            await websocket.close(code=4401, reason="Ticket inválido")
            return
        user_id, trip_id, role = identity
        tracking_service.authorized_trip(db, trip_id, user_id)
        redis = get_redis_client()
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"location:{trip_id}")
        await websocket.send_json({"type": "connected", "data": {"trip_id": trip_id, "role": role}, "timestamp": datetime.now(timezone.utc).isoformat()})
        receiver = asyncio.create_task(websocket.receive_text())
        while True:
            published = await pubsub.get_message(ignore_subscribe_messages=True, timeout=.1)
            if published and published.get("type") == "message":
                await websocket.send_json(json.loads(published["data"]))
            if not receiver.done():
                await asyncio.sleep(.02)
                continue
            raw = receiver.result()
            receiver = asyncio.create_task(websocket.receive_text())
            if len(raw.encode()) > settings.location_max_payload_bytes:
                await websocket.send_json({"type": "error", "data": {"detail": "Payload demasiado grande"}, "timestamp": datetime.now(timezone.utc).isoformat()})
                continue
            try:
                event = json.loads(raw)
                event_type = event.get("type")
                if event_type == "ping":
                    await websocket.send_json({"type": "pong", "data": {}, "timestamp": datetime.now(timezone.utc).isoformat()})
                elif event_type == "location.update" and role == "publisher":
                    await tracking_service.save_location(db, trip_id, user_id, LocationUpdate.model_validate(event.get("data", {})))
                elif event_type == "location.pause" and role == "publisher":
                    tracking_service.transition(db, trip_id, user_id, "pausar")
                    await _publish_location_event(trip_id, "location.paused")
                elif event_type == "location.resume" and role == "publisher":
                    tracking_service.transition(db, trip_id, user_id, "reanudar")
                    await _publish_location_event(trip_id, "location.resumed")
                else:
                    await websocket.send_json({"type": "error", "data": {"detail": "Evento no permitido"}, "timestamp": datetime.now(timezone.utc).isoformat()})
            except (ValueError, ValidationError, HTTPException) as error:
                await websocket.send_json({"type": "error", "data": {"detail": getattr(error, "detail", "Evento inválido")}, "timestamp": datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        pass
    finally:
        if receiver:
            receiver.cancel()
        if pubsub:
            await pubsub.unsubscribe()
            await pubsub.aclose()
        if redis:
            await redis.aclose()
