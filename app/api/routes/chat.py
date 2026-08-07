import asyncio
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.redis import (
    acquire_connection,
    consume_ticket,
    create_ticket,
    enforce_rate_limit,
    get_redis_client,
    publish_chat_event,
    release_connection,
    set_chat_presence,
)
from app.core.security import get_current_user
from app.core.settings import settings
from app.models.usuario import Usuario
from app.schemas.chat_schema import (
    ConversationResponse,
    MessageCreate,
    MessagePage,
    MessageResponse,
    ReadResponse,
    UnreadResponse,
    WebSocketClientEvent,
    WebSocketTicketResponse,
)
from app.services import chat_service
from app.services import notification_service

router = APIRouter()


def event_payload(event_type: str, data: dict) -> dict:
    return {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/reservas/{request_id}/conversacion",
    response_model=ConversationResponse,
)
def conversation_by_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    conversation = chat_service.get_by_request(db, request_id, user.id)
    return chat_service.to_response(db, conversation, user.id)


@router.get("/conversaciones/no-leidos", response_model=UnreadResponse)
def unread(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    return chat_service.unread_counts(db, user.id)


@router.get(
    "/conversaciones/{conversation_id}",
    response_model=ConversationResponse,
)
def conversation_detail(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    conversation = chat_service.get_authorized_conversation(
        db, conversation_id, user.id
    )
    return chat_service.to_response(db, conversation, user.id)


@router.get(
    "/conversaciones/{conversation_id}/mensajes",
    response_model=MessagePage,
)
def messages(
    conversation_id: int,
    before_id: int | None = None,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    return chat_service.list_messages(
        db, conversation_id, user.id, before_id, limit
    )


@router.post(
    "/conversaciones/{conversation_id}/mensajes",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: int,
    data: MessageCreate,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    await enforce_rate_limit(
        "message",
        user.id,
        conversation_id,
        settings.chat_rate_limit_messages,
    )
    message = chat_service.create_message(db, conversation_id, user.id, data)
    await publish_chat_event(
        conversation_id,
        event_payload(
            "message.created",
            MessageResponse.model_validate(message).model_dump(mode="json"),
        ),
    )
    conversation = chat_service.get_authorized_conversation(db, conversation_id, user.id)
    recipient_id = conversation.solicitud.viaje.creador_id if user.id == conversation.solicitud.pasajero_id else conversation.solicitud.pasajero_id
    await notification_service.notify(
        db, user_id=recipient_id, actor_id=user.id, notification_type="mensaje_nuevo",
        title="Nuevo mensaje en tu viaje", body="Tenés un mensaje nuevo.",
        idempotency_key=f"chat:{conversation_id}:{message.client_message_id or message.id}:{recipient_id}",
        destination_url=f"/reservas/{conversation.solicitud_id}", reservation_id=conversation.solicitud_id,
        trip_id=conversation.solicitud.viaje_id, conversation_id=conversation_id,
    )
    return message


@router.patch(
    "/conversaciones/{conversation_id}/leido",
    response_model=ReadResponse,
)
async def mark_read(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    result = chat_service.mark_read(db, conversation_id, user.id)
    notification_service.mark_conversation_read(db, conversation_id, user.id)
    await publish_chat_event(
        conversation_id,
        event_payload(
            "message.read",
            {"usuario_id": user.id, **result.model_dump(mode="json")},
        ),
    )
    return result


@router.post(
    "/conversaciones/{conversation_id}/ws-ticket",
    response_model=WebSocketTicketResponse,
)
async def websocket_ticket(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    chat_service.get_authorized_conversation(db, conversation_id, user.id)
    ticket = await create_ticket(user.id, conversation_id)
    return WebSocketTicketResponse(
        ticket=ticket, expires_in=settings.ws_ticket_expire_seconds
    )


async def _send_error(websocket: WebSocket, detail: str) -> None:
    await websocket.send_json(event_payload("error", {"detail": detail}))


@router.websocket("/ws/chat")
async def chat_websocket(
    websocket: WebSocket,
    ticket: str = Query(...),
    db: Session = Depends(get_db),
):
    await websocket.accept()
    user_id: int | None = None
    pubsub = None
    pubsub_client = None
    receive_task = None
    try:
        try:
            identity = await consume_ticket(ticket)
        except TimeoutError:
            await websocket.close(code=4408, reason="Ticket vencido")
            return
        except HTTPException:
            await websocket.close(code=1013, reason="Redis no disponible")
            return
        if not identity:
            await websocket.close(code=4401, reason="Ticket inválido")
            return
        user_id, conversation_id = identity
        chat_service.get_authorized_conversation(db, conversation_id, user_id)
        if not await acquire_connection(user_id):
            await websocket.close(code=4429, reason="Límite excedido")
            return

        pubsub_client = get_redis_client()
        pubsub = pubsub_client.pubsub()
        await pubsub.subscribe(f"chat:{conversation_id}")
        await set_chat_presence(user_id, conversation_id, True)
        await websocket.send_json(
            event_payload(
                "connected",
                {"conversation_id": conversation_id, "user_id": user_id},
            )
        )
        receive_task = asyncio.create_task(websocket.receive_text())
        while True:
            published = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=0.1
            )
            if published and published.get("type") == "message":
                await websocket.send_json(json.loads(published["data"]))
            if not receive_task.done():
                await asyncio.sleep(0.02)
                continue
            raw = receive_task.result()
            receive_task = asyncio.create_task(websocket.receive_text())
            if len(raw.encode()) > settings.chat_max_payload_bytes:
                await _send_error(websocket, "Payload demasiado grande")
                continue
            try:
                incoming = WebSocketClientEvent.model_validate_json(raw)
            except ValidationError:
                await _send_error(websocket, "Evento inválido")
                continue

            if incoming.type == "ping":
                await websocket.send_json(event_payload("pong", {}))
            elif incoming.type == "message.send":
                try:
                    data = MessageCreate.model_validate(incoming.data)
                    await enforce_rate_limit(
                        "message",
                        user_id,
                        conversation_id,
                        settings.chat_rate_limit_messages,
                    )
                    message = chat_service.create_message(
                        db, conversation_id, user_id, data
                    )
                    serialized = MessageResponse.model_validate(
                        message
                    ).model_dump(mode="json")
                    await publish_chat_event(
                        conversation_id,
                        event_payload("message.created", serialized),
                    )
                    conversation = chat_service.get_authorized_conversation(db, conversation_id, user_id)
                    recipient_id = conversation.solicitud.viaje.creador_id if user_id == conversation.solicitud.pasajero_id else conversation.solicitud.pasajero_id
                    await notification_service.notify(
                        db, user_id=recipient_id, actor_id=user_id, notification_type="mensaje_nuevo",
                        title="Nuevo mensaje en tu viaje", body="Tenés un mensaje nuevo.",
                        idempotency_key=f"chat:{conversation_id}:{message.client_message_id or message.id}:{recipient_id}",
                        destination_url=f"/reservas/{conversation.solicitud_id}", reservation_id=conversation.solicitud_id,
                        trip_id=conversation.solicitud.viaje_id, conversation_id=conversation_id,
                    )
                except (ValidationError, HTTPException) as error:
                    detail = (
                        error.detail
                        if isinstance(error, HTTPException)
                        else "Mensaje inválido"
                    )
                    await _send_error(websocket, detail)
            elif incoming.type == "message.read":
                result = chat_service.mark_read(db, conversation_id, user_id)
                notification_service.mark_conversation_read(db, conversation_id, user_id)
                await publish_chat_event(
                    conversation_id,
                    event_payload(
                        "message.read",
                        {"usuario_id": user_id, **result.model_dump(mode="json")},
                    ),
                )
            else:
                await enforce_rate_limit(
                    "typing",
                    user_id,
                    conversation_id,
                    settings.chat_typing_rate_limit_events,
                )
                event_type = (
                    "typing.started"
                    if incoming.type == "typing.start"
                    else "typing.stopped"
                )
                await publish_chat_event(
                    conversation_id,
                    event_payload(event_type, {"usuario_id": user_id}),
                )
    except WebSocketDisconnect:
        pass
    except (RedisError, HTTPException):
        try:
            await websocket.close(code=1013, reason="Chat no disponible")
        except RuntimeError:
            pass
    finally:
        if receive_task is not None:
            receive_task.cancel()
        if pubsub is not None:
            await pubsub.unsubscribe()
            await pubsub.aclose()
        if pubsub_client is not None:
            await pubsub_client.aclose()
        if user_id is not None:
            if "conversation_id" in locals():
                await set_chat_presence(user_id, conversation_id, False)
            await release_connection(user_id)
