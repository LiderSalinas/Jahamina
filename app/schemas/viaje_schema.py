from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EstadoViaje(StrEnum):
    PUBLICADO = "publicado"
    COMPLETO = "completo"
    EN_CURSO = "en_curso"
    FINALIZADO = "finalizado"
    CANCELADO = "cancelado"

class ViajeCreate(BaseModel):
    origen: str = Field(min_length=2, max_length=150)
    destino: str = Field(min_length=2, max_length=150)
    fecha: datetime
    vehiculo_id: int = Field(gt=0)
    cupos_totales: int = Field(ge=1, le=8)
    descripcion: str | None = Field(default=None, max_length=1000)
    punto_salida: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    punto_llegada: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    origen_latitud: float | None = Field(default=None, ge=-90, le=90)
    origen_longitud: float | None = Field(default=None, ge=-180, le=180)
    destino_latitud: float | None = Field(default=None, ge=-90, le=90)
    destino_longitud: float | None = Field(default=None, ge=-180, le=180)
    punto_salida_latitud: float | None = Field(default=None, ge=-90, le=90)
    punto_salida_longitud: float | None = Field(default=None, ge=-180, le=180)
    punto_llegada_latitud: float | None = Field(default=None, ge=-90, le=90)
    punto_llegada_longitud: float | None = Field(default=None, ge=-180, le=180)
    distancia_estimada_km: float | None = Field(default=None, ge=0)
    duracion_estimada_minutos: int | None = Field(default=None, ge=0)
    ruta_codificada: str | None = Field(default=None, max_length=20000)

    @field_validator("origen", "destino")
    @classmethod
    def limpiar_ubicacion(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("La ubicación debe tener al menos 2 caracteres")
        return value

    @model_validator(mode="after")
    def validar_recorrido(self):
        if self.origen.casefold() == self.destino.casefold():
            raise ValueError("El origen y el destino deben ser diferentes")
        ahora = datetime.now(self.fecha.tzinfo)
        if self.fecha <= ahora:
            raise ValueError("La fecha del viaje debe ser futura")
        self.punto_salida = (self.punto_salida or self.origen).strip()
        self.punto_llegada = (self.punto_llegada or self.destino).strip()
        return self

class ViajeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origen: str
    destino: str
    fecha: datetime
    cancelado: bool
    creador_id: int
    vehiculo_id: int | None
    cupos_totales: int
    cupos_disponibles: int
    descripcion: str | None
    punto_salida: str
    punto_llegada: str
    origen_latitud: float | None
    origen_longitud: float | None
    destino_latitud: float | None
    destino_longitud: float | None
    punto_salida_latitud: float | None
    punto_salida_longitud: float | None
    punto_llegada_latitud: float | None
    punto_llegada_longitud: float | None
    distancia_estimada_km: float | None
    duracion_estimada_minutos: int | None
    ruta_codificada: str | None
    estado: EstadoViaje
    updated_at: datetime

class ViajeUnidoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    viaje_id: int
    usuario_id: int

