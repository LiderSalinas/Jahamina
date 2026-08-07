import json
from urllib.parse import quote

import httpx
from fastapi import HTTPException
from redis.exceptions import RedisError

from app.core.geo import validate_paraguay_coordinates
from app.core.redis import get_redis_client
from app.core.settings import settings
from app.schemas.map_schema import Coordinates, GeocodingResult, RouteResponse
from app.services.geocoding_provider import configured_providers, normalize_search_query


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
    normalized = normalize_search_query(query)
    if len(normalized) < 3:
        raise HTTPException(status_code=422, detail="Consulta demasiado corta")

    async def fetch():
        last_error: Exception | None = None
        for provider in configured_providers():
            try:
                return await provider.search(normalized, limit=6)
            except (httpx.TimeoutException, httpx.HTTPError, KeyError, ValueError) as error:
                last_error = error
        raise HTTPException(status_code=502, detail="Proveedor de geocodificación no disponible") from last_error

    cache_key = f"maps:geocode:{settings.geocoding_provider.casefold()}:{normalized.casefold()}"
    return [GeocodingResult.model_validate(item) for item in await _cached_json(cache_key, fetch)]


async def reverse_geocode(latitude: float, longitude: float) -> GeocodingResult:
    try:
        validate_paraguay_coordinates(latitude, longitude)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    async def fetch():
        last_error: Exception | None = None
        for provider in configured_providers():
            try:
                return await provider.reverse(latitude, longitude)
            except ValueError as error:
                if "Paraguay" in str(error):
                    raise HTTPException(status_code=422, detail=str(error)) from error
                last_error = error
            except (httpx.TimeoutException, httpx.HTTPError, KeyError) as error:
                last_error = error
        raise HTTPException(status_code=502, detail="Proveedor de geocodificación no disponible") from last_error

    cache_key = f"maps:reverse:{settings.geocoding_provider.casefold()}:{latitude:.5f}:{longitude:.5f}"
    return GeocodingResult.model_validate(await _cached_json(cache_key, fetch))


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
                return {
                    "distance_km": round(selected["distance"] / 1000, 2),
                    "duration_minutes": round(selected["duration"] / 60),
                    "geometry": selected.get("geometry"),
                }
        except HTTPException:
            raise
        except (httpx.TimeoutException, httpx.HTTPError, KeyError, ValueError) as error:
            raise HTTPException(status_code=502, detail="Proveedor de rutas no disponible") from error

    return RouteResponse.model_validate(await _cached_json(key, fetch))
