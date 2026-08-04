from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EstadoSolicitud(StrEnum):
    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    CANCELADA = "cancelada"
    FINALIZADA = "finalizada"


class SolicitudCreate(BaseModel):
    mensaje_inicial: str | None = Field(default=None, max_length=1000)
    punto_encuentro_propuesto: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    punto_encuentro_latitud: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )
    punto_encuentro_longitud: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )


class SolicitudResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    viaje_id: int
    pasajero_id: int
    estado: EstadoSolicitud
    estado_pasajero: str
    mensaje_inicial: str | None
    punto_encuentro_propuesto: str | None
    punto_encuentro_latitud: float | None
    punto_encuentro_longitud: float | None
    created_at: datetime
    updated_at: datetime
    responded_at: datetime | None


class ReservaRelacionadaResponse(BaseModel):
    reserva_id: int
    viaje_id: int
    origen: str
    destino: str
    fecha: datetime
    estado: EstadoSolicitud
    rol: Literal["conductor", "pasajero"]
    participante_id: int
    participante: str
    conversacion_id: int | None
    ultimo_mensaje: str | None
    no_leidos: int
    ultima_actividad: datetime
