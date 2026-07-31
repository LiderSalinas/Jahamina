from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.mensaje import Mensaje
from app.models.solicitud_viaje import SolicitudViaje
from app.models.viaje_model import Viaje
from app.schemas.solicitud_schema import (
    ReservaRelacionadaResponse,
    SolicitudCreate,
)


def crear_solicitud(
    db: Session,
    viaje_id: int,
    pasajero_id: int,
    data: SolicitudCreate,
) -> SolicitudViaje:
    viaje = db.get(Viaje, viaje_id)
    if not viaje:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    if viaje.creador_id == pasajero_id:
        raise HTTPException(
            status_code=400,
            detail="No puedes solicitar tu propio viaje",
        )
    if viaje.estado in {"completo", "en_curso", "finalizado", "cancelado"}:
        raise HTTPException(
            status_code=400,
            detail="El viaje no admite nuevas solicitudes",
        )
    if viaje.cupos_disponibles <= 0:
        raise HTTPException(status_code=409, detail="No quedan cupos")
    if viaje.fecha <= datetime.now():
        raise HTTPException(status_code=400, detail="El viaje ya ocurrió")

    solicitud = SolicitudViaje(
        viaje_id=viaje_id,
        pasajero_id=pasajero_id,
        **data.model_dump(),
    )
    try:
        db.add(solicitud)
        db.commit()
        db.refresh(solicitud)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya tienes una solicitud activa para este viaje",
        ) from error
    return solicitud


def listar_mias(db: Session, pasajero_id: int) -> list[SolicitudViaje]:
    return list(
        db.scalars(
            select(SolicitudViaje)
            .where(SolicitudViaje.pasajero_id == pasajero_id)
            .order_by(SolicitudViaje.created_at.desc())
        )
    )


def listar_relacionadas(
    db: Session, usuario_id: int
) -> list[ReservaRelacionadaResponse]:
    solicitudes = list(
        db.scalars(
            select(SolicitudViaje)
            .join(SolicitudViaje.viaje)
            .options(
                joinedload(SolicitudViaje.viaje).joinedload(Viaje.creador),
                joinedload(SolicitudViaje.pasajero),
                joinedload(SolicitudViaje.conversacion),
            )
            .where(
                (SolicitudViaje.pasajero_id == usuario_id)
                | (Viaje.creador_id == usuario_id)
            )
        )
    )
    relacionadas: list[ReservaRelacionadaResponse] = []
    for solicitud in solicitudes:
        viaje = solicitud.viaje
        es_pasajero = solicitud.pasajero_id == usuario_id
        participante = viaje.creador if es_pasajero else solicitud.pasajero
        conversacion = solicitud.conversacion
        ultimo_mensaje = None
        no_leidos = 0
        if conversacion:
            ultimo_mensaje = db.scalar(
                select(Mensaje.contenido)
                .where(
                    Mensaje.conversacion_id == conversacion.id,
                    Mensaje.eliminado.is_(False),
                )
                .order_by(Mensaje.id.desc())
                .limit(1)
            )
            no_leidos = db.scalar(
                select(func.count(Mensaje.id)).where(
                    Mensaje.conversacion_id == conversacion.id,
                    Mensaje.remitente_id.is_not(None),
                    Mensaje.remitente_id != usuario_id,
                    Mensaje.leido_en.is_(None),
                    Mensaje.eliminado.is_(False),
                )
            ) or 0
        relacionadas.append(
            ReservaRelacionadaResponse(
                reserva_id=solicitud.id,
                viaje_id=viaje.id,
                origen=viaje.origen,
                destino=viaje.destino,
                fecha=viaje.fecha,
                estado=solicitud.estado,
                rol="pasajero" if es_pasajero else "conductor",
                participante_id=participante.id,
                participante=participante.nombre,
                conversacion_id=conversacion.id if conversacion else None,
                ultimo_mensaje=ultimo_mensaje,
                no_leidos=no_leidos,
                ultima_actividad=(
                    conversacion.ultimo_mensaje_en
                    if conversacion and conversacion.ultimo_mensaje_en
                    else solicitud.updated_at
                ),
            )
        )
    return sorted(
        relacionadas, key=lambda item: item.ultima_actividad, reverse=True
    )


def listar_del_viaje(
    db: Session,
    viaje_id: int,
    conductor_id: int,
) -> list[SolicitudViaje]:
    viaje = db.get(Viaje, viaje_id)
    if not viaje:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    if viaje.creador_id != conductor_id:
        raise HTTPException(
            status_code=403,
            detail="Solo el conductor puede ver las solicitudes",
        )
    return list(
        db.scalars(
            select(SolicitudViaje)
            .where(SolicitudViaje.viaje_id == viaje_id)
            .order_by(SolicitudViaje.created_at.desc())
        )
    )


def obtener_solicitud(
    db: Session,
    solicitud_id: int,
    usuario_id: int,
) -> SolicitudViaje:
    solicitud = db.get(SolicitudViaje, solicitud_id)
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if (
        solicitud.pasajero_id != usuario_id
        and solicitud.viaje.creador_id != usuario_id
    ):
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return solicitud


def responder_solicitud(
    db: Session,
    solicitud_id: int,
    conductor_id: int,
    aceptar: bool,
) -> SolicitudViaje:
    solicitud = db.scalar(
        select(SolicitudViaje)
        .where(SolicitudViaje.id == solicitud_id)
        .with_for_update()
    )
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    viaje = db.scalar(
        select(Viaje)
        .where(Viaje.id == solicitud.viaje_id)
        .with_for_update()
    )
    if not viaje:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    if viaje.creador_id != conductor_id:
        raise HTTPException(
            status_code=403,
            detail="Solo el conductor puede responder",
        )
    if solicitud.estado != "pendiente":
        raise HTTPException(
            status_code=409,
            detail="La solicitud ya fue respondida",
        )
    if aceptar:
        if viaje.estado != "publicado" or viaje.cupos_disponibles <= 0:
            raise HTTPException(
                status_code=409,
                detail="El viaje no tiene cupos disponibles",
            )
        solicitud.estado = "aceptada"
        viaje.cupos_disponibles -= 1
        if viaje.cupos_disponibles == 0:
            viaje.estado = "completo"
        from app.services.chat_service import create_or_get_conversation

        create_or_get_conversation(db, solicitud)
    else:
        solicitud.estado = "rechazada"
    solicitud.responded_at = datetime.now(timezone.utc)
    try:
        db.commit()
        db.refresh(solicitud)
    except SQLAlchemyError:
        db.rollback()
        raise
    return solicitud


def cancelar_solicitud(
    db: Session,
    solicitud_id: int,
    pasajero_id: int,
) -> SolicitudViaje:
    solicitud = db.scalar(
        select(SolicitudViaje)
        .where(SolicitudViaje.id == solicitud_id)
        .with_for_update()
    )
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if solicitud.pasajero_id != pasajero_id:
        raise HTTPException(
            status_code=403,
            detail="Solo el pasajero puede cancelar su solicitud",
        )
    if solicitud.estado not in {"pendiente", "aceptada"}:
        raise HTTPException(
            status_code=409,
            detail="La solicitud no puede cancelarse",
        )
    viaje = db.scalar(
        select(Viaje)
        .where(Viaje.id == solicitud.viaje_id)
        .with_for_update()
    )
    if (
        solicitud.estado == "aceptada"
        and viaje
        and viaje.estado not in {"en_curso", "finalizado", "cancelado"}
    ):
        viaje.cupos_disponibles = min(
            viaje.cupos_disponibles + 1,
            viaje.cupos_totales,
        )
        if viaje.estado == "completo":
            viaje.estado = "publicado"
    solicitud.estado = "cancelada"
    from app.services.chat_service import close_with_system_message

    close_with_system_message(
        db,
        solicitud,
        "La reserva fue cancelada. El historial queda disponible.",
        f"system:request:{solicitud.id}:cancelled",
    )
    try:
        db.commit()
        db.refresh(solicitud)
    except SQLAlchemyError:
        db.rollback()
        raise
    return solicitud
