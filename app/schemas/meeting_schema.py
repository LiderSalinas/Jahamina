from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.core.geo import validate_paraguay_coordinates


class MeetingPointProposal(BaseModel):
    texto: str = Field(min_length=2, max_length=200)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    @model_validator(mode="after")
    def dentro_de_paraguay(self):
        validate_paraguay_coordinates(self.latitude, self.longitude)
        return self


class MeetingPointResponse(BaseModel):
    reserva_id: int
    texto: str | None
    latitude: float | None
    longitude: float | None
    estado: Literal["sin_definir", "propuesto", "confirmado", "rechazado", "reemplazado"]
    propuesto_por_id: int | None
    propuesto_en: datetime | None
    confirmado_por_conductor_en: datetime | None
    confirmado_por_pasajero_en: datetime | None
    actualizado_en: datetime | None
