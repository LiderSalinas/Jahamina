from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MessageCreate(BaseModel):
    contenido: str = Field(min_length=1, max_length=1000)
    client_message_id: str | None = Field(default=None, max_length=100)

    @field_validator("contenido")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El mensaje no puede estar vacío")
        return value


class MessageResponse(BaseModel):
    id: int
    conversacion_id: int
    remitente_id: int | None
    contenido: str
    tipo: Literal["texto", "sistema"]
    creado_en: datetime
    editado_en: datetime | None
    leido_en: datetime | None
    eliminado: bool
    client_message_id: str | None

    model_config = ConfigDict(from_attributes=True)


class MessagePage(BaseModel):
    items: list[MessageResponse]
    next_cursor: int | None


class ConversationResponse(BaseModel):
    id: int
    solicitud_id: int
    creada_en: datetime
    actualizada_en: datetime
    ultimo_mensaje_en: datetime | None
    cerrada_en: datetime | None
    activa: bool
    puede_escribir: bool
    no_leidos: int
    participante: str
    participante_imagen_url: str | None = None
    viaje_id: int
    origen: str
    destino: str
    estado_viaje: str
    estado_reserva: str
    ultimo_mensaje: str | None


class ReadResponse(BaseModel):
    mensajes_marcados: int
    leido_en: datetime


class UnreadConversation(BaseModel):
    conversacion_id: int
    solicitud_id: int
    cantidad: int


class UnreadResponse(BaseModel):
    total: int
    conversaciones: list[UnreadConversation]


class WebSocketTicketResponse(BaseModel):
    ticket: str
    expires_in: int


class WebSocketClientEvent(BaseModel):
    type: Literal[
        "message.send", "message.read", "typing.start", "typing.stop", "ping"
    ]
    data: dict = Field(default_factory=dict)
