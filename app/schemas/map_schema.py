from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class GeocodingResult(Coordinates):
    label: str


class RouteRequest(BaseModel):
    origin: Coordinates
    destination: Coordinates


class RouteResponse(BaseModel):
    distance_km: float = Field(ge=0)
    duration_minutes: int = Field(ge=0)
    geometry: str | None = None
