from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.evento_viaje import EventoViaje
from app.models.parada_viaje import ParadaViaje
from app.models.solicitud_viaje import SolicitudViaje
from app.models.viaje_model import Viaje
from app.schemas.roadmap_schema import (
    NextAction, PassengerStatus, RoadmapEvent, RoadmapMeetingPoint,
    RoadmapPermissions, RoadmapPersona, RoadmapReserva, RoadmapResponse,
    RoadmapStop, RoadmapVehiculo, RoadmapViaje,
)
from app.services.chat_service import add_system_message


TRIP_TRANSITIONS = {
    "preparar-salida": ({"publicado", "completo", "programado"}, "preparando_salida", "conductor_preparando_salida", "El conductor está preparando la salida."),
    "salir": ({"preparando_salida"}, "conductor_en_camino", "conductor_en_camino", "El conductor salió hacia el próximo punto."),
    "llegar": ({"conductor_en_camino"}, "conductor_en_punto", "conductor_llego", "El conductor llegó al punto de encuentro."),
    "iniciar": ({"conductor_en_punto", "abordaje"}, "en_curso", "viaje_iniciado", "El viaje comenzó."),
    "pausar": ({"en_curso"}, "pausado", "viaje_pausado", "El viaje fue pausado."),
    "reanudar": ({"pausado"}, "en_curso", "viaje_reanudado", "El viaje se reanudó."),
    "finalizar": ({"en_curso"}, "finalizado", "viaje_finalizado", "El viaje finalizó."),
}

PASSENGER_ACTIONS = {
    "listo": ({"confirmado"}, "listo", "pasajero_listo", "El pasajero confirmó que está listo."),
    "llegue": ({"listo"}, "esperando", "pasajero_en_punto", "El pasajero llegó al punto de encuentro."),
    "recoger": ({"listo", "esperando"}, "recogido", "pasajero_recogido", "El conductor confirmó la recogida del pasajero."),
    "abordar": ({"recogido"}, "abordo", "pasajero_abordo", "El pasajero abordó el vehículo."),
}


def _reservation(db: Session, reservation_id: int, user_id: int, lock: bool = False) -> SolicitudViaje:
    if lock:
        locked = db.scalar(
            select(SolicitudViaje)
            .where(SolicitudViaje.id == reservation_id)
            .with_for_update(of=SolicitudViaje)
        )
        if not locked:
            raise HTTPException(status_code=404, detail="Reserva no encontrada")
    query = (
        select(SolicitudViaje)
        .options(
            joinedload(SolicitudViaje.viaje).joinedload(Viaje.creador),
            joinedload(SolicitudViaje.viaje).joinedload(Viaje.vehiculo),
            joinedload(SolicitudViaje.pasajero),
            joinedload(SolicitudViaje.conversacion),
        )
        .where(SolicitudViaje.id == reservation_id)
    )
    request = db.scalar(query)
    if not request or user_id not in {request.pasajero_id, request.viaje.creador_id}:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    if request.estado not in {"aceptada", "finalizada", "cancelada"}:
        raise HTTPException(status_code=409, detail="La reserva aún no habilita la hoja de ruta")
    return request


def _event(db: Session, request: SolicitudViaje, actor_id: int, kind: str, description: str, key: str) -> EventoViaje:
    existing = db.scalar(select(EventoViaje).where(EventoViaje.idempotency_key == key))
    if existing:
        return existing
    event = EventoViaje(viaje_id=request.viaje_id, reserva_id=request.id, actor_id=actor_id, tipo=kind, descripcion_publica=description, metadata_evento={}, idempotency_key=key)
    db.add(event)
    if request.conversacion:
        add_system_message(db, request.conversacion, description, f"system:roadmap:{key}")
    return event


def record_reservation_accepted(db: Session, request: SolicitudViaje, actor_id: int) -> None:
    request.estado_pasajero = "confirmado"
    _event(db, request, actor_id, "reserva_confirmada", "La reserva fue confirmada.", f"reservation:{request.id}:confirmed")


def sync_meeting_stop(db: Session, request: SolicitudViaje) -> None:
    stop = db.scalar(select(ParadaViaje).where(ParadaViaje.reserva_id == request.id, ParadaViaje.tipo == "recogida"))
    if not stop:
        max_order = max((item.orden for item in request.viaje.paradas), default=1)
        stop = ParadaViaje(viaje_id=request.viaje_id, reserva_id=request.id, orden=max_order + 1, tipo="recogida", nombre_publico="Punto de encuentro")
        db.add(stop)
    stop.zona_general = request.punto_encuentro_propuesto
    stop.latitud = request.punto_encuentro_latitud
    stop.longitud = request.punto_encuentro_longitud
    stop.estado = "pendiente"


def _synthetic_stops(request: SolicitudViaje) -> list[RoadmapStop]:
    trip = request.viaje
    stops = [RoadmapStop(orden=1, tipo="origen", nombre_publico=trip.punto_salida, zona_general=trip.origen, latitud=float(trip.punto_salida_latitud) if trip.punto_salida_latitud is not None else None, longitud=float(trip.punto_salida_longitud) if trip.punto_salida_longitud is not None else None, hora_estimada=trip.fecha, hora_real=None, estado="completada" if trip.estado not in {"publicado", "completo", "programado", "preparando_salida"} else "actual")]
    if request.punto_encuentro_propuesto:
        stops.append(RoadmapStop(reserva_id=request.id, orden=2, tipo="recogida", nombre_publico="Punto de encuentro", zona_general=request.punto_encuentro_propuesto, latitud=float(request.punto_encuentro_latitud) if request.punto_encuentro_latitud is not None else None, longitud=float(request.punto_encuentro_longitud) if request.punto_encuentro_longitud is not None else None, hora_estimada=None, hora_real=None, estado="actual" if trip.estado in {"conductor_en_camino", "conductor_en_punto", "abordaje"} else "pendiente"))
    stops.append(RoadmapStop(orden=len(stops) + 1, tipo="destino", nombre_publico=trip.punto_llegada, zona_general=trip.destino, latitud=float(trip.punto_llegada_latitud) if trip.punto_llegada_latitud is not None else None, longitud=float(trip.punto_llegada_longitud) if trip.punto_llegada_longitud is not None else None, hora_estimada=None, hora_real=None, estado="completada" if trip.estado == "finalizado" else "pendiente"))
    return stops


def _next_action(request: SolicitudViaje, role: str) -> NextAction:
    trip = request.viaje
    if trip.estado in {"finalizado", "cancelado"} or request.estado == "cancelada":
        return NextAction(label="Viaje finalizado" if trip.estado == "finalizado" else "Sin acciones disponibles", action="none", enabled=False, reason_disabled="La hoja de ruta está cerrada")
    if role == "pasajero":
        mapping = {"confirmado": ("Confirmar que estoy listo", "listo"), "listo": ("Indicar que llegué", "llegue")}
        label, action = mapping.get(request.estado_pasajero, ("Abrir chat", "chat"))
        return NextAction(label=label, action=action)
    mapping = {
        "publicado": ("Preparar salida", "preparar-salida"), "completo": ("Preparar salida", "preparar-salida"), "programado": ("Preparar salida", "preparar-salida"),
        "preparando_salida": ("Salir hacia el punto", "salir"), "conductor_en_camino": ("Llegué", "llegar"),
        "conductor_en_punto": ("Confirmar pasajero recogido", "recoger"), "abordaje": ("Iniciar viaje", "iniciar"),
        "en_curso": ("Finalizar viaje", "finalizar"), "pausado": ("Reanudar viaje", "reanudar"),
    }
    label, action = mapping.get(trip.estado, ("Sin acciones disponibles", "none"))
    if trip.estado == "conductor_en_punto" and request.estado_pasajero == "recogido":
        label, action = "Confirmar pasajero abordado", "abordar"
    return NextAction(label=label, action=action, enabled=action != "none", confirmation_required=action in {"finalizar"})


def get_roadmap(db: Session, reservation_id: int, user_id: int) -> RoadmapResponse:
    request = _reservation(db, reservation_id, user_id)
    trip = request.viaje
    role = "conductor" if trip.creador_id == user_id else "pasajero"
    stored_stops = list(db.scalars(select(ParadaViaje).where(ParadaViaje.viaje_id == trip.id).order_by(ParadaViaje.orden)))
    events = list(db.scalars(select(EventoViaje).where(EventoViaje.viaje_id == trip.id).order_by(EventoViaje.created_at)))
    return RoadmapResponse(
        reserva=RoadmapReserva(id=request.id, estado=request.estado, rol_actual=role),
        viaje=RoadmapViaje(id=trip.id, origen=trip.origen, destino=trip.destino, fecha_salida=trip.fecha, estado=trip.estado, cupos_totales=trip.cupos_totales, cupos_ocupados=trip.cupos_totales-trip.cupos_disponibles, ruta_codificada=trip.ruta_codificada),
        conductor=RoadmapPersona(id=trip.creador.id, nombre=trip.creador.nombre), pasajero=RoadmapPersona(id=request.pasajero.id, nombre=request.pasajero.nombre),
        vehiculo=RoadmapVehiculo(marca=trip.vehiculo.marca, modelo=trip.vehiculo.modelo, color=trip.vehiculo.color, matricula=trip.vehiculo.matricula) if trip.vehiculo else None,
        punto_encuentro=RoadmapMeetingPoint(estado=request.estado_punto_encuentro, texto=request.punto_encuentro_propuesto, latitud=float(request.punto_encuentro_latitud) if request.punto_encuentro_latitud is not None else None, longitud=float(request.punto_encuentro_longitud) if request.punto_encuentro_longitud is not None else None),
        paradas=[RoadmapStop.model_validate(stop) for stop in stored_stops] if stored_stops else _synthetic_stops(request),
        eventos=[RoadmapEvent(id=e.id, reserva_id=e.reserva_id, tipo=e.tipo, descripcion_publica=e.descripcion_publica, metadata=e.metadata_evento, created_at=e.created_at) for e in events],
        estado_pasajero=PassengerStatus(estado=request.estado_pasajero, nombre=request.pasajero.nombre), proxima_accion=_next_action(request, role),
        permisos=RoadmapPermissions(puede_operar_viaje=role == "conductor", puede_actualizar_estado_propio=role == "pasajero"),
    )


def trip_action(db: Session, trip_id: int, user_id: int, action: str) -> tuple[RoadmapResponse, dict]:
    config = TRIP_TRANSITIONS.get(action)
    if not config:
        raise HTTPException(status_code=404, detail="Acción no encontrada")
    trip = db.scalar(select(Viaje).where(Viaje.id == trip_id).with_for_update())
    if not trip or trip.creador_id != user_id:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    request = db.scalar(select(SolicitudViaje).where(SolicitudViaje.viaje_id == trip_id, SolicitudViaje.estado == "aceptada").order_by(SolicitudViaje.id).with_for_update())
    if not request:
        raise HTTPException(status_code=409, detail="El viaje no tiene reservas aceptadas")
    allowed, target, kind, description = config
    if trip.estado == target:
        return get_roadmap(db, request.id, user_id), {"type": "trip.status.changed", "data": {"estado": target}}
    if trip.estado not in allowed:
        raise HTTPException(status_code=409, detail=f"No se puede ejecutar la acción desde {trip.estado}")
    if action == "iniciar":
        pending = db.scalar(select(SolicitudViaje.id).where(SolicitudViaje.viaje_id == trip_id, SolicitudViaje.estado == "aceptada", SolicitudViaje.estado_pasajero.not_in({"abordo", "ausente"})).limit(1))
        if pending:
            raise HTTPException(status_code=409, detail="Aún hay pasajeros pendientes de abordaje")
    trip.estado = target
    if target == "finalizado":
        for accepted in db.scalars(select(SolicitudViaje).where(SolicitudViaje.viaje_id == trip_id, SolicitudViaje.estado == "aceptada")):
            accepted.estado = "finalizada"; accepted.estado_pasajero = "completado"
    _event(db, request, user_id, kind, description, f"trip:{trip_id}:{kind}")
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback(); raise
    return get_roadmap(db, request.id, user_id), {"type": "trip.status.changed", "data": {"estado": target, "viaje_id": trip_id}}


def passenger_action(db: Session, reservation_id: int, user_id: int, action: str) -> tuple[RoadmapResponse, dict]:
    config = PASSENGER_ACTIONS.get(action)
    if not config:
        raise HTTPException(status_code=404, detail="Acción no encontrada")
    request = _reservation(db, reservation_id, user_id, lock=True)
    allowed, target, kind, description = config
    is_driver_action = action in {"recoger", "abordar"}
    if (is_driver_action and request.viaje.creador_id != user_id) or (not is_driver_action and request.pasajero_id != user_id):
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    if request.estado_pasajero == target:
        return get_roadmap(db, request.id, user_id), {"type": "passenger.status.changed", "data": {"estado": target}}
    if request.estado_pasajero not in allowed:
        raise HTTPException(status_code=409, detail=f"No se puede ejecutar la acción desde {request.estado_pasajero}")
    if is_driver_action and request.viaje.estado not in {"conductor_en_punto", "abordaje"}:
        raise HTTPException(status_code=409, detail="El conductor todavía no está en el punto")
    request.estado_pasajero = target
    if target == "abordo":
        request.viaje.estado = "abordaje"
    _event(db, request, user_id, kind, description, f"reservation:{request.id}:{kind}")
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback(); raise
    return get_roadmap(db, request.id, user_id), {"type": "passenger.status.changed", "data": {"estado": target, "reserva_id": request.id}}
