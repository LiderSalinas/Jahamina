from pydantic import BaseModel, Field, model_validator

from app.core.geo import validate_paraguay_coordinates


class Coordinates(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    @model_validator(mode="after")
    def dentro_de_paraguay(self):
        validate_paraguay_coordinates(self.latitude, self.longitude)
        return self


class GeocodingResult(Coordinates):
    label: str


class RouteRequest(BaseModel):
    origin: Coordinates
    destination: Coordinates


class RouteResponse(BaseModel):
    distance_km: float = Field(ge=0)
    duration_minutes: int = Field(ge=0)
    geometry: str | None = None
