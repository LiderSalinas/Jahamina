import asyncio
import json
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.redis import publish_notification_event
from app.core.settings import settings
from app.models.notificacion import Notificacion, SuscripcionPush
from app.schemas.notification_schema import NotificationResponse, PushPreferences, PushSubscriptionCreate

MESSAGE_TYPES = {"mensaje_nuevo"}
RESERVATION_TYPES = {"solicitud_nueva", "solicitud_aceptada", "solicitud_rechazada", "punto_confirmado"}


def validate_internal_url(value: str) -> str:
    parsed = urlparse(value)
    if not value.startswith("/") or value.startswith("//") or parsed.scheme or parsed.netloc:
        raise HTTPException(status_code=422, detail="La URL de destino debe ser interna")
    return value


def list_notifications(db: Session, user_id: int, limit: int = 30) -> tuple[list[Notificacion], int]:
    items = list(db.scalars(select(Notificacion).where(Notificacion.usuario_id == user_id).order_by(Notificacion.creada_en.desc()).limit(limit)))
    unread = db.scalar(select(func.count(Notificacion.id)).where(Notificacion.usuario_id == user_id, Notificacion.leida.is_(False))) or 0
    return items, unread


def mark_read(db: Session, notification_id: int, user_id: int) -> Notificacion:
    item = db.scalar(select(Notificacion).where(Notificacion.id == notification_id, Notificacion.usuario_id == user_id))
    if not item:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    if not item.leida:
        item.leida = True
        item.leida_en = datetime.now(timezone.utc)
        db.commit()
        db.refresh(item)
    return item


def mark_all_read(db: Session, user_id: int) -> int:
    now = datetime.now(timezone.utc)
    result = db.execute(update(Notificacion).where(Notificacion.usuario_id == user_id, Notificacion.leida.is_(False)).values(leida=True, leida_en=now))
    db.commit()
    return result.rowcount


def mark_conversation_read(db: Session, conversation_id: int, user_id: int) -> None:
    db.execute(update(Notificacion).where(Notificacion.usuario_id == user_id, Notificacion.conversacion_id == conversation_id, Notificacion.leida.is_(False)).values(leida=True, leida_en=datetime.now(timezone.utc)))
    db.commit()


def register_subscription(db: Session, user_id: int, data: PushSubscriptionCreate, user_agent: str | None) -> SuscripcionPush:
    existing = db.scalar(select(SuscripcionPush).where(SuscripcionPush.endpoint == data.endpoint))
    if existing and existing.usuario_id != user_id:
        raise HTTPException(status_code=409, detail="La suscripción pertenece a otro usuario")
    item = existing or SuscripcionPush(usuario_id=user_id, endpoint=data.endpoint)
    item.p256dh = data.keys.p256dh
    item.auth = data.keys.auth
    item.dispositivo_nombre = data.dispositivo_nombre
    item.user_agent = user_agent[:160] if user_agent else None
    item.activa = True
    item.revocada_en = None
    item.mensajes, item.reservas, item.viaje = data.mensajes, data.reservas, data.viaje
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def revoke_subscription(db: Session, subscription_id: int, user_id: int) -> None:
    item = db.scalar(select(SuscripcionPush).where(SuscripcionPush.id == subscription_id, SuscripcionPush.usuario_id == user_id))
    if not item:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    item.activa = False
    item.revocada_en = datetime.now(timezone.utc)
    db.commit()


def update_preferences(db: Session, subscription_id: int, user_id: int, data: PushPreferences) -> SuscripcionPush:
    item = db.scalar(select(SuscripcionPush).where(SuscripcionPush.id == subscription_id, SuscripcionPush.usuario_id == user_id, SuscripcionPush.activa.is_(True)))
    if not item:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    item.mensajes, item.reservas, item.viaje = data.mensajes, data.reservas, data.viaje
    db.commit(); db.refresh(item)
    return item


def list_subscriptions(db: Session, user_id: int) -> list[SuscripcionPush]:
    return list(db.scalars(select(SuscripcionPush).where(SuscripcionPush.usuario_id == user_id, SuscripcionPush.activa.is_(True)).order_by(SuscripcionPush.creada_en.desc())))


def _category_enabled(subscription: SuscripcionPush, notification_type: str) -> bool:
    if notification_type in MESSAGE_TYPES:
        return subscription.mensajes
    if notification_type in RESERVATION_TYPES:
        return subscription.reservas
    return subscription.viaje


def _send_web_push(subscription: SuscripcionPush, notification: Notificacion) -> None:
    from pywebpush import WebPushException, webpush

    try:
        webpush(
            subscription_info={"endpoint": subscription.endpoint, "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth}},
            data=json.dumps({"title": notification.titulo, "body": notification.cuerpo, "url": notification.url_destino, "tag": notification.clave_idempotencia}),
            vapid_private_key=settings.web_push_vapid_private_key,
            vapid_claims={"sub": settings.web_push_subject},
            timeout=8,
        )
    except WebPushException as error:
        status_code = getattr(getattr(error, "response", None), "status_code", None)
        if status_code in {404, 410}:
            raise LookupError("Suscripción expirada") from error
        raise


async def _dispatch_push(db: Session, notification: Notificacion) -> None:
    if not settings.web_push_enabled or not settings.web_push_vapid_private_key:
        return
    subscriptions = list(db.scalars(select(SuscripcionPush).where(SuscripcionPush.usuario_id == notification.usuario_id, SuscripcionPush.activa.is_(True))))
    for subscription in subscriptions:
        if not _category_enabled(subscription, notification.tipo):
            continue
        try:
            await asyncio.to_thread(_send_web_push, subscription, notification)
            subscription.ultima_utilizacion_en = datetime.now(timezone.utc)
        except LookupError:
            subscription.activa = False
            subscription.revocada_en = datetime.now(timezone.utc)
        except Exception:
            continue
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()


async def notify(
    db: Session, *, user_id: int, actor_id: int | None, notification_type: str,
    title: str, body: str, idempotency_key: str, destination_url: str,
    reservation_id: int | None = None, trip_id: int | None = None,
    conversation_id: int | None = None,
) -> Notificacion | None:
    if actor_id == user_id:
        return None
    destination_url = validate_internal_url(destination_url)
    item = db.scalar(select(Notificacion).where(Notificacion.clave_idempotencia == idempotency_key))
    if item:
        return item
    item = Notificacion(
        usuario_id=user_id, tipo=notification_type, titulo=title[:120], cuerpo=body[:300],
        reserva_id=reservation_id, viaje_id=trip_id, conversacion_id=conversation_id,
        url_destino=destination_url, clave_idempotencia=idempotency_key[:180],
    )
    try:
        db.add(item)
        db.commit()
        db.refresh(item)
    except IntegrityError:
        db.rollback()
        return db.scalar(select(Notificacion).where(Notificacion.clave_idempotencia == idempotency_key))
    payload = NotificationResponse.model_validate(item).model_dump(mode="json")
    try:
        await publish_notification_event(user_id, {"type": "notification.created", "data": payload, "timestamp": datetime.now(timezone.utc).isoformat()})
    except Exception:
        pass
    try:
        await _dispatch_push(db, item)
    except Exception:
        # La acción principal y la notificación interna ya fueron confirmadas.
        # Web Push es un canal complementario y nunca debe revertirlas.
        pass
    return item
