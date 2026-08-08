import asyncio
import json
from datetime import datetime, timedelta
from typing import Any

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notificacion import Notificacion, SuscripcionPush
from app.models.usuario import Usuario
from app.services import notification_service


def user_id(client: TestClient, headers: dict[str, str]) -> int:
    return client.get("/auth/me", headers=headers).json()["id"]


def create_trip_and_request(client: TestClient, driver: dict[str, str], passenger: dict[str, str], create_vehicle, future_trip_payload) -> tuple[int, int]:
    vehicle = create_vehicle(driver)
    payload = {**future_trip_payload, "vehiculo_id": vehicle["id"]}
    trip = client.post("/viajes/", headers=driver, json=payload).json()
    request = client.post(f"/viajes/{trip['id']}/solicitudes", headers=passenger, json={})
    assert request.status_code == 201, request.text
    return trip["id"], request.json()["id"]


def test_internal_notifications_are_idempotent_private_and_readable(client: TestClient, auth_headers, db_session: Session, monkeypatch):
    first = auth_headers(email="notify-one@example.com")
    second = auth_headers(email="notify-two@example.com")
    first_id, second_id = user_id(client, first), user_id(client, second)

    async def no_publish(*args: Any, **kwargs: Any) -> None: pass
    monkeypatch.setattr(notification_service, "publish_notification_event", no_publish)
    monkeypatch.setattr(notification_service, "_dispatch_push", no_publish)

    for _ in range(2):
        asyncio.run(notification_service.notify(db_session, user_id=first_id, actor_id=second_id, notification_type="mensaje_nuevo", title="Nuevo mensaje", body="Hola", idempotency_key="notification:idempotent", destination_url="/reservas"))
    assert db_session.scalar(select(Notificacion).where(Notificacion.clave_idempotencia == "notification:idempotent"))
    assert len(client.get("/notificaciones", headers=first).json()["items"]) == 1
    assert client.get("/notificaciones", headers=second).json()["items"] == []
    notification_id = client.get("/notificaciones", headers=first).json()["items"][0]["id"]
    assert client.patch(f"/notificaciones/{notification_id}/leida", headers=second).status_code == 404
    assert client.patch(f"/notificaciones/{notification_id}/leida", headers=first).json()["leida"] is True
    assert client.patch("/notificaciones/leer-todas", headers=first).status_code == 200


def test_actor_is_not_notified_and_external_url_is_rejected(auth_headers, client: TestClient, db_session: Session):
    headers = auth_headers(email="notify-self@example.com")
    current_id = user_id(client, headers)
    assert asyncio.run(notification_service.notify(db_session, user_id=current_id, actor_id=current_id, notification_type="mensaje_nuevo", title="x", body="x", idempotency_key="self", destination_url="/reservas")) is None
    try:
        notification_service.validate_internal_url("https://evil.example/path")
        raise AssertionError("External URL accepted")
    except HTTPException as error:
        assert error.status_code == 422


def test_notification_target_is_contextual_and_internal() -> None:
    assert notification_service.notification_target(
        "mensaje_nuevo", reservation_id=12, conversation_id=34, fallback="/reservas"
    ) == "/reservas/12?chat=34"
    assert notification_service.notification_target("viaje_iniciado", reservation_id=12) == "/reservas/12"
    assert notification_service.notification_target("viaje_iniciado", trip_id=7) == "/mis-viajes"


def test_push_subscription_is_private_and_endpoint_is_unique(client: TestClient, auth_headers):
    owner = auth_headers(email="push-owner@example.com")
    outsider = auth_headers(email="push-other@example.com")
    payload = {"endpoint":"https://push.example/subscription-one","keys":{"p256dh":"p" * 40,"auth":"a" * 16},"dispositivo_nombre":"Teléfono"}
    created = client.post("/notificaciones/suscripciones", headers=owner, json=payload)
    assert created.status_code == 201, created.text
    repeated = client.post("/notificaciones/suscripciones", headers=owner, json=payload)
    assert repeated.status_code == 201 and repeated.json()["id"] == created.json()["id"]
    second = client.post("/notificaciones/suscripciones", headers=owner, json={**payload, "endpoint":"https://push.example/subscription-two"})
    assert second.status_code == 201 and second.json()["id"] != created.json()["id"]
    assert "endpoint" not in created.json() and "p256dh" not in created.json()
    assert client.post("/notificaciones/suscripciones", headers=outsider, json=payload).status_code == 409
    preferences = client.patch(f"/notificaciones/suscripciones/{created.json()['id']}", headers=owner, json={"mensajes":False,"reservas":True,"viaje":True})
    assert preferences.status_code == 200 and preferences.json()["mensajes"] is False
    assert client.delete(f"/notificaciones/suscripciones/{created.json()['id']}", headers=outsider).status_code == 404
    assert client.delete(f"/notificaciones/suscripciones/{created.json()['id']}", headers=owner).status_code == 204


def test_current_device_can_unsubscribe_by_endpoint(client: TestClient, auth_headers):
    owner = auth_headers(email="push-current@example.com")
    outsider = auth_headers(email="push-current-other@example.com")
    payload = {"endpoint":"https://push.example/current-device","keys":{"p256dh":"p" * 40,"auth":"a" * 16}}
    assert client.post("/notificaciones/suscripciones", headers=owner, json=payload).status_code == 201
    assert client.post("/notificaciones/suscripciones/desactivar-actual", headers=outsider, json={"endpoint":payload["endpoint"]}).status_code == 404
    assert client.post("/notificaciones/suscripciones/desactivar-actual", headers=owner, json={"endpoint":payload["endpoint"]}).status_code == 204


def test_push_configuration_and_test_endpoint_are_disabled_by_default(client: TestClient, auth_headers):
    owner = auth_headers(email="push-disabled@example.com")
    config = client.get("/notificaciones/configuracion-push")
    assert config.status_code == 200 and config.json() == {"enabled": False, "public_key": None}
    assert client.post("/notificaciones/prueba", headers=owner).status_code == 404


def test_push_dispatch_success_and_expired_subscription(client: TestClient, auth_headers, db_session: Session, monkeypatch):
    owner = auth_headers(email="push-dispatch@example.com")
    owner_id = user_id(client, owner)
    payload = {"endpoint":"https://push.example/dispatch-device","keys":{"p256dh":"p" * 40,"auth":"a" * 16}}
    subscription_id = client.post("/notificaciones/suscripciones", headers=owner, json=payload).json()["id"]
    notification = Notificacion(usuario_id=owner_id, tipo="viaje_iniciado", titulo="Viaje iniciado", cuerpo="Tu viaje comenzó.", url_destino="/reservas", clave_idempotencia="push:dispatch")
    db_session.add(notification); db_session.commit(); db_session.refresh(notification)
    monkeypatch.setattr(notification_service.settings, "web_push_enabled", True)
    monkeypatch.setattr(notification_service.settings, "web_push_vapid_public_key", "public")
    monkeypatch.setattr(notification_service.settings, "web_push_vapid_private_key", "private")
    sent = []
    monkeypatch.setattr(notification_service, "_send_web_push", lambda subscription, item: sent.append(item.id))
    assert asyncio.run(notification_service._dispatch_push(db_session, notification)) == 1
    assert sent == [notification.id]

    def expired(*args): raise LookupError("expired")
    monkeypatch.setattr(notification_service, "_send_web_push", expired)
    assert asyncio.run(notification_service._dispatch_push(db_session, notification)) == 0
    db_session.expire_all()
    assert db_session.get(SuscripcionPush, subscription_id).activa is False


def test_web_push_payload_and_vapid_claims_are_safe(monkeypatch):
    captured = {}
    monkeypatch.setattr("pywebpush.webpush", lambda **kwargs: captured.update(kwargs))
    monkeypatch.setattr(notification_service.settings, "web_push_vapid_private_key", "private-key")
    monkeypatch.setattr(notification_service.settings, "web_push_subject", "mailto:push@example.com")
    subscription = SuscripcionPush(endpoint="https://push.example/safe", p256dh="p" * 40, auth="a" * 16, usuario_id=1)
    notification = Notificacion(usuario_id=1, tipo="mensaje_nuevo", titulo="Nuevo mensaje", cuerpo="Tenés un mensaje nuevo.", url_destino="/reservas/12", clave_idempotencia="safe-payload")

    notification_service._send_web_push(subscription, notification)

    payload = json.loads(captured["data"])
    assert captured["vapid_private_key"] == "private-key"
    assert captured["vapid_claims"] == {"sub": "mailto:push@example.com"}
    assert payload["data"]["url"] == "/reservas/12"
    assert payload["tag"] == "safe-payload"
    assert "endpoint" not in payload and "p256dh" not in payload and "auth" not in payload


def test_vapid_auth_failure_preserves_subscription(client: TestClient, auth_headers, db_session: Session, monkeypatch, caplog):
    owner = auth_headers(email="push-vapid-auth@example.com")
    owner_id = user_id(client, owner)
    payload = {"endpoint":"https://push.example/vapid-auth","keys":{"p256dh":"p" * 40,"auth":"a" * 16}}
    subscription_id = client.post("/notificaciones/suscripciones", headers=owner, json=payload).json()["id"]
    notification = Notificacion(usuario_id=owner_id, tipo="viaje_iniciado", titulo="Viaje iniciado", cuerpo="Tu viaje comenzó.", url_destino="/reservas", clave_idempotencia="push:vapid-auth")
    db_session.add(notification); db_session.commit(); db_session.refresh(notification)
    monkeypatch.setattr(notification_service.settings, "web_push_enabled", True)
    monkeypatch.setattr(notification_service.settings, "web_push_vapid_public_key", "public")
    monkeypatch.setattr(notification_service.settings, "web_push_vapid_private_key", "private")

    class VapidRejected(Exception):
        response = type("Response", (), {"status_code": 403})()

    monkeypatch.setattr(notification_service, "_send_web_push", lambda *_: (_ for _ in ()).throw(VapidRejected()))
    assert asyncio.run(notification_service._dispatch_push(db_session, notification)) == 0
    db_session.expire_all()
    assert db_session.get(SuscripcionPush, subscription_id).activa is True
    assert "credenciales VAPID" in caplog.text
    assert payload["endpoint"] not in caplog.text


def test_push_failure_does_not_rollback_internal_notification(client: TestClient, auth_headers, db_session: Session, monkeypatch):
    receiver = auth_headers(email="push-failure@example.com")
    receiver_id = user_id(client, receiver)
    async def fail(*args: Any, **kwargs: Any) -> None: raise RuntimeError("push unavailable")
    async def no_publish(*args: Any, **kwargs: Any) -> None: pass
    monkeypatch.setattr(notification_service, "_dispatch_push", fail)
    monkeypatch.setattr(notification_service, "publish_notification_event", no_publish)
    result = asyncio.run(notification_service.notify(db_session, user_id=receiver_id, actor_id=None, notification_type="viaje_iniciado", title="Viaje iniciado", body="Comenzó", idempotency_key="push:failure", destination_url="/reservas"))
    assert result and db_session.get(Notificacion, result.id)


def test_request_and_chat_create_notifications(client: TestClient, auth_headers, create_vehicle, future_trip_payload):
    driver = auth_headers(email="notify-driver@example.com", nombre="Conductor")
    passenger = auth_headers(email="notify-passenger@example.com", nombre="Pasajero")
    _, request_id = create_trip_and_request(client, driver, passenger, create_vehicle, future_trip_payload)
    driver_notifications = client.get("/notificaciones", headers=driver).json()["items"]
    assert any(item["tipo"] == "solicitud_nueva" for item in driver_notifications)
    accepted = client.patch(f"/solicitudes/{request_id}/aceptar", headers=driver)
    assert accepted.status_code == 200, accepted.text
    conversation = client.get(f"/reservas/{request_id}/conversacion", headers=passenger).json()
    sent = client.post(f"/conversaciones/{conversation['id']}/mensajes", headers=passenger, json={"contenido":"¿Dónde nos encontramos?","client_message_id":"notify-chat-message"})
    assert sent.status_code == 201, sent.text
    driver_items = client.get("/notificaciones", headers=driver).json()["items"]
    types = [item["tipo"] for item in driver_items]
    assert "mensaje_nuevo" in types
    message_notification = next(item for item in driver_items if item["tipo"] == "mensaje_nuevo")
    assert message_notification["url_destino"] == f"/reservas/{request_id}?chat={conversation['id']}"
    passenger_types = [item["tipo"] for item in client.get("/notificaciones", headers=passenger).json()["items"]]
    assert "solicitud_aceptada" in passenger_types
