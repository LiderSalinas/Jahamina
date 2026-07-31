from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.conversacion import Conversacion
from app.models.mensaje import Mensaje
from app.models.solicitud_viaje import SolicitudViaje
from app.models.usuario import Usuario
from app.schemas.chat_schema import (
    ConversationResponse,
    MessageCreate,
    MessagePage,
    ReadResponse,
    UnreadConversation,
    UnreadResponse,
)
from app.core.settings import settings

SYSTEM_ACCEPTED = "La reserva fue aceptada. Ya pueden coordinar el viaje."
WRITABLE_TRIP_STATES = {"publicado", "completo", "en_curso"}


def _conversation_query():
    return select(Conversacion).options(
        joinedload(Conversacion.solicitud).joinedload(SolicitudViaje.viaje),
        joinedload(Conversacion.solicitud).joinedload(SolicitudViaje.pasajero),
    )


def get_authorized_conversation(
    db: Session, conversation_id: int, user_id: int
) -> Conversacion:
    conversation = db.scalar(
        _conversation_query().where(Conversacion.id == conversation_id)
    )
    if not conversation or user_id not in {
        conversation.solicitud.pasajero_id,
        conversation.solicitud.viaje.creador_id,
    }:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return conversation


def can_write(conversation: Conversacion) -> bool:
    request = conversation.solicitud
    return (
        conversation.activa
        and request.estado == "aceptada"
        and request.viaje.estado in WRITABLE_TRIP_STATES
    )


def create_or_get_conversation(
    db: Session, request: SolicitudViaje
) -> Conversacion:
    existing = db.scalar(
        select(Conversacion).where(Conversacion.solicitud_id == request.id)
    )
    if existing:
        return existing
    if request.estado != "aceptada":
        raise HTTPException(status_code=409, detail="La reserva aún no fue aceptada")
    conversation = Conversacion(solicitud_id=request.id)
    db.add(conversation)
    db.flush()
    add_system_message(
        db,
        conversation,
        SYSTEM_ACCEPTED,
        f"system:request:{request.id}:accepted",
    )
    return conversation


def add_system_message(
    db: Session,
    conversation: Conversacion,
    content: str,
    event_id: str,
) -> Mensaje:
    existing = db.scalar(
        select(Mensaje).where(
            Mensaje.conversacion_id == conversation.id,
            Mensaje.client_message_id == event_id,
        )
    )
    if existing:
        return existing
    message = Mensaje(
        conversacion_id=conversation.id,
        remitente_id=None,
        contenido=content,
        tipo="sistema",
        client_message_id=event_id,
    )
    db.add(message)
    db.flush()
    conversation.ultimo_mensaje_en = message.creado_en or datetime.now(timezone.utc)
    conversation.actualizada_en = datetime.now(timezone.utc)
    return message


def close_with_system_message(
    db: Session, request: SolicitudViaje, content: str, event_id: str
) -> None:
    conversation = db.scalar(
        select(Conversacion).where(Conversacion.solicitud_id == request.id)
    )
    if not conversation:
        return
    add_system_message(db, conversation, content, event_id)
    conversation.activa = False
    conversation.cerrada_en = conversation.cerrada_en or datetime.now(timezone.utc)


def get_by_request(db: Session, request_id: int, user_id: int) -> Conversacion:
    request = db.scalar(
        select(SolicitudViaje)
        .options(joinedload(SolicitudViaje.viaje))
        .where(SolicitudViaje.id == request_id)
    )
    if not request or user_id not in {request.pasajero_id, request.viaje.creador_id}:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    if request.estado == "pendiente" or request.estado == "rechazada":
        raise HTTPException(status_code=409, detail="La reserva no tiene chat")
    conversation = db.scalar(
        select(Conversacion).where(Conversacion.solicitud_id == request_id)
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    return get_authorized_conversation(db, conversation.id, user_id)


def to_response(
    db: Session, conversation: Conversacion, user_id: int
) -> ConversationResponse:
    request = conversation.solicitud
    trip = request.viaje
    participant_id = trip.creador_id if user_id == request.pasajero_id else request.pasajero_id
    participant = db.get(Usuario, participant_id)
    last_message = db.scalar(
        select(Mensaje.contenido)
        .where(Mensaje.conversacion_id == conversation.id, Mensaje.eliminado.is_(False))
        .order_by(Mensaje.id.desc())
        .limit(1)
    )
    unread = db.scalar(
        select(func.count(Mensaje.id)).where(
            Mensaje.conversacion_id == conversation.id,
            Mensaje.remitente_id.is_not(None),
            Mensaje.remitente_id != user_id,
            Mensaje.leido_en.is_(None),
            Mensaje.eliminado.is_(False),
        )
    ) or 0
    return ConversationResponse(
        id=conversation.id,
        solicitud_id=request.id,
        creada_en=conversation.creada_en,
        actualizada_en=conversation.actualizada_en,
        ultimo_mensaje_en=conversation.ultimo_mensaje_en,
        cerrada_en=conversation.cerrada_en,
        activa=conversation.activa,
        puede_escribir=can_write(conversation),
        no_leidos=unread,
        participante=participant.nombre if participant else "Participante",
        viaje_id=trip.id,
        origen=trip.origen,
        destino=trip.destino,
        estado_viaje=trip.estado,
        estado_reserva=request.estado,
        ultimo_mensaje=last_message,
    )


def list_messages(
    db: Session,
    conversation_id: int,
    user_id: int,
    before_id: int | None,
    limit: int,
) -> MessagePage:
    get_authorized_conversation(db, conversation_id, user_id)
    query = select(Mensaje).where(
        Mensaje.conversacion_id == conversation_id,
        Mensaje.eliminado.is_(False),
    )
    if before_id is not None:
        query = query.where(Mensaje.id < before_id)
    descending = list(db.scalars(query.order_by(Mensaje.id.desc()).limit(limit + 1)))
    has_more = len(descending) > limit
    selected = descending[:limit]
    return MessagePage(
        items=list(reversed(selected)),
        next_cursor=selected[-1].id if has_more and selected else None,
    )


def create_message(
    db: Session,
    conversation_id: int,
    user_id: int,
    data: MessageCreate,
) -> Mensaje:
    if len(data.contenido) > settings.chat_max_message_length:
        raise HTTPException(status_code=422, detail="Mensaje demasiado largo")
    conversation = get_authorized_conversation(db, conversation_id, user_id)
    if not can_write(conversation):
        raise HTTPException(status_code=409, detail="La conversación está cerrada")
    if data.client_message_id:
        existing = db.scalar(
            select(Mensaje).where(
                Mensaje.conversacion_id == conversation_id,
                Mensaje.remitente_id == user_id,
                Mensaje.client_message_id == data.client_message_id,
            )
        )
        if existing:
            return existing
    message = Mensaje(
        conversacion_id=conversation_id,
        remitente_id=user_id,
        contenido=data.contenido,
        tipo="texto",
        client_message_id=data.client_message_id,
    )
    try:
        db.add(message)
        db.flush()
        conversation.ultimo_mensaje_en = message.creado_en or datetime.now(timezone.utc)
        conversation.actualizada_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(message)
    except IntegrityError:
        db.rollback()
        if data.client_message_id:
            duplicate = db.scalar(
                select(Mensaje).where(
                    Mensaje.conversacion_id == conversation_id,
                    Mensaje.remitente_id == user_id,
                    Mensaje.client_message_id == data.client_message_id,
                )
            )
            if duplicate:
                return duplicate
        raise
    except SQLAlchemyError:
        db.rollback()
        raise
    return message


def mark_read(db: Session, conversation_id: int, user_id: int) -> ReadResponse:
    get_authorized_conversation(db, conversation_id, user_id)
    now = datetime.now(timezone.utc)
    result = db.execute(
        update(Mensaje)
        .where(
            Mensaje.conversacion_id == conversation_id,
            Mensaje.remitente_id.is_not(None),
            Mensaje.remitente_id != user_id,
            Mensaje.leido_en.is_(None),
            Mensaje.eliminado.is_(False),
        )
        .values(leido_en=now)
    )
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return ReadResponse(mensajes_marcados=result.rowcount, leido_en=now)


def unread_counts(db: Session, user_id: int) -> UnreadResponse:
    rows = db.execute(
        select(
            Mensaje.conversacion_id,
            SolicitudViaje.id,
            func.count(Mensaje.id),
        )
        .select_from(Mensaje)
        .join(Mensaje.conversacion)
        .join(Conversacion.solicitud)
        .join(SolicitudViaje.viaje)
        .where(
            (SolicitudViaje.pasajero_id == user_id) | (SolicitudViaje.viaje.has(creador_id=user_id)),
            Mensaje.remitente_id.is_not(None),
            Mensaje.remitente_id != user_id,
            Mensaje.leido_en.is_(None),
            Mensaje.eliminado.is_(False),
        )
        .group_by(Mensaje.conversacion_id, SolicitudViaje.id)
    ).all()
    conversations = [
        UnreadConversation(
            conversacion_id=row[0], solicitud_id=row[1], cantidad=row[2]
        )
        for row in rows
    ]
    return UnreadResponse(total=sum(item.cantidad for item in conversations), conversaciones=conversations)
