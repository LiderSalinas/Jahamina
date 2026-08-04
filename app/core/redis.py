import hashlib
import json
import secrets
import time
from fastapi import HTTPException
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.settings import settings


def get_redis_client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def _ticket_key(ticket: str) -> str:
    digest = hashlib.sha256(ticket.encode()).hexdigest()
    return f"chat:ticket:{digest}"


async def require_redis() -> Redis:
    client = get_redis_client()
    try:
        await client.ping()
    except RedisError as error:
        raise HTTPException(
            status_code=503, detail="Chat en tiempo real no disponible"
        ) from error
    return client


async def create_ticket(user_id: int, conversation_id: int) -> str:
    client = await require_redis()
    expires_at = int(time.time()) + settings.ws_ticket_expire_seconds
    ticket = f"{expires_at}.{secrets.token_urlsafe(32)}"
    value = json.dumps({"user_id": user_id, "conversation_id": conversation_id})
    try:
        await client.set(
            _ticket_key(ticket),
            value,
            ex=settings.ws_ticket_expire_seconds,
            nx=True,
        )
    finally:
        await client.aclose()
    return ticket


async def consume_ticket(ticket: str) -> tuple[int, int] | None:
    try:
        expires_at = int(ticket.split(".", 1)[0])
    except (ValueError, IndexError):
        return None
    if expires_at < int(time.time()):
        raise TimeoutError("Ticket vencido")
    client = await require_redis()
    try:
        value = await client.getdel(_ticket_key(ticket))
    finally:
        await client.aclose()
    if not value:
        return None
    payload = json.loads(value)
    return int(payload["user_id"]), int(payload["conversation_id"])


async def create_location_ticket(user_id: int, trip_id: int, role: str) -> str:
    client = await require_redis()
    expires_at = int(time.time()) + settings.ws_ticket_expire_seconds
    ticket = f"{expires_at}.{secrets.token_urlsafe(32)}"
    value = json.dumps({"user_id": user_id, "trip_id": trip_id, "role": role})
    try:
        await client.set(
            f"location:ticket:{hashlib.sha256(ticket.encode()).hexdigest()}",
            value,
            ex=settings.ws_ticket_expire_seconds,
            nx=True,
        )
    finally:
        await client.aclose()
    return ticket


async def consume_location_ticket(ticket: str) -> tuple[int, int, str] | None:
    try:
        expires_at = int(ticket.split(".", 1)[0])
    except (ValueError, IndexError):
        return None
    if expires_at < int(time.time()):
        raise TimeoutError("Ticket vencido")
    client = await require_redis()
    try:
        value = await client.getdel(
            f"location:ticket:{hashlib.sha256(ticket.encode()).hexdigest()}"
        )
    finally:
        await client.aclose()
    if not value:
        return None
    payload = json.loads(value)
    return int(payload["user_id"]), int(payload["trip_id"]), payload["role"]


async def create_roadmap_ticket(user_id: int, reservation_id: int, trip_id: int) -> str:
    client = await require_redis()
    expires_at = int(time.time()) + settings.ws_ticket_expire_seconds
    ticket = f"{expires_at}.{secrets.token_urlsafe(32)}"
    key = f"roadmap:ticket:{hashlib.sha256(ticket.encode()).hexdigest()}"
    value = json.dumps({"user_id": user_id, "reservation_id": reservation_id, "trip_id": trip_id})
    try:
        await client.set(key, value, ex=settings.ws_ticket_expire_seconds, nx=True)
    finally:
        await client.aclose()
    return ticket


async def consume_roadmap_ticket(ticket: str) -> tuple[int, int, int] | None:
    try:
        expires_at = int(ticket.split(".", 1)[0])
    except (ValueError, IndexError):
        return None
    if expires_at < int(time.time()):
        raise TimeoutError("Ticket vencido")
    client = await require_redis()
    try:
        value = await client.getdel(f"roadmap:ticket:{hashlib.sha256(ticket.encode()).hexdigest()}")
    finally:
        await client.aclose()
    if not value:
        return None
    payload = json.loads(value)
    return int(payload["user_id"]), int(payload["reservation_id"]), int(payload["trip_id"])


async def publish_roadmap_event(trip_id: int, event: dict) -> None:
    client = await require_redis()
    try:
        await client.publish(f"roadmap:{trip_id}", json.dumps(event))
    finally:
        await client.aclose()


async def enforce_rate_limit(
    scope: str,
    user_id: int,
    conversation_id: int,
    limit: int,
    window_seconds: int | None = None,
) -> None:
    client = await require_redis()
    window = window_seconds or settings.chat_rate_limit_window_seconds
    bucket = int(time.time()) // window
    key = f"chat:rate:{scope}:{conversation_id}:{user_id}:{bucket}"
    try:
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, window + 1)
    finally:
        await client.aclose()
    if count > limit:
        raise HTTPException(status_code=429, detail="Límite de chat excedido")


async def publish_chat_event(conversation_id: int, event: dict) -> None:
    client = await require_redis()
    try:
        await client.publish(f"chat:{conversation_id}", json.dumps(event))
    finally:
        await client.aclose()


async def acquire_connection(user_id: int) -> bool:
    client = await require_redis()
    key = f"chat:connections:{user_id}"
    try:
        count = await client.incr(key)
        await client.expire(key, 3600)
    finally:
        await client.aclose()
    if count > settings.chat_max_connections_per_user:
        await client.decr(key)
        return False
    return True


async def release_connection(user_id: int) -> None:
    try:
        client = get_redis_client()
        key = f"chat:connections:{user_id}"
        if int(await client.get(key) or 0) > 0:
            await client.decr(key)
    except RedisError:
        pass
    finally:
        if "client" in locals():
            await client.aclose()
