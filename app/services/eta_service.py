import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException

from app.core.redis import get_redis_client
from app.core.settings import settings
from app.schemas.map_schema import Coordinates
from app.schemas.tracking_schema import LocationEtaResponse
from app.services import map_service, roadmap_service, tracking_service


def _distance_text(meters: int) -> str:
    return f"{meters} m" if meters < 1000 else f"{meters / 1000:.1f} km".replace(".", ",")


async def next_stop_eta(db, reservation_id: int, user_id: int) -> LocationEtaResponse:
    roadmap = roadmap_service.get_roadmap(db, reservation_id, user_id)
    stop = next((item for item in sorted(roadmap.paradas, key=lambda value: value.orden)
                 if item.estado in {"actual", "pendiente"} and item.latitud is not None and item.longitud is not None), None)
    if not stop:
        return LocationEtaResponse(estado="no_disponible")
    try:
        location = await tracking_service.get_location(db, roadmap.viaje.id, user_id)
    except HTTPException as error:
        if error.status_code == 404:
            return LocationEtaResponse(parada_id=stop.id, parada_nombre=stop.nombre_publico, estado="no_disponible")
        raise
    if location.stale:
        return LocationEtaResponse(ubicacion=location, parada_id=stop.id, parada_nombre=stop.nombre_publico, estado="desactualizado")

    key = f"location:eta:{roadmap.viaje.id}:{stop.id or stop.orden}:{location.latitude:.3f}:{location.longitude:.3f}"
    redis = get_redis_client()
    try:
        cached = await redis.get(key)
        if cached:
            result = json.loads(cached)
        else:
            route = await map_service.route(
                Coordinates(latitude=location.latitude, longitude=location.longitude),
                Coordinates(latitude=stop.latitud, longitude=stop.longitud),
            )
            calculated = datetime.now(timezone.utc)
            result = {"distancia_metros": round(route.distance_km * 1000), "duracion_segundos": route.duration_minutes * 60, "calculado_en": calculated.isoformat()}
            await redis.set(key, json.dumps(result), ex=settings.location_eta_cache_seconds)
    except HTTPException:
        return LocationEtaResponse(ubicacion=location, parada_id=stop.id, parada_nombre=stop.nombre_publico, estado="error")
    finally:
        await redis.aclose()

    calculated_at = datetime.fromisoformat(result["calculado_en"])
    distance, duration = int(result["distancia_metros"]), int(result["duracion_segundos"])
    return LocationEtaResponse(
        ubicacion=location, parada_id=stop.id, parada_nombre=stop.nombre_publico,
        distancia_metros=distance, distancia_texto=_distance_text(distance), duracion_segundos=duration,
        eta_aproximada=calculated_at + timedelta(seconds=duration), proveedor="OSRM",
        calculado_en=calculated_at, estado="disponible",
    )
