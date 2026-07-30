from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.solicitud_viaje import SolicitudViaje
from app.models.viaje_model import Viaje
from app.schemas.solicitud_schema import SolicitudCreate


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
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para ver esta solicitud",
        )
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
    try:
        db.commit()
        db.refresh(solicitud)
    except SQLAlchemyError:
        db.rollback()
        raise
    return solicitud
