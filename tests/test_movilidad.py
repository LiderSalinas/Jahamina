from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.core.db import SessionLocal
from app.models.solicitud_viaje import SolicitudViaje
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.models.viaje_model import Viaje
from app.services.solicitud_service import responder_solicitud


def trip_payload(vehicle_id: int, seats: int = 2) -> dict[str, Any]:
    return {
        "origen": "Asunción",
        "destino": "Luque",
        "fecha": (datetime.now() + timedelta(days=1)).isoformat(),
        "vehiculo_id": vehicle_id,
        "cupos_totales": seats,
        "descripcion": "Viaje de prueba",
        "punto_salida": "Plaza Uruguaya",
        "punto_llegada": "Centro de Luque",
    }


def test_crud_vehiculo_y_matricula_normalizada(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
) -> None:
    headers = auth_headers()
    response = client.post(
        "/vehiculos",
        headers=headers,
        json={
            "marca": "Toyota",
            "modelo": "Vitz",
            "color": "Azul",
            "matricula": "abc-123",
            "capacidad": 4,
        },
    )
    assert response.status_code == 201
    vehicle = response.json()
    assert vehicle["matricula"] == "ABC123"
    assert "propietario" not in vehicle
    assert client.get("/vehiculos", headers=headers).json()[0]["id"] == vehicle["id"]
    assert client.get(
        f"/vehiculos/{vehicle['id']}",
        headers=headers,
    ).status_code == 200
    updated = client.patch(
        f"/vehiculos/{vehicle['id']}",
        headers=headers,
        json={"color": "Rojo"},
    )
    assert updated.status_code == 200
    assert updated.json()["color"] == "Rojo"
    disabled = client.patch(
        f"/vehiculos/{vehicle['id']}/desactivar",
        headers=headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["activo"] is False


def test_matricula_duplicada_y_capacidad_invalida(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    create_vehicle: Callable[..., dict[str, Any]],
) -> None:
    headers = auth_headers()
    create_vehicle(headers, matricula="ABC123")
    duplicate = client.post(
        "/vehiculos",
        headers=headers,
        json={
            "marca": "Kia",
            "modelo": "Rio",
            "color": "Negro",
            "matricula": "abc-123",
            "capacidad": 4,
        },
    )
    assert duplicate.status_code == 409
    for capacity in (0, 9):
        invalid = client.post(
            "/vehiculos",
            headers=headers,
            json={
                "marca": "Kia",
                "modelo": "Rio",
                "color": "Negro",
                "matricula": f"CAP{capacity}X",
                "capacidad": capacity,
            },
        )
        assert invalid.status_code == 422


def test_autorizacion_vehiculo(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    create_vehicle: Callable[..., dict[str, Any]],
) -> None:
    owner = auth_headers(email="vehicle-owner@example.com")
    other = auth_headers(email="vehicle-other@example.com")
    vehicle = create_vehicle(owner)
    assert client.get(
        f"/vehiculos/{vehicle['id']}",
        headers=other,
    ).status_code == 403
    assert client.patch(
        f"/vehiculos/{vehicle['id']}",
        headers=other,
        json={"color": "Rojo"},
    ).status_code == 403
    assert client.patch(
        f"/vehiculos/{vehicle['id']}/desactivar",
        headers=other,
    ).status_code == 403


def test_viaje_rechaza_vehiculo_ajeno_inactivo_y_cupos_excesivos(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    create_vehicle: Callable[..., dict[str, Any]],
) -> None:
    owner = auth_headers(email="trip-owner@example.com")
    other = auth_headers(email="trip-other@example.com")
    vehicle = create_vehicle(owner, capacidad=2)
    assert client.post(
        "/viajes/",
        headers=other,
        json=trip_payload(vehicle["id"]),
    ).status_code == 403
    assert client.post(
        "/viajes/",
        headers=owner,
        json=trip_payload(vehicle["id"], seats=3),
    ).status_code == 400
    client.patch(f"/vehiculos/{vehicle['id']}/desactivar", headers=owner)
    assert client.post(
        "/viajes/",
        headers=owner,
        json=trip_payload(vehicle["id"]),
    ).status_code == 400


def test_solicitudes_aceptacion_cancelacion_y_cupos(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    create_vehicle: Callable[..., dict[str, Any]],
) -> None:
    owner = auth_headers(email="request-owner@example.com")
    passenger = auth_headers(email="request-passenger@example.com")
    outsider = auth_headers(email="request-outsider@example.com")
    vehicle = create_vehicle(owner, capacidad=2)
    trip = client.post(
        "/viajes/",
        headers=owner,
        json=trip_payload(vehicle["id"], seats=1),
    ).json()

    assert client.post(
        f"/viajes/{trip['id']}/solicitudes",
        headers=owner,
        json={},
    ).status_code == 400
    request = client.post(
        f"/viajes/{trip['id']}/solicitudes",
        headers=passenger,
        json={"mensaje_inicial": "¿Puedo acompañarte?"},
    )
    assert request.status_code == 201
    request_id = request.json()["id"]
    assert client.post(
        f"/viajes/{trip['id']}/solicitudes",
        headers=passenger,
        json={},
    ).status_code == 409
    assert client.get(
        f"/viajes/{trip['id']}/solicitudes",
        headers=outsider,
    ).status_code == 403
    assert client.get(
        f"/solicitudes/{request_id}",
        headers=outsider,
    ).status_code == 403
    assert client.patch(
        f"/solicitudes/{request_id}/aceptar",
        headers=outsider,
    ).status_code == 403
    assert client.patch(
        f"/solicitudes/{request_id}/cancelar",
        headers=outsider,
    ).status_code == 403

    accepted = client.patch(
        f"/solicitudes/{request_id}/aceptar",
        headers=owner,
    )
    assert accepted.status_code == 200
    assert accepted.json()["estado"] == "aceptada"
    full_trip = client.get("/viajes/mis-viajes", headers=owner).json()[0]
    assert full_trip["cupos_disponibles"] == 0
    assert full_trip["estado"] == "completo"

    cancelled = client.patch(
        f"/solicitudes/{request_id}/cancelar",
        headers=passenger,
    )
    assert cancelled.status_code == 200
    restored = client.get("/viajes/mis-viajes", headers=owner).json()[0]
    assert restored["cupos_disponibles"] == 1
    assert restored["estado"] == "publicado"


def test_rechazo_no_descuenta_cupo_y_estados_viaje(
    client: TestClient,
    auth_headers: Callable[..., dict[str, str]],
    create_vehicle: Callable[..., dict[str, Any]],
) -> None:
    owner = auth_headers(email="state-owner@example.com")
    passenger = auth_headers(email="state-passenger@example.com")
    other = auth_headers(email="state-other@example.com")
    vehicle = create_vehicle(owner)
    trip = client.post(
        "/viajes/",
        headers=owner,
        json=trip_payload(vehicle["id"]),
    ).json()
    request = client.post(
        f"/viajes/{trip['id']}/solicitudes",
        headers=passenger,
        json={},
    ).json()
    rejected = client.patch(
        f"/solicitudes/{request['id']}/rechazar",
        headers=owner,
    )
    assert rejected.status_code == 200
    current = client.get("/viajes/mis-viajes", headers=owner).json()[0]
    assert current["cupos_disponibles"] == current["cupos_totales"]
    assert client.patch(
        f"/viajes/{trip['id']}/iniciar",
        headers=other,
    ).status_code == 403
    assert client.patch(
        f"/viajes/{trip['id']}/iniciar",
        headers=owner,
    ).json()["estado"] == "en_curso"
    assert client.patch(
        f"/viajes/{trip['id']}/finalizar",
        headers=owner,
    ).json()["estado"] == "finalizado"
    assert client.post(
        f"/viajes/{trip['id']}/solicitudes",
        headers=passenger,
        json={},
    ).status_code == 400


def test_aceptacion_concurrente_no_sobrevende() -> None:
    suffix = uuid4().hex
    created_ids: dict[str, list[int]] = {
        "users": [],
        "vehicles": [],
        "trips": [],
        "requests": [],
    }
    try:
        with SessionLocal() as db:
            owner = Usuario(
                nombre="Owner",
                email=f"owner-{suffix}@example.com",
                hashed_password="not-used",
            )
            passengers = [
                Usuario(
                    nombre=f"Passenger {index}",
                    email=f"passenger-{index}-{suffix}@example.com",
                    hashed_password="not-used",
                )
                for index in range(2)
            ]
            db.add_all([owner, *passengers])
            db.flush()
            created_ids["users"] = [owner.id, *(p.id for p in passengers)]
            vehicle = Vehiculo(
                propietario_id=owner.id,
                marca="Toyota",
                modelo="Vitz",
                color="Blanco",
                matricula=f"C{suffix[:7]}",
                capacidad=1,
            )
            db.add(vehicle)
            db.flush()
            created_ids["vehicles"] = [vehicle.id]
            trip = Viaje(
                origen="Asunción",
                destino="Luque",
                fecha=datetime.now() + timedelta(days=1),
                creador_id=owner.id,
                vehiculo_id=vehicle.id,
                cupos_totales=1,
                cupos_disponibles=1,
                punto_salida="Centro",
                punto_llegada="Centro",
                estado="publicado",
                cancelado=False,
            )
            db.add(trip)
            db.flush()
            created_ids["trips"] = [trip.id]
            requests = [
                SolicitudViaje(
                    viaje_id=trip.id,
                    pasajero_id=passenger.id,
                    estado="pendiente",
                )
                for passenger in passengers
            ]
            db.add_all(requests)
            db.commit()
            created_ids["requests"] = [request.id for request in requests]
            owner_id = owner.id

        def accept(request_id: int) -> int:
            with SessionLocal() as session:
                try:
                    responder_solicitud(session, request_id, owner_id, True)
                    return 200
                except HTTPException as error:
                    return error.status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = sorted(
                pool.map(accept, created_ids["requests"])
            )
        assert results == [200, 409]
        with SessionLocal() as db:
            trip = db.get(Viaje, created_ids["trips"][0])
            assert trip
            assert trip.cupos_disponibles == 0
            assert trip.estado == "completo"
            accepted_count = len(
                list(
                    db.scalars(
                        select(SolicitudViaje).where(
                            SolicitudViaje.id.in_(created_ids["requests"]),
                            SolicitudViaje.estado == "aceptada",
                        )
                    )
                )
            )
            assert accepted_count == 1
    finally:
        with SessionLocal() as db:
            db.execute(
                delete(SolicitudViaje).where(
                    SolicitudViaje.id.in_(created_ids["requests"])
                )
            )
            db.execute(
                delete(Viaje).where(Viaje.id.in_(created_ids["trips"]))
            )
            db.execute(
                delete(Vehiculo).where(
                    Vehiculo.id.in_(created_ids["vehicles"])
                )
            )
            db.execute(
                delete(Usuario).where(
                    Usuario.id.in_(created_ids["users"])
                )
            )
            db.commit()
