from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class RoadmapReserva(BaseModel):
    id: int
    estado: str
    rol_actual: Literal["conductor", "pasajero"]
    mensaje_inicial: str | None


class RoadmapViaje(BaseModel):
    id: int
    origen: str
    destino: str
    fecha_salida: datetime
    estado: str
    cupos_totales: int
    cupos_ocupados: int
    ruta_codificada: str | None = None


class RoadmapPersona(BaseModel):
    id: int
    nombre: str


class RoadmapVehiculo(BaseModel):
    id: int
    marca: str
    modelo: str
    color: str
    matricula: str


class RoadmapMeetingPoint(BaseModel):
    estado: str
    nombre_publico: str | None
    zona_general: str | None
    latitud: float | None
    longitud: float | None


class RoadmapStop(BaseModel):
    id: int | None = None
    reserva_id: int | None = None
    orden: int
    tipo: str
    nombre_publico: str
    zona_general: str | None
    latitud: float | None
    longitud: float | None
    hora_estimada: datetime | None
    hora_real: datetime | None
    estado: str

    model_config = ConfigDict(from_attributes=True)


class RoadmapEvent(BaseModel):
    id: int
    reserva_id: int | None
    tipo: str
    descripcion_publica: str
    metadata: dict[str, Any]
    created_at: datetime


class DerivedRoadmapStep(BaseModel):
    id: str
    titulo: str
    descripcion: str
    estado: Literal["completado", "actual", "pendiente", "cancelado"]
    timestamp: datetime | None
    orden: int


class RoadmapOccupancy(BaseModel):
    ocupados: int
    totales: int
    pendientes: int


class PassengerStatus(BaseModel):
    estado: str
    nombre: str


class NextAction(BaseModel):
    label: str
    action: str
    enabled: bool = True
    reason_disabled: str | None = None
    confirmation_required: bool = False


class RoadmapPermissions(BaseModel):
    puede_operar_viaje: bool
    puede_actualizar_estado_propio: bool
    puede_ver_puntos_exactos: bool = True
    puede_ver_chat: bool = True
    puede_ver_punto_exacto: bool = True
    puede_modificar_viaje: bool = False


class RoadmapResponse(BaseModel):
    reserva: RoadmapReserva
    viaje: RoadmapViaje
    conductor: RoadmapPersona
    pasajero_actual: RoadmapPersona
    vehiculo: RoadmapVehiculo | None
    punto_encuentro: RoadmapMeetingPoint
    paradas: list[RoadmapStop]
    hoja_ruta: list[DerivedRoadmapStep]
    ocupacion: RoadmapOccupancy
    eventos: list[RoadmapEvent]
    estado_pasajero: PassengerStatus
    proxima_accion: NextAction
    permisos: RoadmapPermissions


class RoadmapTicketResponse(BaseModel):
    ticket: str
    expires_in: int
