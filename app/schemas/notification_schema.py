from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

NotificationType = Literal[
    "mensaje_nuevo", "solicitud_nueva", "solicitud_aceptada",
    "solicitud_rechazada", "punto_confirmado", "conductor_en_camino",
    "viaje_iniciado", "viaje_cancelado", "viaje_finalizado",
]


class NotificationResponse(BaseModel):
    id: int
    tipo: NotificationType
    titulo: str
    cuerpo: str
    reserva_id: int | None
    viaje_id: int | None
    conversacion_id: int | None
    url_destino: str
    leida: bool
    creada_en: datetime
    leida_en: datetime | None
    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total_no_leidas: int


class PushKeys(BaseModel):
    p256dh: str = Field(min_length=20, max_length=255)
    auth: str = Field(min_length=8, max_length=255)


class PushSubscriptionCreate(BaseModel):
    endpoint: str = Field(min_length=20, max_length=2048)
    keys: PushKeys
    dispositivo_nombre: str | None = Field(default=None, max_length=80)
    mensajes: bool = True
    reservas: bool = True
    viaje: bool = True

    @field_validator("endpoint")
    @classmethod
    def validate_endpoint(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("La suscripción Push debe usar HTTPS")
        return value


class PushSubscriptionResponse(BaseModel):
    id: int
    dispositivo_nombre: str | None
    activa: bool
    mensajes: bool
    reservas: bool
    viaje: bool
    creada_en: datetime
    ultima_utilizacion_en: datetime | None
    model_config = ConfigDict(from_attributes=True)


class PushPreferences(BaseModel):
    mensajes: bool
    reservas: bool
    viaje: bool


class PushConfigResponse(BaseModel):
    enabled: bool
    public_key: str | None


class NotificationTicketResponse(BaseModel):
    ticket: str
    expires_in: int
