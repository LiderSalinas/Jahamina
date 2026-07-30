from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VehiculoCreate(BaseModel):
    marca: str = Field(min_length=2, max_length=80)
    modelo: str = Field(min_length=1, max_length=80)
    color: str = Field(min_length=2, max_length=50)
    matricula: str = Field(min_length=3, max_length=20)
    capacidad: int = Field(ge=1, le=8)

    @field_validator("marca", "modelo", "color")
    @classmethod
    def limpiar_texto(cls, value: str) -> str:
        return value.strip()

    @field_validator("matricula")
    @classmethod
    def normalizar_matricula(cls, value: str) -> str:
        normalized = value.strip().upper().replace(" ", "").replace("-", "")
        if not normalized.isalnum():
            raise ValueError("La matrícula solo puede contener letras y números")
        return normalized


class VehiculoUpdate(BaseModel):
    marca: str | None = Field(default=None, min_length=2, max_length=80)
    modelo: str | None = Field(default=None, min_length=1, max_length=80)
    color: str | None = Field(default=None, min_length=2, max_length=50)
    matricula: str | None = Field(default=None, min_length=3, max_length=20)
    capacidad: int | None = Field(default=None, ge=1, le=8)

    @field_validator("marca", "modelo", "color")
    @classmethod
    def limpiar_texto(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value

    @field_validator("matricula")
    @classmethod
    def normalizar_matricula(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().upper().replace(" ", "").replace("-", "")
        if not normalized.isalnum():
            raise ValueError("La matrícula solo puede contener letras y números")
        return normalized


class VehiculoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    propietario_id: int
    marca: str
    modelo: str
    color: str
    matricula: str
    capacidad: int
    activo: bool
    created_at: datetime
    updated_at: datetime
