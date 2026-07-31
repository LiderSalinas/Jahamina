import time
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.redis import get_redis_client
from app.core.settings import settings


def accepted_chat(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    create_vehicle: Callable[..., dict[str, Any]],
    future_trip_payload: dict[str, Any],
) -> dict[str, Any]:
    driver = auth_headers(email=f"driver-{uuid4().hex}@example.com")
    passenger = auth_headers(email=f"passenger-{uuid4().hex}@example.com")
    outsider = auth_headers(email=f"outsider-{uuid4().hex}@example.com")
    vehicle = create_vehicle(driver)
    trip = client.post(
        "/viajes/",
        headers=driver,
        json={**future_trip_payload, "vehiculo_id": vehicle["id"]},
    ).json()
    request = client.post(
        f"/viajes/{trip['id']}/solicitudes",
        headers=passenger,
        json={},
    ).json()
    response = client.patch(
        f"/solicitudes/{request['id']}/aceptar", headers=driver
    )
    assert response.status_code == 200, response.text
    conversation_response = client.get(
        f"/reservas/{request['id']}/conversacion", headers=passenger
    )
    assert conversation_response.status_code == 200
    return {
        "driver": driver,
        "passenger": passenger,
        "outsider": outsider,
        "trip": trip,
        "request": request,
        "conversation": conversation_response.json(),
    }


def test_chat_created_only_when_accepted(
    client, auth_headers, create_vehicle, future_trip_payload
):
    driver = auth_headers()
    passenger = auth_headers()
    vehicle = create_vehicle(driver)
    trip = client.post(
        "/viajes/",
        headers=driver,
        json={**future_trip_payload, "vehiculo_id": vehicle["id"]},
    ).json()
    request = client.post(
        f"/viajes/{trip['id']}/solicitudes", headers=passenger, json={}
    ).json()
    pending = client.get(
        f"/reservas/{request['id']}/conversacion", headers=passenger
    )
    assert pending.status_code == 409
    client.patch(f"/solicitudes/{request['id']}/aceptar", headers=driver)
    conversation = client.get(
        f"/reservas/{request['id']}/conversacion", headers=driver
    )
    assert conversation.status_code == 200
    history = client.get(
        f"/conversaciones/{conversation.json()['id']}/mensajes",
        headers=passenger,
    ).json()
    assert history["items"][0]["tipo"] == "sistema"
    assert "aceptada" in history["items"][0]["contenido"]


def test_participants_authorized_and_outsider_hidden(
    client, auth_headers, create_vehicle, future_trip_payload
):
    chat = accepted_chat(client, auth_headers, create_vehicle, future_trip_payload)
    conversation_id = chat["conversation"]["id"]
    assert client.get(
        f"/conversaciones/{conversation_id}", headers=chat["driver"]
    ).status_code == 200
    assert client.get(
        f"/conversaciones/{conversation_id}", headers=chat["passenger"]
    ).status_code == 200
    assert client.get(
        f"/conversaciones/{conversation_id}", headers=chat["outsider"]
    ).status_code == 404
    assert client.get(
        f"/solicitudes/{chat['request']['id']}", headers=chat["outsider"]
    ).status_code == 404


def test_related_reservations_for_driver_and_passenger_without_duplicates(
    client, auth_headers, create_vehicle, future_trip_payload
):
    chat = accepted_chat(client, auth_headers, create_vehicle, future_trip_payload)
    request_id = chat["request"]["id"]
    for role, headers in (
        ("conductor", chat["driver"]),
        ("pasajero", chat["passenger"]),
    ):
        response = client.get("/reservas/relacionadas", headers=headers)
        assert response.status_code == 200
        related = [item for item in response.json() if item["reserva_id"] == request_id]
        assert len(related) == 1
        assert related[0]["rol"] == role
        assert related[0]["conversacion_id"] == chat["conversation"]["id"]
        assert related[0]["participante"]


def test_rest_message_idempotence_validation_history_and_read(
    client, auth_headers, create_vehicle, future_trip_payload
):
    chat = accepted_chat(client, auth_headers, create_vehicle, future_trip_payload)
    conversation_id = chat["conversation"]["id"]
    path = f"/conversaciones/{conversation_id}/mensajes"
    client_id = str(uuid4())
    first = client.post(
        path,
        headers=chat["passenger"],
        json={"contenido": "Nos vemos en el punto", "client_message_id": client_id},
    )
    duplicate = client.post(
        path,
        headers=chat["passenger"],
        json={"contenido": "Nos vemos en el punto", "client_message_id": client_id},
    )
    assert first.status_code == duplicate.status_code == 201
    assert first.json()["id"] == duplicate.json()["id"]
    assert client.post(path, headers=chat["passenger"], json={"contenido": "  "}).status_code == 422
    assert client.post(path, headers=chat["passenger"], json={"contenido": "x" * 1001}).status_code == 422
    history = client.get(path, headers=chat["driver"], params={"limit": 1}).json()
    assert len(history["items"]) == 1
    assert history["next_cursor"] is not None
    unread = client.get("/conversaciones/no-leidos", headers=chat["driver"]).json()
    assert unread["total"] == 1
    read = client.patch(
        f"/conversaciones/{conversation_id}/leido", headers=chat["driver"]
    )
    assert read.json()["mensajes_marcados"] == 1
    assert client.get("/conversaciones/no-leidos", headers=chat["driver"]).json()["total"] == 0
    assert "hashed_password" not in first.text


def test_ticket_single_use_websocket_and_realtime_message(
    client, auth_headers, create_vehicle, future_trip_payload
):
    chat = accepted_chat(client, auth_headers, create_vehicle, future_trip_payload)
    conversation_id = chat["conversation"]["id"]
    ticket_response = client.post(
        f"/conversaciones/{conversation_id}/ws-ticket",
        headers=chat["passenger"],
    )
    assert ticket_response.status_code == 200
    ticket = ticket_response.json()["ticket"]
    with client.websocket_connect(f"/ws/chat?ticket={ticket}") as websocket:
        assert websocket.receive_json()["type"] == "connected"
        websocket.send_json(
            {
                "type": "message.send",
                "data": {
                    "contenido": "Mensaje en tiempo real",
                    "client_message_id": str(uuid4()),
                },
            }
        )
        event = websocket.receive_json()
        assert event["type"] == "message.created"
        assert event["data"]["contenido"] == "Mensaje en tiempo real"
        websocket.send_json({"type": "ping", "data": {}})
        assert websocket.receive_json()["type"] == "pong"
    try:
        with client.websocket_connect(f"/ws/chat?ticket={ticket}") as reused:
            reused.receive_json()
        assert False, "El ticket reutilizado debía rechazarse"
    except Exception:
        pass


def test_websocket_broadcast_reaches_both_participants(
    client, auth_headers, create_vehicle, future_trip_payload
):
    chat = accepted_chat(client, auth_headers, create_vehicle, future_trip_payload)
    conversation_id = chat["conversation"]["id"]
    driver_ticket = client.post(
        f"/conversaciones/{conversation_id}/ws-ticket",
        headers=chat["driver"],
    ).json()["ticket"]
    passenger_ticket = client.post(
        f"/conversaciones/{conversation_id}/ws-ticket",
        headers=chat["passenger"],
    ).json()["ticket"]
    with client.websocket_connect(
        f"/ws/chat?ticket={driver_ticket}"
    ) as driver_socket, client.websocket_connect(
        f"/ws/chat?ticket={passenger_ticket}"
    ) as passenger_socket:
        assert driver_socket.receive_json()["type"] == "connected"
        assert passenger_socket.receive_json()["type"] == "connected"
        passenger_socket.send_json(
            {
                "type": "message.send",
                "data": {
                    "contenido": "Mensaje para ambos",
                    "client_message_id": str(uuid4()),
                },
            }
        )
        driver_event = driver_socket.receive_json()
        passenger_event = passenger_socket.receive_json()
        assert driver_event["type"] == "message.created"
        assert passenger_event["type"] == "message.created"
        assert driver_event["data"]["id"] == passenger_event["data"]["id"]

    related = client.get(
        "/reservas/relacionadas", headers=chat["driver"]
    ).json()
    item = next(
        row for row in related if row["reserva_id"] == chat["request"]["id"]
    )
    unread = client.get(
        "/conversaciones/no-leidos", headers=chat["driver"]
    ).json()
    assert item["no_leidos"] == unread["total"] == 1


def test_ticket_access_expiration_closed_chat_and_rate_limit(
    client, auth_headers, create_vehicle, future_trip_payload, monkeypatch
):
    chat = accepted_chat(client, auth_headers, create_vehicle, future_trip_payload)
    conversation_id = chat["conversation"]["id"]
    assert client.post(
        f"/conversaciones/{conversation_id}/ws-ticket",
        headers=chat["outsider"],
    ).status_code == 404

    monkeypatch.setattr(settings, "ws_ticket_expire_seconds", 1)
    expired = client.post(
        f"/conversaciones/{conversation_id}/ws-ticket",
        headers=chat["driver"],
    ).json()["ticket"]
    time.sleep(1.1)
    try:
        with client.websocket_connect(f"/ws/chat?ticket={expired}") as websocket:
            websocket.receive_json()
        assert False, "El ticket vencido debía rechazarse"
    except Exception:
        pass

    monkeypatch.setattr(settings, "chat_rate_limit_messages", 1)
    path = f"/conversaciones/{conversation_id}/mensajes"
    assert client.post(path, headers=chat["driver"], json={"contenido": "Uno"}).status_code == 201
    assert client.post(path, headers=chat["driver"], json={"contenido": "Dos"}).status_code == 429

    client.patch(
        f"/solicitudes/{chat['request']['id']}/cancelar",
        headers=chat["passenger"],
    )
    detail = client.get(
        f"/conversaciones/{conversation_id}", headers=chat["passenger"]
    )
    assert detail.status_code == 200
    assert detail.json()["puede_escribir"] is False
    monkeypatch.setattr(settings, "chat_rate_limit_messages", 10)
    assert client.post(
        path, headers=chat["passenger"], json={"contenido": "Tarde"}
    ).status_code == 409
