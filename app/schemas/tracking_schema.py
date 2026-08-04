from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy: float = Field(gt=0, le=5000)
    speed: float | None = Field(default=None, ge=0, le=150)
    heading: float | None = Field(default=None, ge=0, lt=360)
    client_timestamp: datetime | None = None
    sequence: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def timestamp_reasonable(self):
        if self.client_timestamp:
            from datetime import datetime, timedelta, timezone
            value = self.client_timestamp
            now = datetime.now(timezone.utc)
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            if abs(now - value) > timedelta(minutes=5):
                raise ValueError("Timestamp de ubicación fuera de rango")
        return self


class SharingUpdate(BaseModel):
    enabled: bool


class TrackingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    viaje_id: int
    conductor_id: int
    estado: Literal["inactivo", "activo", "pausado", "finalizado", "cancelado"]
    iniciado_en: datetime | None
    pausado_en: datetime | None
    finalizado_en: datetime | None
    compartir_ubicacion: bool
    ultima_actualizacion_en: datetime | None


class CurrentLocation(BaseModel):
    latitude: float
    longitude: float
    accuracy: float
    speed: float | None
    heading: float | None
    updated_at: datetime
    stale: bool


class LocationTicketResponse(BaseModel):
    ticket: str
    role: Literal["publisher", "subscriber"]
    expires_in: int
