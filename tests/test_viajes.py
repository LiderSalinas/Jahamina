from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient


def crear_viaje(
    client: TestClient,
    headers: dict[str, str],
    payload: dict[str, str],
) -> dict[str, Any]:
    if "vehiculo_id" not in payload:
        vehicle = client.post(
            "/vehiculos",
            headers=headers,
            json={
                "marca": "Toyota",
                "modelo": "Corolla",
                "color": "Blanco",
                "matricula": f"T{uuid4().hex[:7]}",
                "capacidad": 4,
            },
        )
        assert vehicle.status_code == 201, vehicle.text
        payload = {**payload, "vehiculo_id": vehicle.json()["id"]}
    response = client.post("/viajes/", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_crear_viaje_autenticado(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    future_trip_payload: dict[str, str],
) -> None:
    trip = crear_viaje(client, auth_headers(), future_trip_payload)
    assert trip["cancelado"] is False
    assert trip["estado"] == "publicado"


def test_crear_viaje_sin_token(
    client: TestClient,
    future_trip_payload: dict[str, str],
) -> None:
    assert client.post("/viajes/", json=future_trip_payload).status_code == 401


def test_rechaza_fecha_pasada(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    future_trip_payload: dict[str, str],
) -> None:
    future_trip_payload["fecha"] = (
        datetime.now() - timedelta(minutes=1)
    ).isoformat()
    response = client.post(
        "/viajes/",
        headers=auth_headers(),
        json=future_trip_payload,
    )
    assert response.status_code == 422


def test_rechaza_origen_igual_a_destino(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    future_trip_payload: dict[str, str],
) -> None:
    future_trip_payload["destino"] = " asunción "
    response = client.post(
        "/viajes/",
        headers=auth_headers(),
        json=future_trip_payload,
    )
    assert response.status_code == 422


def test_rechaza_ubicaciones_invalidas(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    future_trip_payload: dict[str, str],
) -> None:
    future_trip_payload["origen"] = " "
    future_trip_payload["destino"] = ""
    response = client.post(
        "/viajes/",
        headers=auth_headers(),
        json=future_trip_payload,
    )
    assert response.status_code == 422


def test_listar_disponibles_excluye_cancelados_y_pasados(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    future_trip_payload: dict[str, str],
    db_session: Any,
) -> None:
    from app.models.viaje_model import Viaje

    headers = auth_headers()
    active = crear_viaje(client, headers, future_trip_payload)
    cancelled_payload = {
        **future_trip_payload,
        "destino": "Luque",
    }
    cancelled = crear_viaje(client, headers, cancelled_payload)
    client.put(f"/viajes/cancelar/{cancelled['id']}", headers=headers)
    db_session.add(
        Viaje(
            origen="Asunción",
            destino="Capiatá",
            fecha=datetime.now() - timedelta(days=1),
            creador_id=active["creador_id"],
            cancelado=False,
            cupos_totales=1,
            cupos_disponibles=1,
            punto_salida="Asunción",
            punto_llegada="Capiatá",
            estado="publicado",
        )
    )
    db_session.commit()

    response = client.get("/viajes/disponibles", headers=headers)
    assert response.status_code == 200
    returned_ids = [trip["id"] for trip in response.json()]
    assert active["id"] in returned_ids
    assert cancelled["id"] not in returned_ids


def test_consultar_mis_viajes(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    future_trip_payload: dict[str, str],
) -> None:
    headers = auth_headers()
    trip = crear_viaje(client, headers, future_trip_payload)
    response = client.get("/viajes/mis-viajes", headers=headers)
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [trip["id"]]


def test_cancelar_viaje_propio_y_rechazar_repeticion(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    future_trip_payload: dict[str, str],
) -> None:
    headers = auth_headers()
    trip = crear_viaje(client, headers, future_trip_payload)
    assert client.put(
        f"/viajes/cancelar/{trip['id']}",
        headers=headers,
    ).status_code == 200
    assert client.put(
        f"/viajes/cancelar/{trip['id']}",
        headers=headers,
    ).status_code == 409


def test_impedir_cancelacion_por_otro_usuario(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    future_trip_payload: dict[str, str],
) -> None:
    owner = auth_headers(email="owner@example.com")
    other = auth_headers(email="other@example.com")
    trip = crear_viaje(client, owner, future_trip_payload)
    response = client.put(f"/viajes/cancelar/{trip['id']}", headers=other)
    assert response.status_code == 403


def test_pasajeros_flujo_y_reglas(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    future_trip_payload: dict[str, str],
) -> None:
    owner = auth_headers(email="owner@example.com")
    passenger = auth_headers(email="passenger@example.com")
    trip = crear_viaje(client, owner, future_trip_payload)

    assert client.put(
        f"/viajes/unirse/{trip['id']}",
        headers=owner,
    ).status_code == 400
    joined = client.put(
        f"/viajes/unirse/{trip['id']}",
        headers=passenger,
    )
    assert joined.status_code == 201
    assert joined.json()["viaje_id"] == trip["id"]
    assert joined.json()["estado"] == "pendiente"
    assert client.put(
        f"/viajes/unirse/{trip['id']}",
        headers=passenger,
    ).status_code == 409

    accepted = client.patch(
        f"/solicitudes/{joined.json()['id']}/aceptar",
        headers=owner,
    )
    assert accepted.status_code == 200
    response = client.get("/viajes/unidos", headers=passenger)
    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [trip["id"]]


def test_impedir_union_a_cancelado_o_inexistente(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    future_trip_payload: dict[str, str],
) -> None:
    owner = auth_headers(email="owner@example.com")
    passenger = auth_headers(email="passenger@example.com")
    trip = crear_viaje(client, owner, future_trip_payload)
    client.put(f"/viajes/cancelar/{trip['id']}", headers=owner)

    assert client.put(
        f"/viajes/unirse/{trip['id']}",
        headers=passenger,
    ).status_code == 400
    assert client.put(
        "/viajes/unirse/999999",
        headers=passenger,
    ).status_code == 404
