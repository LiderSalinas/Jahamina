import asyncio
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


def test_push_subscription_is_private_and_endpoint_is_unique(client: TestClient, auth_headers):
    owner = auth_headers(email="push-owner@example.com")
    outsider = auth_headers(email="push-other@example.com")
    payload = {"endpoint":"https://push.example/subscription-one","keys":{"p256dh":"p" * 40,"auth":"a" * 16},"dispositivo_nombre":"Teléfono"}
    created = client.post("/notificaciones/suscripciones", headers=owner, json=payload)
    assert created.status_code == 201, created.text
    assert "endpoint" not in created.json() and "p256dh" not in created.json()
    assert client.post("/notificaciones/suscripciones", headers=outsider, json=payload).status_code == 409
    preferences = client.patch(f"/notificaciones/suscripciones/{created.json()['id']}", headers=owner, json={"mensajes":False,"reservas":True,"viaje":True})
    assert preferences.status_code == 200 and preferences.json()["mensajes"] is False
    assert client.delete(f"/notificaciones/suscripciones/{created.json()['id']}", headers=outsider).status_code == 404
    assert client.delete(f"/notificaciones/suscripciones/{created.json()['id']}", headers=owner).status_code == 204


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
    types = [item["tipo"] for item in client.get("/notificaciones", headers=driver).json()["items"]]
    assert "mensaje_nuevo" in types
    passenger_types = [item["tipo"] for item in client.get("/notificaciones", headers=passenger).json()["items"]]
    assert "solicitud_aceptada" in passenger_types
