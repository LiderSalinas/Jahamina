from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient


def _accepted(client: TestClient, auth_headers: Callable[..., dict[str, str]], create_vehicle: Callable[..., dict[str, Any]], suffix: str):
    driver = auth_headers(email=f"roadmap-driver-{suffix}@example.com", nombre="Rubén")
    passenger = auth_headers(email=f"roadmap-passenger-{suffix}@example.com", nombre="Ramón")
    vehicle = create_vehicle(driver, capacidad=4)
    trip = client.post("/viajes/", headers=driver, json={"origen":"San Juan", "destino":"Asunción", "fecha":(datetime.now()+timedelta(days=1)).isoformat(), "vehiculo_id":vehicle["id"], "cupos_totales":3, "punto_salida":"Centro de San Juan", "punto_llegada":"Centro de Asunción"}).json()
    request = client.post(f"/viajes/{trip['id']}/solicitudes", headers=passenger, json={}).json()
    accepted = client.patch(f"/solicitudes/{request['id']}/aceptar", headers=driver)
    assert accepted.status_code == 200
    return driver, passenger, trip, request


def test_both_participants_get_consolidated_roadmap_and_outsider_is_hidden(client, auth_headers, create_vehicle):
    driver, passenger, trip, request = _accepted(client, auth_headers, create_vehicle, "read")
    outsider = auth_headers(email="roadmap-outsider@example.com")
    for headers, role in ((driver, "conductor"), (passenger, "pasajero")):
        response = client.get(f"/reservas/{request['id']}/hoja-ruta", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["reserva"]["rol_actual"] == role
        assert body["viaje"]["id"] == trip["id"]
        assert body["conductor"]["nombre"] == "Rubén"
        assert body["pasajero_actual"]["nombre"] == "Ramón"
        assert body["vehiculo"]["marca"] == "Toyota"
        assert body["ocupacion"] == {"ocupados": 1, "totales": 3, "pendientes": 0}
        assert [stop["tipo"] for stop in body["paradas"]] == ["origen", "destino"]
        assert body["hoja_ruta"][0]["id"] == "reserva-confirmada"
        assert body["hoja_ruta"][0]["estado"] == "completado"
        assert body["eventos"][0]["tipo"] == "reserva_confirmada"
        assert "hashed_password" not in response.text
        assert "email" not in response.text
    assert client.get(f"/reservas/{request['id']}/hoja-ruta", headers=outsider).status_code == 404
    assert client.get("/reservas/999999/hoja-ruta", headers=driver).status_code == 404


def test_roadmap_derives_meeting_point_and_cancelled_privacy(client, auth_headers, create_vehicle):
    driver, passenger, _trip, request = _accepted(client, auth_headers, create_vehicle, "meeting")
    reservation_id = request["id"]
    proposed = client.post(f"/reservas/{reservation_id}/punto-encuentro/proponer", headers=driver, json={"texto":"Terminal de San Miguel", "latitude":-25.30, "longitude":-57.60})
    assert proposed.status_code == 200
    assert client.patch(f"/reservas/{reservation_id}/punto-encuentro/confirmar", headers=passenger).status_code == 200
    body = client.get(f"/reservas/{reservation_id}/hoja-ruta", headers=passenger).json()
    assert body["punto_encuentro"]["estado"] == "confirmado"
    assert body["punto_encuentro"]["zona_general"] == "Terminal de San Miguel"
    assert [stop["tipo"] for stop in body["paradas"]] == ["origen", "recogida", "destino"]
    assert any(step["id"] == "punto-confirmado" and step["estado"] == "completado" for step in body["hoja_ruta"])
    assert client.patch(f"/solicitudes/{reservation_id}/cancelar", headers=passenger).status_code == 200
    cancelled = client.get(f"/reservas/{reservation_id}/hoja-ruta", headers=driver)
    assert cancelled.status_code == 200
    assert cancelled.json()["punto_encuentro"]["latitud"] is None
    assert cancelled.json()["permisos"]["puede_ver_punto_exacto"] is False


def test_pending_reservation_does_not_expose_roadmap(client, auth_headers, create_vehicle):
    driver = auth_headers(email="roadmap-pending-driver@example.com")
    passenger = auth_headers(email="roadmap-pending-passenger@example.com")
    vehicle = create_vehicle(driver)
    trip = client.post("/viajes/", headers=driver, json={"origen":"Ciudad A", "destino":"Ciudad B", "fecha":(datetime.now()+timedelta(days=1)).isoformat(), "vehiculo_id":vehicle["id"], "cupos_totales":2, "punto_salida":"Zona A", "punto_llegada":"Zona B"}).json()
    request = client.post(f"/viajes/{trip['id']}/solicitudes", headers=passenger, json={}).json()
    assert client.get(f"/reservas/{request['id']}/hoja-ruta", headers=passenger).status_code == 409


def test_state_machine_permissions_idempotency_and_system_messages(client, auth_headers, create_vehicle):
    driver, passenger, trip, request = _accepted(client, auth_headers, create_vehicle, "flow")
    reservation_id = request["id"]
    assert client.post(f"/viajes/{trip['id']}/acciones/preparar-salida", headers=passenger).status_code == 404
    ready = client.post(f"/reservas/{reservation_id}/acciones/listo", headers=passenger)
    assert ready.status_code == 200 and ready.json()["estado_pasajero"]["estado"] == "listo"
    repeated = client.post(f"/reservas/{reservation_id}/acciones/listo", headers=passenger)
    assert repeated.status_code == 200
    prepared = client.post(f"/viajes/{trip['id']}/acciones/preparar-salida", headers=driver)
    assert prepared.status_code == 200 and prepared.json()["viaje"]["estado"] == "preparando_salida"
    assert client.post(f"/viajes/{trip['id']}/acciones/iniciar", headers=driver).status_code == 409
    assert client.post(f"/viajes/{trip['id']}/acciones/salir", headers=driver).status_code == 200
    assert client.post(f"/viajes/{trip['id']}/acciones/llegar", headers=driver).status_code == 200
    assert client.post(f"/reservas/{reservation_id}/acciones/recoger", headers=driver).status_code == 200
    boarded = client.post(f"/reservas/{reservation_id}/acciones/abordar", headers=driver)
    assert boarded.status_code == 200 and boarded.json()["viaje"]["estado"] == "abordaje"
    assert client.post(f"/viajes/{trip['id']}/acciones/iniciar", headers=driver).status_code == 200
    assert client.post(f"/viajes/{trip['id']}/acciones/pausar", headers=driver).status_code == 200
    assert client.post(f"/viajes/{trip['id']}/acciones/reanudar", headers=driver).status_code == 200
    finished = client.post(f"/viajes/{trip['id']}/acciones/finalizar", headers=driver)
    assert finished.status_code == 200 and finished.json()["viaje"]["estado"] == "finalizado"
    assert client.post(f"/reservas/{reservation_id}/acciones/listo", headers=passenger).status_code == 409
    events = finished.json()["eventos"]
    assert len([event for event in events if event["tipo"] == "pasajero_listo"]) == 1
    conversation = client.get(f"/reservas/{reservation_id}/conversacion", headers=passenger).json()
    messages = client.get(f"/conversaciones/{conversation['id']}/mensajes", headers=passenger).json()["items"]
    assert any(message["tipo"] == "sistema" and "viaje" in message["contenido"].lower() for message in messages)
