from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.solicitud_viaje import SolicitudViaje
from app.models.evento_viaje import EventoViaje
from app.models.vehiculo import Vehiculo
from app.models.viaje_model import Viaje
from app.schemas.viaje_schema import ViajeCreate


def crear_viaje(db: Session, viaje_data: ViajeCreate, usuario_id: int):
    vehiculo = db.get(Vehiculo, viaje_data.vehiculo_id)
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    if vehiculo.propietario_id != usuario_id:
        raise HTTPException(
            status_code=403,
            detail="El vehículo no pertenece al conductor",
        )
    if not vehiculo.activo:
        raise HTTPException(
            status_code=400,
            detail="No puedes usar un vehículo inactivo",
        )
    if viaje_data.cupos_totales > vehiculo.capacidad:
        raise HTTPException(
            status_code=400,
            detail="Los cupos superan la capacidad del vehículo",
        )
    nuevo_viaje = Viaje(
        **viaje_data.model_dump(),
        creador_id=usuario_id,
        cupos_disponibles=viaje_data.cupos_totales,
        estado="publicado",
        cancelado=False,
    )
    try:
        db.add(nuevo_viaje)
        db.commit()
        db.refresh(nuevo_viaje)
    except SQLAlchemyError:
        db.rollback()
        raise
    return nuevo_viaje


def obtener_viajes_disponibles(db: Session):
    return list(
        db.scalars(
            select(Viaje).where(
                Viaje.estado == "publicado",
                Viaje.cupos_disponibles > 0,
                Viaje.fecha > datetime.now(),
            )
        )
    )


def obtener_mis_viajes(db: Session, usuario_id: int):
    return list(
        db.scalars(select(Viaje).where(Viaje.creador_id == usuario_id))
    )


def cancelar_viaje(db: Session, viaje_id: int, usuario_id: int):
    viaje = db.get(Viaje, viaje_id)
    if not viaje:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    if viaje.creador_id != usuario_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para cancelar este viaje",
        )
    if viaje.estado == "cancelado":
        raise HTTPException(status_code=409, detail="El viaje ya está cancelado")
    if viaje.estado == "finalizado":
        raise HTTPException(
            status_code=400,
            detail="No puedes cancelar un viaje finalizado",
        )
    viaje.cancelado = True
    viaje.estado = "cancelado"
    if not db.scalar(select(EventoViaje).where(EventoViaje.idempotency_key == f"trip:{viaje.id}:viaje_cancelado")):
        db.add(EventoViaje(
            viaje_id=viaje.id,
            actor_id=usuario_id,
            tipo="viaje_cancelado",
            descripcion_publica="El viaje fue cancelado.",
            metadata_evento={},
            idempotency_key=f"trip:{viaje.id}:viaje_cancelado",
        ))
    solicitudes = list(
        db.scalars(
            select(SolicitudViaje).where(
                SolicitudViaje.viaje_id == viaje.id,
                SolicitudViaje.estado.in_(["pendiente", "aceptada"]),
            )
        )
    )
    for solicitud in solicitudes:
        solicitud.estado = "cancelada"
        solicitud.estado_pasajero = "cancelado"
        from app.services.chat_service import close_with_system_message

        close_with_system_message(
            db,
            solicitud,
            "El viaje fue cancelado. El chat quedó cerrado.",
            f"system:trip:{viaje.id}:cancelled:request:{solicitud.id}",
        )
    try:
        db.commit()
        db.refresh(viaje)
    except SQLAlchemyError:
        db.rollback()
        raise
    return viaje


def unirse_a_viaje(db: Session, viaje_id: int, usuario_id: int):
    from app.schemas.solicitud_schema import SolicitudCreate
    from app.services.solicitud_service import crear_solicitud

    return crear_solicitud(
        db,
        viaje_id,
        usuario_id,
        SolicitudCreate(),
    )


def obtener_viajes_unidos(db: Session, usuario_id: int):
    return list(
        db.scalars(
            select(Viaje)
            .join(SolicitudViaje)
            .where(
                SolicitudViaje.pasajero_id == usuario_id,
                SolicitudViaje.estado == "aceptada",
                Viaje.estado.not_in(["cancelado", "finalizado"]),
            )
        )
    )


def cambiar_estado_viaje(
    db: Session,
    viaje_id: int,
    usuario_id: int,
    nuevo_estado: str,
) -> Viaje:
    viaje = db.get(Viaje, viaje_id)
    if not viaje:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    if viaje.creador_id != usuario_id:
        raise HTTPException(
            status_code=403,
            detail="Solo el conductor puede cambiar el estado",
        )
    if nuevo_estado == "en_curso" and viaje.estado not in {
        "publicado",
        "completo",
    }:
        raise HTTPException(
            status_code=400,
            detail="El viaje no puede iniciarse en su estado actual",
        )
    if nuevo_estado == "finalizado" and viaje.estado != "en_curso":
        raise HTTPException(
            status_code=400,
            detail="Solo un viaje en curso puede finalizarse",
        )
    viaje.estado = nuevo_estado
    from app.services.chat_service import add_system_message

    for solicitud in viaje.solicitudes:
        if solicitud.conversacion and solicitud.estado == "aceptada":
            if nuevo_estado == "en_curso":
                add_system_message(
                    db,
                    solicitud.conversacion,
                    "El viaje ha comenzado.",
                    f"system:trip:{viaje.id}:started:request:{solicitud.id}",
                )
    if nuevo_estado == "finalizado":
        solicitudes = list(
            db.scalars(
                select(SolicitudViaje).where(
                    SolicitudViaje.viaje_id == viaje.id,
                    SolicitudViaje.estado == "aceptada",
                )
            )
        )
        for solicitud in solicitudes:
            from app.services.chat_service import close_with_system_message

            close_with_system_message(
                db,
                solicitud,
                "El viaje finalizó. El historial queda disponible.",
                f"system:trip:{viaje.id}:finished:request:{solicitud.id}",
            )
            solicitud.estado = "finalizada"
            solicitud.estado_pasajero = "completado"
    try:
        db.commit()
        db.refresh(viaje)
    except SQLAlchemyError:
        db.rollback()
        raise
    return viaje
