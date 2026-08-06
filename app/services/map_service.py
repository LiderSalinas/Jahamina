import json
from urllib.parse import quote

import httpx
from fastapi import HTTPException
from redis.exceptions import RedisError

from app.core.redis import get_redis_client
from app.core.settings import settings
from app.core.geo import PARAGUAY_COUNTRY_CODE, PARAGUAY_COUNTRY_NAME, PARAGUAY_VIEWBOX, is_within_paraguay
from app.schemas.map_schema import Coordinates, GeocodingResult, RouteResponse


async def _cached_json(key: str, fetcher):
    redis = get_redis_client()
    try:
        cached = await redis.get(key)
        if cached:
            return json.loads(cached)
        result = await fetcher()
        await redis.set(key, json.dumps(result), ex=settings.map_cache_ttl_seconds)
        return result
    except RedisError:
        return await fetcher()
    finally:
        await redis.aclose()


async def geocode(query: str) -> list[GeocodingResult]:
    normalized = " ".join(query.strip().split())
    if len(normalized) < 3:
        raise HTTPException(status_code=422, detail="Consulta demasiado corta")

    async def fetch():
        try:
            async with httpx.AsyncClient(timeout=settings.map_request_timeout_seconds) as client:
                response = await client.get(
                    f"{settings.geocoding_provider_url.rstrip('/')}/search",
                    params={
                        "q": normalized, "countrycodes": PARAGUAY_COUNTRY_CODE,
                        "bounded": 1, "viewbox": PARAGUAY_VIEWBOX,
                        "addressdetails": 1, "format": "jsonv2", "limit": 5,
                    },
                    headers={"User-Agent": "Jahamina/1.0"},
                )
                response.raise_for_status()
                results = []
                for item in response.json()[:5]:
                    address = item.get("address") or {}
                    latitude, longitude = float(item["lat"]), float(item["lon"])
                    if address.get("country_code", "").casefold() != PARAGUAY_COUNTRY_CODE or not is_within_paraguay(latitude, longitude):
                        continue
                    parts = [item.get("name") or address.get("amenity") or address.get("road"), address.get("suburb") or address.get("neighbourhood"), address.get("city") or address.get("town") or address.get("village") or address.get("municipality"), address.get("state"), PARAGUAY_COUNTRY_NAME]
                    label = ", ".join(dict.fromkeys(part.strip() for part in parts if isinstance(part, str) and part.strip()))
                    results.append({"label": label or f"{normalized}, {PARAGUAY_COUNTRY_NAME}", "latitude": latitude, "longitude": longitude})
                return results
        except (httpx.TimeoutException, httpx.HTTPError, KeyError, ValueError) as error:
            raise HTTPException(status_code=502, detail="Proveedor de geocodificación no disponible") from error

    data = await _cached_json(f"maps:geocode:{normalized.casefold()}", fetch)
    return [GeocodingResult.model_validate(item) for item in data]


async def reverse_geocode(latitude: float, longitude: float) -> GeocodingResult:
    from app.core.geo import validate_paraguay_coordinates

    try:
        validate_paraguay_coordinates(latitude, longitude)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    async def fetch():
        try:
            async with httpx.AsyncClient(timeout=settings.map_request_timeout_seconds) as client:
                response = await client.get(
                    f"{settings.geocoding_provider_url.rstrip('/')}/reverse",
                    params={"lat": latitude, "lon": longitude, "addressdetails": 1, "format": "jsonv2"},
                    headers={"User-Agent": "Jahamina/1.0"},
                )
                response.raise_for_status()
                item = response.json()
                address = item.get("address") or {}
                if address.get("country_code", "").casefold() != PARAGUAY_COUNTRY_CODE:
                    raise HTTPException(status_code=422, detail="La ubicación debe estar dentro de Paraguay.")
                parts = [item.get("name") or address.get("road"), address.get("suburb") or address.get("neighbourhood"), address.get("city") or address.get("town") or address.get("village") or address.get("municipality"), address.get("state"), PARAGUAY_COUNTRY_NAME]
                return {"label": ", ".join(dict.fromkeys(part.strip() for part in parts if isinstance(part, str) and part.strip())), "latitude": latitude, "longitude": longitude}
        except HTTPException:
            raise
        except (httpx.TimeoutException, httpx.HTTPError, KeyError, ValueError) as error:
            raise HTTPException(status_code=502, detail="Proveedor de geocodificación no disponible") from error

    data = await _cached_json(f"maps:reverse:{latitude:.5f}:{longitude:.5f}", fetch)
    return GeocodingResult.model_validate(data)


async def route(origin: Coordinates, destination: Coordinates) -> RouteResponse:
    key = f"maps:route:{origin.latitude:.5f},{origin.longitude:.5f}:{destination.latitude:.5f},{destination.longitude:.5f}"

    async def fetch():
        coordinates = f"{origin.longitude},{origin.latitude};{destination.longitude},{destination.latitude}"
        try:
            async with httpx.AsyncClient(timeout=settings.map_request_timeout_seconds) as client:
                response = await client.get(
                    f"{settings.routing_provider_url.rstrip('/')}/route/v1/driving/{quote(coordinates, safe=';,.-')}",
                    params={"overview": "simplified", "geometries": "polyline"},
                )
                response.raise_for_status()
                routes = response.json().get("routes", [])
                if not routes:
                    raise HTTPException(status_code=404, detail="No se encontró una ruta")
                selected = routes[0]
                return {"distance_km": round(selected["distance"] / 1000, 2), "duration_minutes": round(selected["duration"] / 60), "geometry": selected.get("geometry")}
        except HTTPException:
            raise
        except (httpx.TimeoutException, httpx.HTTPError, KeyError, ValueError) as error:
            raise HTTPException(status_code=502, detail="Proveedor de rutas no disponible") from error

    return RouteResponse.model_validate(await _cached_json(key, fetch))
