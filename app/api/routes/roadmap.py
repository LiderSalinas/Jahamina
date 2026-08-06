import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, get_db
from app.core.redis import (
    consume_roadmap_ticket, create_roadmap_ticket, get_redis_client,
    publish_chat_event, publish_roadmap_event,
)
from app.core.security import get_current_user
from app.core.settings import settings
from app.models.usuario import Usuario
from app.schemas.chat_schema import MessageResponse
from app.schemas.roadmap_schema import RoadmapResponse, RoadmapTicketResponse
from app.services import roadmap_service
from app.services import notification_service
from app.models.solicitud_viaje import SolicitudViaje
from sqlalchemy import select

router = APIRouter()


@router.get("/reservas/{reserva_id}/hoja-ruta", response_model=RoadmapResponse)
def get_roadmap(reserva_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return roadmap_service.get_roadmap(db, reserva_id, user.id)


@router.post("/reservas/{reserva_id}/hoja-ruta/ws-ticket", response_model=RoadmapTicketResponse)
async def roadmap_ticket(reserva_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    data = roadmap_service.get_roadmap(db, reserva_id, user.id)
    ticket = await create_roadmap_ticket(user.id, reserva_id, data.viaje.id)
    return RoadmapTicketResponse(ticket=ticket, expires_in=settings.ws_ticket_expire_seconds)


async def _publish(response: RoadmapResponse, event: dict) -> RoadmapResponse:
    messages = event.pop("messages", [])
    created = event.pop("created", False)
    timestamp = datetime.now(timezone.utc).isoformat()
    event["timestamp"] = timestamp
    events = [event]
    if created:
        events.append({"type": "trip.event.created", "data": event["data"], "timestamp": timestamp})
    if event["type"] == "passenger.status.changed":
        events.append({"type": "trip.stop.updated", "data": event["data"], "timestamp": timestamp})
        if event["data"].get("estado") == "abordo":
            events.append({"type": "trip.occupancy.changed", "data": response.ocupacion.model_dump(), "timestamp": timestamp})
    events.append({"type": "roadmap.updated", "data": {"reserva_id": response.reserva.id, "viaje_id": response.viaje.id}, "timestamp": timestamp})
    for roadmap_event in events:
        await publish_roadmap_event(response.viaje.id, roadmap_event)
    for message in messages:
        await publish_chat_event(
            message.conversacion_id,
            {"type": "message.created", "data": MessageResponse.model_validate(message).model_dump(mode="json"), "timestamp": timestamp},
        )
    return response


@router.post("/viajes/{viaje_id}/acciones/{accion}", response_model=RoadmapResponse)
async def trip_action(viaje_id: int, accion: str, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    response, event = roadmap_service.trip_action(db, viaje_id, user.id, accion)
    published = await _publish(response, event)
    config = {
        "salir": ("conductor_en_camino", "El conductor está en camino", "El conductor salió hacia el punto de encuentro."),
        "iniciar": ("viaje_iniciado", "El viaje comenzó", "Tu viaje compartido ya está en curso."),
        "finalizar": ("viaje_finalizado", "Viaje finalizado", "El viaje compartido finalizó."),
    }.get(accion)
    if config and event.get("created", True):
        kind, title, body = config
        requests = list(db.scalars(select(SolicitudViaje).where(SolicitudViaje.viaje_id == viaje_id, SolicitudViaje.estado.in_({"aceptada", "finalizada"}))))
        for request in requests:
            await notification_service.notify(
                db, user_id=request.pasajero_id, actor_id=user.id, notification_type=kind,
                title=title, body=body, idempotency_key=f"trip:{viaje_id}:{kind}:{request.pasajero_id}",
                destination_url=f"/reservas/{request.id}", reservation_id=request.id, trip_id=viaje_id,
                conversation_id=request.conversacion.id if request.conversacion else None,
            )
    return published


@router.post("/reservas/{reserva_id}/acciones/{accion}", response_model=RoadmapResponse)
async def passenger_action(reserva_id: int, accion: str, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    response, event = roadmap_service.passenger_action(db, reserva_id, user.id, accion)
    return await _publish(response, event)


@router.websocket("/ws/hoja-ruta")
async def roadmap_socket(websocket: WebSocket, ticket: str = Query(...)):
    try:
        identity = await consume_roadmap_ticket(ticket)
    except TimeoutError:
        await websocket.close(code=4408); return
    if not identity:
        await websocket.close(code=4401); return
    user_id, reservation_id, trip_id = identity
    with SessionLocal() as db:
        try:
            roadmap_service.get_roadmap(db, reservation_id, user_id)
        except Exception:
            await websocket.close(code=4403); return
    await websocket.accept()
    await websocket.send_json({"type": "connected", "data": {"reserva_id": reservation_id}, "timestamp": datetime.now(timezone.utc).isoformat()})
    redis = get_redis_client()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"roadmap:{trip_id}")

    async def forward() -> None:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
            if message:
                await websocket.send_json(json.loads(message["data"]))
            await asyncio.sleep(0.05)

    task = asyncio.create_task(forward())
    try:
        while True:
            incoming = await websocket.receive_json()
            if incoming.get("type") == "ping":
                await websocket.send_json({"type": "pong", "data": {}, "timestamp": datetime.now(timezone.utc).isoformat()})
            else:
                await websocket.send_json({"type": "error", "data": {"detail": "Evento no permitido"}, "timestamp": datetime.now(timezone.utc).isoformat()})
    except (WebSocketDisconnect, ValueError):
        pass
    finally:
        task.cancel()
        await pubsub.unsubscribe(f"roadmap:{trip_id}")
        await pubsub.aclose()
        await redis.aclose()
