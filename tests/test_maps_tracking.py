import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient
import httpx
import pytest
from app.schemas.map_schema import RouteResponse
from app.services import map_service
from app.services.geocoding_provider import MapTilerProvider, NominatimProvider, configured_providers, normalize_search_query, rank_suggestions


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


@pytest.mark.parametrize("latitude,longitude", [(-34.60, -58.38), (-23.55, -46.63), (-17.39, -66.16)])
def test_trip_rejects_coordinates_outside_paraguay(client, auth_headers, create_vehicle, latitude, longitude):
    driver = auth_headers()
    vehicle = create_vehicle(driver)
    payload = {"origen":"Asunción","destino":"Luque","fecha":(datetime.now()+timedelta(days=1)).isoformat(),"vehiculo_id":vehicle["id"],"cupos_totales":2,"origen_latitud":latitude,"origen_longitud":longitude,"destino_latitud":-25.26,"destino_longitud":-57.57}
    response = client.post("/viajes/", headers=driver, json=payload)
    assert response.status_code == 422
    assert "Paraguay" in response.text


def test_meeting_point_outside_paraguay_is_rejected(client, auth_headers, create_vehicle):
    flow = mobility_flow(client, auth_headers, create_vehicle)
    response = client.post(f"/reservas/{flow['request']['id']}/punto-encuentro/proponer", headers=flow["passenger"], json={"texto":"Exterior","latitude":-34.60,"longitude":-58.38})
    assert response.status_code == 422
    assert "Paraguay" in response.text


def test_geocoder_is_bounded_to_paraguay_and_filters_foreign_results(monkeypatch):
    calls = []
    payload = [
        {"name":"Asunción","lat":"-25.2867","lon":"-57.3333","address":{"city":"Asunción","state":"Distrito Capital","country":"Paraguay","country_code":"py"}},
        {"name":"Buenos Aires","lat":"-34.6037","lon":"-58.3816","address":{"city":"Buenos Aires","country":"Argentina","country_code":"ar"}},
    ]

    class Response:
        def raise_for_status(self): return None
        def json(self): return payload

    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def get(self, url, **kwargs):
            calls.append(kwargs["params"])
            if kwargs["params"]["q"].startswith("Buenos Aires"):
                return type("ForeignResponse", (), {"raise_for_status": lambda self: None, "json": lambda self: payload[1:]})()
            return Response()

    monkeypatch.setattr(httpx, "AsyncClient", Client)
    query = f"Asunción-{uuid4().hex}"
    results = asyncio.run(map_service.geocode(query))
    cached = asyncio.run(map_service.geocode(query))
    assert len(results) == 1
    assert results[0].label.endswith("Paraguay")
    assert calls[0]["countrycodes"] == "py"
    assert calls[0]["bounded"] == 1
    assert calls[0]["viewbox"] == "-62.65,-19.29,-54.26,-27.61"
    assert calls[0]["addressdetails"] == 1
    assert calls[0]["namedetails"] == 1
    assert calls[0]["accept-language"] == "es"
    assert cached == results
    assert len(calls) == 1
    assert asyncio.run(map_service.geocode(f"Buenos Aires-{uuid4().hex}")) == []
    assert len(asyncio.run(map_service.geocode(f"San Juan-{uuid4().hex}"))) == 1


@pytest.mark.parametrize("query", [
    "San Juan Bautista", "San Ignacio", "Ayolas", "Santa Rosa", "San Miguel", "Santiago",
    "Encarnación", "Asunción", "Villarrica", "Caaguazú", "Coronel Oviedo", "Ciudad del Este",
])
def test_paraguayan_city_search_does_not_require_department_or_country(monkeypatch, query):
    calls = []

    class Response:
        def raise_for_status(self): return None
        def json(self):
            return [{
                "name": normalize_search_query(query), "type": "city", "addresstype": "city",
                "lat": "-25.3", "lon": "-57.5",
                "address": {"city": normalize_search_query(query), "state": "Paraguay", "country_code": "py"},
            }]

    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def get(self, url, **kwargs):
            calls.append(kwargs["params"])
            return Response()

    monkeypatch.setattr(httpx, "AsyncClient", Client)
    results = asyncio.run(NominatimProvider().search(query))

    assert results[0]["primary"] == normalize_search_query(query)
    assert results[0]["secondary"].endswith("Paraguay")
    assert calls[0]["q"] == normalize_search_query(query)
    assert "departamento" not in calls[0]["q"].casefold()
    assert calls[0]["countrycodes"] == "py"
    assert len(results) <= 6


def test_city_results_rank_before_pois_and_aliases_are_accent_insensitive():
    items = [
        {"primary": "San Juan Hotel", "secondary": "Misiones, Paraguay", "place_type": "hotel"},
        {"primary": "San Juan Bautista", "secondary": "Misiones, Paraguay", "place_type": "city"},
        {"primary": "San Juan", "secondary": "Misiones, Paraguay", "place_type": "road"},
    ]

    assert rank_suggestions(items, "san juan", 6)[0]["primary"] == "San Juan Bautista"
    assert normalize_search_query("encarnacion") == "Encarnación"
    assert normalize_search_query("  Ayolas  ") == "Ayolas"


def test_maptiler_is_optional_and_keeps_nominatim_as_fallback(monkeypatch):
    monkeypatch.setattr(map_service.settings, "geocoding_provider", "maptiler")

    providers = configured_providers()

    assert isinstance(providers[0], MapTilerProvider)
    assert isinstance(providers[1], NominatimProvider)


def test_geocoder_timeout_returns_controlled_error(monkeypatch):
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *args): return None
        async def get(self, *args, **kwargs): raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(httpx, "AsyncClient", Client)
    with pytest.raises(Exception) as caught:
        asyncio.run(map_service.geocode(f"San Juan-{uuid4().hex}"))
    assert getattr(caught.value, "status_code", None) == 502


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
