from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.evento_viaje import EventoViaje
from app.models.parada_viaje import ParadaViaje
from app.models.solicitud_viaje import SolicitudViaje
from app.models.viaje_model import Viaje
from app.schemas.roadmap_schema import (
    DerivedRoadmapStep, NextAction, PassengerStatus, RoadmapEvent, RoadmapMeetingPoint,
    RoadmapOccupancy,
    RoadmapPermissions, RoadmapPersona, RoadmapReserva, RoadmapResponse,
    RoadmapStop, RoadmapVehiculo, RoadmapViaje,
)
from app.services.chat_service import add_system_message


TRIP_TRANSITIONS = {
    "preparar-salida": ({"publicado", "completo", "programado"}, "preparando_salida", "conductor_preparando_salida", "El conductor está preparando la salida."),
    "salir": ({"publicado", "completo", "programado", "preparando_salida"}, "conductor_en_camino", "conductor_en_camino", "El conductor salió hacia el punto de encuentro."),
    "llegar": ({"conductor_en_camino"}, "conductor_en_punto", "conductor_llego", "El conductor llegó al punto de encuentro."),
    "iniciar": ({"conductor_en_camino", "conductor_en_punto", "abordaje"}, "en_curso", "viaje_iniciado", "El viaje comenzó."),
    "pausar": ({"en_curso"}, "pausado", "viaje_pausado", "El viaje fue pausado."),
    "reanudar": ({"pausado"}, "en_curso", "viaje_reanudado", "El viaje se reanudó."),
    "finalizar": ({"en_curso", "pausado"}, "finalizado", "viaje_finalizado", "El viaje finalizó."),
}

PASSENGER_ACTIONS = {
    "listo": ({"confirmado"}, "listo", "pasajero_listo", "El pasajero confirmó que está listo."),
    "llegue": ({"listo", "esperando"}, "llego_al_punto", "pasajero_llego", "El pasajero llegó al punto de encuentro."),
    "recoger": ({"listo", "esperando", "llego_al_punto"}, "recogido", "pasajero_recogido", "El conductor confirmó la recogida del pasajero."),
    "abordar": ({"recogido"}, "abordo", "pasajero_abordo", "El pasajero fue confirmado a bordo."),
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


def _event(db: Session, request: SolicitudViaje, actor_id: int, kind: str, description: str, key: str) -> tuple[EventoViaje, list, bool]:
    existing = db.scalar(select(EventoViaje).where(EventoViaje.idempotency_key == key))
    if existing:
        return existing, [], False
    event = EventoViaje(viaje_id=request.viaje_id, reserva_id=request.id, actor_id=actor_id, tipo=kind, descripcion_publica=description, metadata_evento={}, idempotency_key=key)
    db.add(event)
    messages = []
    if request.conversacion:
        messages.append(add_system_message(db, request.conversacion, description, f"system:roadmap:{key}"))
    return event, messages, True


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
    pickup_done = request.estado_pasajero in {"abordo", "completado"}
    stops.append(RoadmapStop(reserva_id=request.id, orden=2, tipo="recogida", nombre_publico=f"Recogida de {request.pasajero.nombre}", zona_general=request.punto_encuentro_propuesto or "Punto todavía no definido", latitud=float(request.punto_encuentro_latitud) if request.punto_encuentro_latitud is not None else None, longitud=float(request.punto_encuentro_longitud) if request.punto_encuentro_longitud is not None else None, hora_estimada=None, hora_real=None, estado="completada" if pickup_done else "actual" if trip.estado in {"conductor_en_camino", "conductor_en_punto", "abordaje"} else "pendiente"))
    destination_active = request.estado_pasajero in {"abordo", "completado"} or trip.estado in {"en_curso", "pausado"}
    stops.append(RoadmapStop(orden=len(stops) + 1, tipo="destino", nombre_publico=f"Llegada a {trip.destino}", zona_general=trip.punto_llegada, latitud=float(trip.punto_llegada_latitud) if trip.punto_llegada_latitud is not None else None, longitud=float(trip.punto_llegada_longitud) if trip.punto_llegada_longitud is not None else None, hora_estimada=None, hora_real=None, estado="completada" if trip.estado == "finalizado" else "actual" if destination_active else "pendiente"))
    return stops


def _derived_timeline(request: SolicitudViaje, events: list[EventoViaje]) -> list[DerivedRoadmapStep]:
    cancelled = request.estado == "cancelada" or request.viaje.estado == "cancelado"
    meeting_confirmed = request.estado_punto_encuentro == "confirmado"
    by_type = {event.tipo: event for event in events}
    trip_state = request.viaje.estado
    on_the_way = trip_state in {"conductor_en_camino", "conductor_en_punto", "abordaje", "en_curso", "pausado", "finalizado"}
    in_progress = trip_state in {"en_curso", "pausado", "finalizado"}
    finished = request.estado == "finalizada" or trip_state == "finalizado"
    point_detail = request.punto_encuentro_propuesto or "Todavía falta acordarlo."
    if "pasajero_listo" in by_type:
        point_detail = f"{point_detail} · Pasajero listo."
    driver_detail = "En camino hacia el punto acordado."
    if "pasajero_abordo" in by_type:
        driver_detail = "Encuentro completado · pasajero a bordo."
    elif "conductor_llego" in by_type:
        driver_detail = "El conductor llegó al punto acordado."
    trip_detail = "Viaje pausado temporalmente." if trip_state == "pausado" else f"Trayecto hacia {request.viaje.destino}."
    raw: list[tuple[str, str, str, bool, datetime | None]] = [
        ("reserva-confirmada", "Reserva confirmada", "Tu lugar está reservado.", True, request.responded_at or request.created_at),
        ("punto-confirmado", "Punto de encuentro", point_detail, meeting_confirmed, request.punto_encuentro_actualizado_en if meeting_confirmed else None),
        ("conductor-en-camino", "Conductor en camino", driver_detail, on_the_way, by_type.get("conductor_en_camino").created_at if by_type.get("conductor_en_camino") else None),
        ("viaje-en-curso", "Viaje en curso", trip_detail, in_progress, by_type.get("viaje_iniciado").created_at if by_type.get("viaje_iniciado") else None),
        ("viaje-finalizado", "Viaje finalizado", "Llegaron al destino.", finished, by_type.get("viaje_finalizado").created_at if by_type.get("viaje_finalizado") else None),
    ]
    current_index = 4 if finished else next((index for index, item in enumerate(raw) if not item[3]), 4)
    return [DerivedRoadmapStep(id=key, titulo=title, descripcion=description, estado="cancelado" if cancelled and index >= current_index else "actual" if index == current_index else "completado" if done and index < current_index else "pendiente", timestamp=timestamp, orden=index + 1) for index, (key, title, description, done, timestamp) in enumerate(raw)]


def _next_action(request: SolicitudViaje, role: str) -> NextAction:
    trip = request.viaje
    if trip.estado in {"finalizado", "cancelado"} or request.estado == "cancelada":
        return NextAction(id="none", label="Viaje finalizado" if trip.estado == "finalizado" else "Sin acciones disponibles", enabled=False, reason_disabled="La hoja de ruta está cerrada")
    if role == "pasajero":
        mapping = {"confirmado": ("Confirmar que estoy listo", "listo")}
        label, action = mapping.get(request.estado_pasajero, ("Abrir chat", "chat"))
        return NextAction(id=action, label=label)
    mapping = {
        "publicado": ("Salir hacia el punto", "salir"), "completo": ("Salir hacia el punto", "salir"), "programado": ("Salir hacia el punto", "salir"),
        "preparando_salida": ("Salir hacia el punto", "salir"),
        "conductor_en_camino": ("Iniciar viaje", "iniciar"), "conductor_en_punto": ("Iniciar viaje", "iniciar"), "abordaje": ("Iniciar viaje", "iniciar"),
        "en_curso": ("Finalizar viaje", "finalizar"), "pausado": ("Finalizar viaje", "finalizar"),
    }
    label, action = mapping.get(trip.estado, ("Sin acciones disponibles", "none"))
    return NextAction(id=action, label=label, enabled=action != "none", confirmation_required=action in {"finalizar"})


def get_roadmap(db: Session, reservation_id: int, user_id: int) -> RoadmapResponse:
    request = _reservation(db, reservation_id, user_id)
    trip = request.viaje
    role = "conductor" if trip.creador_id == user_id else "pasajero"
    pending = db.scalar(select(func.count(SolicitudViaje.id)).where(SolicitudViaje.viaje_id == trip.id, SolicitudViaje.estado == "pendiente")) or 0
    events = list(db.scalars(select(EventoViaje).where(EventoViaje.viaje_id == trip.id).order_by(EventoViaje.created_at)))
    return RoadmapResponse(
        reserva=RoadmapReserva(id=request.id, estado=request.estado, rol_actual=role, mensaje_inicial=request.mensaje_inicial),
        viaje=RoadmapViaje(id=trip.id, origen=trip.origen, destino=trip.destino, fecha_salida=trip.fecha, estado=trip.estado, cupos_totales=trip.cupos_totales, cupos_ocupados=trip.cupos_totales-trip.cupos_disponibles, ruta_codificada=trip.ruta_codificada),
        conductor=RoadmapPersona(id=trip.creador.id, nombre=trip.creador.nombre, imagen_url=trip.creador.imagen_url), pasajero_actual=RoadmapPersona(id=request.pasajero.id, nombre=request.pasajero.nombre, imagen_url=request.pasajero.imagen_url),
        vehiculo=RoadmapVehiculo(id=trip.vehiculo.id, marca=trip.vehiculo.marca, modelo=trip.vehiculo.modelo, color=trip.vehiculo.color, matricula=trip.vehiculo.matricula, imagen_url=trip.vehiculo.imagen_url) if trip.vehiculo else None,
        punto_encuentro=RoadmapMeetingPoint(estado=request.estado_punto_encuentro, nombre_publico="Punto de encuentro" if request.punto_encuentro_propuesto else None, zona_general=request.punto_encuentro_propuesto, latitud=float(request.punto_encuentro_latitud) if request.estado != "cancelada" and request.punto_encuentro_latitud is not None else None, longitud=float(request.punto_encuentro_longitud) if request.estado != "cancelada" and request.punto_encuentro_longitud is not None else None),
        paradas=_synthetic_stops(request),
        hoja_ruta=_derived_timeline(request, events),
        ocupacion=RoadmapOccupancy(
            ocupados=trip.cupos_totales-trip.cupos_disponibles,
            abordo=db.scalar(select(func.count(SolicitudViaje.id)).where(
                SolicitudViaje.viaje_id == trip.id,
                SolicitudViaje.estado_pasajero.in_({"abordo", "completado"}),
            )) or 0,
            totales=trip.cupos_totales,
            pendientes=pending,
        ),
        eventos=[RoadmapEvent(id=e.id, reserva_id=e.reserva_id, tipo=e.tipo, descripcion_publica=e.descripcion_publica, metadata=e.metadata_evento, created_at=e.created_at) for e in events],
        estado_pasajero=PassengerStatus(estado=request.estado_pasajero, nombre=request.pasajero.nombre), proxima_accion=_next_action(request, role),
        permisos=RoadmapPermissions(puede_operar_viaje=False, puede_actualizar_estado_propio=False, puede_ver_puntos_exactos=request.estado != "cancelada", puede_ver_chat=bool(request.conversacion), puede_ver_punto_exacto=request.estado != "cancelada", puede_modificar_viaje=False),
    )


def trip_action(db: Session, trip_id: int, user_id: int, action: str) -> tuple[RoadmapResponse, dict]:
    config = TRIP_TRANSITIONS.get(action)
    if not config:
        raise HTTPException(status_code=404, detail="Acción no encontrada")
    trip = db.scalar(select(Viaje).where(Viaje.id == trip_id).with_for_update())
    if not trip or trip.creador_id != user_id:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    request = db.scalar(select(SolicitudViaje).where(SolicitudViaje.viaje_id == trip_id, SolicitudViaje.estado.in_({"aceptada", "finalizada"})).order_by(SolicitudViaje.id).with_for_update())
    if not request:
        raise HTTPException(status_code=409, detail="El viaje no tiene reservas aceptadas")
    allowed, target, kind, description = config
    if trip.estado == target:
        return get_roadmap(db, request.id, user_id), {"type": "trip.status.changed", "data": {"estado": target}, "messages": [], "created": False}
    if trip.estado not in allowed:
        raise HTTPException(status_code=409, detail=f"No se puede ejecutar la acción desde {trip.estado}")
    trip.estado = target
    if action == "iniciar":
        for accepted in db.scalars(select(SolicitudViaje).where(SolicitudViaje.viaje_id == trip_id, SolicitudViaje.estado == "aceptada")):
            if accepted.estado_pasajero != "ausente":
                accepted.estado_pasajero = "abordo"
            pickup = db.scalar(select(ParadaViaje).where(ParadaViaje.reserva_id == accepted.id, ParadaViaje.tipo == "recogida"))
            if pickup:
                pickup.estado = "completada"
    if target == "finalizado":
        for accepted in db.scalars(select(SolicitudViaje).where(SolicitudViaje.viaje_id == trip_id, SolicitudViaje.estado == "aceptada")):
            accepted.estado = "finalizada"; accepted.estado_pasajero = "completado"
    event, messages, created = _event(db, request, user_id, kind, description, f"trip:{trip_id}:{kind}")
    if created:
        for related in db.scalars(select(SolicitudViaje).where(
            SolicitudViaje.viaje_id == trip_id,
            SolicitudViaje.estado.in_({"aceptada", "finalizada"}),
            SolicitudViaje.id != request.id,
        )):
            if related.conversacion:
                messages.append(add_system_message(db, related.conversacion, description, f"system:roadmap:trip:{trip_id}:{kind}"))
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback(); raise
    return get_roadmap(db, request.id, user_id), {"type": "trip.status.changed", "data": {"estado": target, "viaje_id": trip_id, "evento_id": event.id}, "messages": messages, "created": created}


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
        return get_roadmap(db, request.id, user_id), {"type": "passenger.status.changed", "data": {"estado": target}, "messages": [], "created": False}
    if request.estado_pasajero not in allowed:
        raise HTTPException(status_code=409, detail=f"No se puede ejecutar la acción desde {request.estado_pasajero}")
    if is_driver_action and request.viaje.estado not in {"conductor_en_punto", "abordaje"}:
        raise HTTPException(status_code=409, detail="El conductor todavía no está en el punto")
    request.estado_pasajero = target
    pickup_stop = db.scalar(select(ParadaViaje).where(
        ParadaViaje.reserva_id == request.id,
        ParadaViaje.tipo == "recogida",
    ))
    if pickup_stop and target in {"llego_al_punto", "recogido", "abordo"}:
        pickup_stop.estado = "completada" if target == "abordo" else "actual"
    if target == "abordo":
        request.viaje.estado = "abordaje"
    public_description = description.replace("El pasajero", request.pasajero.nombre)
    event, messages, created = _event(db, request, user_id, kind, public_description, f"reservation:{request.id}:{kind}")
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback(); raise
    return get_roadmap(db, request.id, user_id), {"type": "passenger.status.changed", "data": {"estado": target, "reserva_id": request.id, "evento_id": event.id}, "messages": messages, "created": created}
