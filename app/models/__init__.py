"""Registro central de todos los modelos SQLAlchemy."""

from app.models.conversacion import Conversacion
from app.models.mensaje import Mensaje
from app.models.seguimiento_viaje import SeguimientoViaje
from app.models.pasajero_viaje import ViajeUnido
from app.models.solicitud_viaje import SolicitudViaje
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.models.viaje_model import Viaje

__all__ = [
    "Conversacion",
    "Mensaje",
    "SeguimientoViaje",
    "SolicitudViaje",
    "Usuario",
    "Vehiculo",
    "Viaje",
    "ViajeUnido",
]
