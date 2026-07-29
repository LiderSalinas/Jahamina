from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from datetime import datetime

class ViajeCreate(BaseModel):
    origen: str = Field(min_length=2, max_length=150)
    destino: str = Field(min_length=2, max_length=150)
    fecha: datetime

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
        return self

class ViajeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origen: str
    destino: str
    fecha: datetime
    cancelado: bool
    creador_id: int

class ViajeUnidoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    viaje_id: int
    usuario_id: int

