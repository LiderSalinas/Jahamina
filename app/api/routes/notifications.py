import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.redis import consume_notification_ticket, create_notification_ticket, enforce_rate_limit, get_redis_client
from app.core.security import get_current_user
from app.core.settings import settings
from app.models.usuario import Usuario
from app.schemas.notification_schema import (
    NotificationListResponse, NotificationResponse, NotificationTicketResponse,
    PushConfigResponse, PushPreferences, PushSubscriptionCreate, PushSubscriptionResponse,
)
from app.services import notification_service

router = APIRouter(prefix="/notificaciones")


@router.get("/configuracion-push", response_model=PushConfigResponse)
def push_config():
    enabled = bool(settings.web_push_enabled and settings.web_push_vapid_public_key)
    return PushConfigResponse(enabled=enabled, public_key=settings.web_push_vapid_public_key if enabled else None)


@router.get("", response_model=NotificationListResponse)
def list_items(limit: int = Query(30, ge=1, le=100), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    items, unread = notification_service.list_notifications(db, user.id, limit)
    return NotificationListResponse(items=items, total_no_leidas=unread)


@router.get("/no-leidas", response_model=NotificationListResponse)
def unread_items(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    items, unread = notification_service.list_notifications(db, user.id, 30)
    return NotificationListResponse(items=[item for item in items if not item.leida], total_no_leidas=unread)


@router.patch("/leer-todas")
def read_all(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return {"marcadas": notification_service.mark_all_read(db, user.id)}


@router.patch("/{notification_id}/leida", response_model=NotificationResponse)
def read_one(notification_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return notification_service.mark_read(db, notification_id, user.id)


@router.post("/suscripciones", response_model=PushSubscriptionResponse, status_code=201)
def subscribe(data: PushSubscriptionCreate, request: Request, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return notification_service.register_subscription(db, user.id, data, request.headers.get("user-agent"))


@router.get("/suscripciones", response_model=list[PushSubscriptionResponse])
def subscriptions(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return notification_service.list_subscriptions(db, user.id)


@router.delete("/suscripciones/{subscription_id}", status_code=204)
def unsubscribe(subscription_id: int, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    notification_service.revoke_subscription(db, subscription_id, user.id)
    return Response(status_code=204)


@router.patch("/suscripciones/{subscription_id}", response_model=PushSubscriptionResponse)
def preferences(subscription_id: int, data: PushPreferences, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return notification_service.update_preferences(db, subscription_id, user.id, data)


@router.post("/prueba", response_model=NotificationResponse)
async def test_notification(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    if not settings.web_push_test_enabled:
        raise HTTPException(status_code=404, detail="Endpoint no disponible")
    await enforce_rate_limit("notification-test", user.id, 0, 3, 60)
    timestamp = int(datetime.now(timezone.utc).timestamp())
    return await notification_service.notify(db, user_id=user.id, actor_id=None, notification_type="mensaje_nuevo", title="Aviso de prueba", body="Las notificaciones de Jahamina están activas.", idempotency_key=f"test:{user.id}:{timestamp}", destination_url="/reservas")


@router.post("/ws-ticket", response_model=NotificationTicketResponse)
async def websocket_ticket(user: Usuario = Depends(get_current_user)):
    ticket = await create_notification_ticket(user.id)
    return NotificationTicketResponse(ticket=ticket, expires_in=settings.ws_ticket_expire_seconds)


@router.websocket("/ws")
async def notifications_socket(websocket: WebSocket, ticket: str = Query(...)):
    try:
        user_id = await consume_notification_ticket(ticket)
    except TimeoutError:
        await websocket.close(code=4408); return
    if not user_id:
        await websocket.close(code=4401); return
    await websocket.accept()
    await websocket.send_json({"type": "connected", "data": {}, "timestamp": datetime.now(timezone.utc).isoformat()})
    redis = get_redis_client(); pubsub = redis.pubsub()
    await pubsub.subscribe(f"notifications:{user_id}")
    receive_task = asyncio.create_task(websocket.receive_text())
    try:
        while True:
            published = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
            if published:
                await websocket.send_json(json.loads(published["data"]))
            if receive_task.done():
                raw = receive_task.result()
                receive_task = asyncio.create_task(websocket.receive_text())
                try:
                    event = json.loads(raw)
                except ValueError:
                    event = {}
                if event.get("type") == "ping":
                    await websocket.send_json({"type":"pong","data":{},"timestamp":datetime.now(timezone.utc).isoformat()})
    except WebSocketDisconnect:
        pass
    finally:
        receive_task.cancel()
        await pubsub.unsubscribe(); await pubsub.aclose(); await redis.aclose()
