from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient
from app.schemas.map_schema import RouteResponse


def mobility_flow(client: TestClient, auth_headers, create_vehicle) -> dict[str, Any]:
    driver = auth_headers(email=f"geo-driver-{uuid4().hex}@example.com")
    passenger = auth_headers(email=f"geo-passenger-{uuid4().hex}@example.com")
    outsider = auth_headers(email=f"geo-outsider-{uuid4().hex}@example.com")
    vehicle = create_vehicle(driver)
    payload = {
        "origen": "Asunción",
        "destino": "Luque",
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "vehiculo_id": vehicle["id"],
        "cupos_totales": 2,
        "punto_salida": "Centro",
        "punto_llegada": "Terminal",
        "origen_latitud": -25.2867,
        "origen_longitud": -57.3333,
        "destino_latitud": -25.2637,
        "destino_longitud": -57.5759,
        "punto_salida_latitud": -25.2867,
        "punto_salida_longitud": -57.3333,
        "punto_llegada_latitud": -25.2637,
        "punto_llegada_longitud": -57.5759,
    }
    trip_response = client.post("/viajes/", headers=driver, json=payload)
    assert trip_response.status_code == 201, trip_response.text
    trip = trip_response.json()
    request = client.post(f"/viajes/{trip['id']}/solicitudes", headers=passenger, json={}).json()
    client.patch(f"/solicitudes/{request['id']}/aceptar", headers=driver)
    return {"driver": driver, "passenger": passenger, "outsider": outsider, "trip": trip, "request": request}


def move_driver_to_tracking_state(client: TestClient, flow: dict[str, Any]) -> None:
    trip_id = flow["trip"]["id"]
    assert client.post(f"/viajes/{trip_id}/acciones/preparar-salida", headers=flow["driver"]).status_code == 200
    assert client.post(f"/viajes/{trip_id}/acciones/salir", headers=flow["driver"]).status_code == 200


def test_trip_coordinates_are_validated(client, auth_headers, create_vehicle):
    driver = auth_headers()
    vehicle = create_vehicle(driver)
    payload = {
        "origen": "Asunción", "destino": "Luque",
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "vehiculo_id": vehicle["id"], "cupos_totales": 2,
        "punto_salida": "Centro", "punto_llegada": "Terminal",
        "origen_latitud": 91, "origen_longitud": -57,
    }
    assert client.post("/viajes/", headers=driver, json=payload).status_code == 422
    payload["origen_latitud"] = -25.28
    payload["origen_longitud"] = -181
    assert client.post("/viajes/", headers=driver, json=payload).status_code == 422


def test_meeting_point_proposal_confirmation_and_security(client, auth_headers, create_vehicle):
    flow = mobility_flow(client, auth_headers, create_vehicle)
    request_id = flow["request"]["id"]
    path = f"/reservas/{request_id}/punto-encuentro"
    assert client.get(path, headers=flow["outsider"]).status_code == 404
    proposal = client.post(f"{path}/proponer", headers=flow["passenger"], json={"texto": "Entrada principal", "latitude": -25.28, "longitude": -57.57})
    assert proposal.status_code == 200
    assert proposal.json()["estado"] == "propuesto"
    confirmed = client.patch(f"{path}/confirmar", headers=flow["driver"])
    assert confirmed.json()["estado"] == "confirmado"
    repeated = client.patch(f"{path}/confirmar", headers=flow["driver"])
    assert repeated.json()["estado"] == "confirmado"
    history = client.get(f"/conversaciones/{client.get(f'/reservas/{request_id}/conversacion', headers=flow['driver']).json()['id']}/mensajes", headers=flow["driver"]).json()
    assert sum("quedó confirmado" in item["contenido"] for item in history["items"]) == 1


def test_tracking_lifecycle_location_and_authorization(client, auth_headers, create_vehicle):
    flow = mobility_flow(client, auth_headers, create_vehicle)
    trip_id = flow["trip"]["id"]
    move_driver_to_tracking_state(client, flow)
    assert client.post(f"/viajes/{trip_id}/seguimiento/iniciar", headers=flow["passenger"]).status_code == 404
    started = client.post(f"/viajes/{trip_id}/seguimiento/iniciar", headers=flow["driver"])
    assert started.status_code == 200
    assert started.json()["compartir_ubicacion"] is False
    assert client.post(f"/viajes/{trip_id}/ubicacion", headers=flow["driver"], json={"latitude": -25.28, "longitude": -57.57, "accuracy": 10}).status_code == 409
    client.patch(f"/viajes/{trip_id}/seguimiento/compartir", headers=flow["driver"], json={"enabled": True})
    location = client.post(f"/viajes/{trip_id}/ubicacion", headers=flow["driver"], json={"latitude": -25.28, "longitude": -57.57, "accuracy": 10})
    assert location.status_code == 200
    assert client.get(f"/viajes/{trip_id}/ubicacion-actual", headers=flow["passenger"]).status_code == 200
    assert client.get(f"/viajes/{trip_id}/ubicacion-actual", headers=flow["outsider"]).status_code == 404
    assert client.patch(f"/viajes/{trip_id}/seguimiento/pausar", headers=flow["driver"]).json()["estado"] == "pausado"
    assert client.patch(f"/viajes/{trip_id}/seguimiento/reanudar", headers=flow["driver"]).json()["estado"] == "activo"
    assert client.patch(f"/viajes/{trip_id}/seguimiento/finalizar", headers=flow["driver"]).json()["estado"] == "finalizado"
    assert client.get(f"/viajes/{trip_id}/ubicacion-actual", headers=flow["passenger"]).status_code == 404


def test_location_websocket_ticket_and_broadcast(client, auth_headers, create_vehicle):
    flow = mobility_flow(client, auth_headers, create_vehicle)
    trip_id = flow["trip"]["id"]
    move_driver_to_tracking_state(client, flow)
    client.post(f"/viajes/{trip_id}/seguimiento/iniciar", headers=flow["driver"])
    client.patch(f"/viajes/{trip_id}/seguimiento/compartir", headers=flow["driver"], json={"enabled": True})
    publisher = client.post(f"/viajes/{trip_id}/ubicacion/ws-ticket", headers=flow["driver"]).json()
    subscriber = client.post(f"/viajes/{trip_id}/ubicacion/ws-ticket", headers=flow["passenger"]).json()
    assert publisher["role"] == "publisher" and subscriber["role"] == "subscriber"
    with client.websocket_connect(f"/ws/ubicacion?ticket={publisher['ticket']}") as pub, client.websocket_connect(f"/ws/ubicacion?ticket={subscriber['ticket']}") as sub:
        assert pub.receive_json()["type"] == "connected"
        assert sub.receive_json()["type"] == "connected"
        pub.send_json({"type": "location.update", "data": {"latitude": -25.28, "longitude": -57.57, "accuracy": 8}})
        assert pub.receive_json()["type"] == "location.updated"
        assert sub.receive_json()["type"] == "location.updated"


def test_next_stop_eta_uses_route_cache_and_keeps_authorization(client, auth_headers, create_vehicle, monkeypatch):
    flow = mobility_flow(client, auth_headers, create_vehicle)
    trip_id = flow["trip"]["id"]
    request_id = flow["request"]["id"]
    move_driver_to_tracking_state(client, flow)
    calls = 0

    async def fake_route(origin, destination):
        nonlocal calls
        calls += 1
        assert origin.latitude == -25.28
        assert destination.latitude is not None
        return RouteResponse(distance_km=2.8, duration_minutes=7)

    monkeypatch.setattr("app.services.map_service.route", fake_route)
    client.post(f"/viajes/{trip_id}/seguimiento/iniciar", headers=flow["driver"])
    client.patch(f"/viajes/{trip_id}/seguimiento/compartir", headers=flow["driver"], json={"enabled": True})
    client.post(f"/viajes/{trip_id}/ubicacion", headers=flow["driver"], json={"latitude": -25.28, "longitude": -57.57, "accuracy": 10})

    first = client.get(f"/reservas/{request_id}/ubicacion-contexto", headers=flow["passenger"])
    second = client.get(f"/reservas/{request_id}/ubicacion-contexto", headers=flow["passenger"])
    assert first.status_code == 200
    assert first.json()["estado"] == "disponible"
    assert first.json()["distancia_metros"] == 2800
    assert first.json()["duracion_segundos"] == 420
    assert second.status_code == 200
    assert calls == 1
    assert client.get(f"/reservas/{request_id}/ubicacion-contexto", headers=flow["outsider"]).status_code == 404
