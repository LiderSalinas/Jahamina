from __future__ import annotations

from typing import Any, Protocol
from unicodedata import normalize
from urllib.parse import quote

import httpx

from app.core.geo import PARAGUAY_COUNTRY_CODE, PARAGUAY_COUNTRY_NAME, PARAGUAY_VIEWBOX, is_within_paraguay
from app.core.settings import settings


CITY_TYPES = {"city", "town", "village", "municipality", "city_district", "place", "locality"}
DISTRICT_TYPES = {"district", "county", "administrative"}
NEIGHBOURHOOD_TYPES = {"suburb", "neighbourhood", "quarter"}
STREET_TYPES = {"road", "street", "residential", "address", "house"}
QUERY_ALIASES = {
    "asuncion": "Asunción",
    "encarnacion": "Encarnación",
    "caaguazu": "Caaguazú",
    "coronel oviedo": "Coronel Oviedo",
}


class GeocodingProvider(Protocol):
    name: str

    async def search(self, query: str, limit: int = 6) -> list[dict[str, Any]]: ...

    async def reverse(self, latitude: float, longitude: float) -> dict[str, Any]: ...


def comparable(value: str) -> str:
    decomposed = normalize("NFKD", value.casefold())
    return "".join(character for character in decomposed if not 0x300 <= ord(character) <= 0x36F)


def normalize_search_query(query: str) -> str:
    cleaned = " ".join(query.strip().split())
    return QUERY_ALIASES.get(comparable(cleaned), cleaned)


def _rank(place_type: str) -> int:
    normalized_type = place_type.casefold()
    if normalized_type in CITY_TYPES:
        return 0
    if normalized_type in DISTRICT_TYPES:
        return 1
    if normalized_type in NEIGHBOURHOOD_TYPES:
        return 2
    if normalized_type in STREET_TYPES:
        return 3
    return 4


def _unique_parts(*parts: Any) -> list[str]:
    result: list[str] = []
    for part in parts:
        if isinstance(part, str) and part.strip() and not any(comparable(part) == comparable(value) for value in result):
            result.append(part.strip())
    return result


def format_place_suggestion(*, primary: str, state: str | None, latitude: float, longitude: float, place_type: str) -> dict[str, Any]:
    secondary = ", ".join(part for part in _unique_parts(state, PARAGUAY_COUNTRY_NAME) if comparable(part) != comparable(primary))
    return {
        "label": ", ".join(_unique_parts(primary, secondary)),
        "primary": primary,
        "secondary": secondary or PARAGUAY_COUNTRY_NAME,
        "place_type": place_type,
        "latitude": latitude,
        "longitude": longitude,
    }


def rank_suggestions(items: list[dict[str, Any]], query: str, limit: int) -> list[dict[str, Any]]:
    wanted = comparable(query)

    def score(item: dict[str, Any]) -> tuple[int, int, int, str]:
        primary = comparable(str(item.get("primary", "")))
        return (_rank(str(item.get("place_type", ""))), 0 if primary == wanted else 1, 0 if primary.startswith(wanted) else 1, primary)

    unique: dict[tuple[str, str], dict[str, Any]] = {}
    for item in items:
        key = (comparable(str(item.get("primary", ""))), comparable(str(item.get("secondary", ""))))
        unique.setdefault(key, item)
    return sorted(unique.values(), key=score)[:limit]


class NominatimProvider:
    name = "nominatim"

    async def search(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=settings.map_request_timeout_seconds) as client:
            response = await client.get(
                f"{settings.geocoding_provider_url.rstrip('/')}/search",
                params={
                    "q": normalize_search_query(query), "countrycodes": PARAGUAY_COUNTRY_CODE,
                    "bounded": 1, "viewbox": PARAGUAY_VIEWBOX, "addressdetails": 1,
                    "namedetails": 1, "dedupe": 1, "accept-language": "es",
                    "format": "jsonv2", "limit": max(limit * 2, 10),
                },
                headers={"User-Agent": "Jahamina/1.0"},
            )
            response.raise_for_status()
            suggestions: list[dict[str, Any]] = []
            for item in response.json():
                address = item.get("address") or {}
                latitude, longitude = float(item["lat"]), float(item["lon"])
                if address.get("country_code", "").casefold() != PARAGUAY_COUNTRY_CODE or not is_within_paraguay(latitude, longitude):
                    continue
                place_type = str(item.get("addresstype") or item.get("type") or "place")
                primary = next((value for value in (
                    item.get("name"), address.get("city"), address.get("town"), address.get("village"),
                    address.get("municipality"), address.get("suburb"), address.get("road"),
                ) if isinstance(value, str) and value.strip()), normalize_search_query(query))
                suggestions.append(format_place_suggestion(primary=primary, state=address.get("state") or address.get("region"), latitude=latitude, longitude=longitude, place_type=place_type))
            return rank_suggestions(suggestions, query, limit)

    async def reverse(self, latitude: float, longitude: float) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=settings.map_request_timeout_seconds) as client:
            response = await client.get(
                f"{settings.geocoding_provider_url.rstrip('/')}/reverse",
                params={"lat": latitude, "lon": longitude, "addressdetails": 1, "accept-language": "es", "format": "jsonv2"},
                headers={"User-Agent": "Jahamina/1.0"},
            )
            response.raise_for_status()
            item = response.json()
            address = item.get("address") or {}
            if address.get("country_code", "").casefold() != PARAGUAY_COUNTRY_CODE:
                raise ValueError("La ubicación debe estar dentro de Paraguay.")
            primary = next((value for value in (
                item.get("name"), address.get("road"), address.get("suburb"), address.get("city"),
                address.get("town"), address.get("village"), address.get("municipality"),
            ) if isinstance(value, str) and value.strip()), PARAGUAY_COUNTRY_NAME)
            return format_place_suggestion(primary=primary, state=address.get("state") or address.get("region"), latitude=latitude, longitude=longitude, place_type=str(item.get("addresstype") or item.get("type") or "place"))


class MapTilerProvider:
    name = "maptiler"

    def _key(self) -> str:
        key = settings.maptiler_api_key or settings.geocoding_api_key
        if not key:
            raise ValueError("MAPTILER_API_KEY no está configurada")
        return key

    async def _request(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=settings.map_request_timeout_seconds) as client:
            response = await client.get(f"{settings.maptiler_geocoding_url.rstrip('/')}/{path}.json", params={**params, "key": self._key()}, headers={"User-Agent": "Jahamina/1.0"})
            response.raise_for_status()
            return response.json()

    def _suggestion(self, feature: dict[str, Any]) -> dict[str, Any] | None:
        coordinates = feature.get("center") or feature.get("geometry", {}).get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) < 2:
            return None
        longitude, latitude = float(coordinates[0]), float(coordinates[1])
        if not is_within_paraguay(latitude, longitude):
            return None
        context = feature.get("context") or []
        country = next((item for item in context if str(item.get("id", "")).startswith("country")), {})
        country_code = str(country.get("short_code") or feature.get("properties", {}).get("country_code") or "").casefold()
        if country_code and country_code.split("-")[-1] != PARAGUAY_COUNTRY_CODE:
            return None
        state = next((item.get("text") for item in context if str(item.get("id", "")).startswith(("region", "district"))), None)
        place_type = str((feature.get("place_type") or ["place"])[0])
        primary = str(feature.get("text") or feature.get("place_name", "").split(",")[0]).strip()
        return format_place_suggestion(primary=primary, state=state, latitude=latitude, longitude=longitude, place_type=place_type) if primary else None

    async def search(self, query: str, limit: int = 6) -> list[dict[str, Any]]:
        data = await self._request(quote(normalize_search_query(query), safe=""), {"country": PARAGUAY_COUNTRY_CODE, "autocomplete": "true", "fuzzyMatch": "true", "language": "es", "limit": limit})
        suggestions = [suggestion for feature in data.get("features", []) if (suggestion := self._suggestion(feature))]
        return rank_suggestions(suggestions, query, limit)

    async def reverse(self, latitude: float, longitude: float) -> dict[str, Any]:
        data = await self._request(f"{longitude},{latitude}", {"country": PARAGUAY_COUNTRY_CODE, "language": "es", "limit": 1})
        for feature in data.get("features", []):
            if suggestion := self._suggestion(feature):
                return suggestion
        raise ValueError("La ubicación debe estar dentro de Paraguay.")


def configured_providers() -> list[GeocodingProvider]:
    if settings.geocoding_provider.casefold() == "maptiler":
        return [MapTilerProvider(), NominatimProvider()]
    return [NominatimProvider()]
