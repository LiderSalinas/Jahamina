from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.vehiculo import Vehiculo
from app.models.viaje_model import Viaje
from app.schemas.vehiculo_schema import VehiculoCreate, VehiculoUpdate


def _vehiculo_del_propietario(
    db: Session,
    vehiculo_id: int,
    propietario_id: int,
) -> Vehiculo:
    vehiculo = db.get(Vehiculo, vehiculo_id)
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    if vehiculo.propietario_id != propietario_id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso sobre este vehículo",
        )
    return vehiculo


def crear_vehiculo(
    db: Session,
    data: VehiculoCreate,
    propietario_id: int,
) -> Vehiculo:
    vehiculo = Vehiculo(propietario_id=propietario_id, **data.model_dump())
    try:
        db.add(vehiculo)
        db.commit()
        db.refresh(vehiculo)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La matrícula ya está registrada",
        ) from error
    return vehiculo


def listar_vehiculos(db: Session, propietario_id: int) -> list[Vehiculo]:
    return list(
        db.scalars(
            select(Vehiculo)
            .where(Vehiculo.propietario_id == propietario_id)
            .order_by(Vehiculo.created_at.desc())
        )
    )


def obtener_vehiculo(
    db: Session,
    vehiculo_id: int,
    propietario_id: int,
) -> Vehiculo:
    return _vehiculo_del_propietario(db, vehiculo_id, propietario_id)


def actualizar_vehiculo(
    db: Session,
    vehiculo_id: int,
    propietario_id: int,
    data: VehiculoUpdate,
) -> Vehiculo:
    vehiculo = _vehiculo_del_propietario(db, vehiculo_id, propietario_id)
    changes = data.model_dump(exclude_unset=True)
    if "capacidad" in changes:
        max_cupos = db.scalar(
            select(func.max(Viaje.cupos_totales)).where(
                Viaje.vehiculo_id == vehiculo.id,
                Viaje.estado.in_(["publicado", "completo", "en_curso"]),
            )
        )
        if max_cupos and changes["capacidad"] < max_cupos:
            raise HTTPException(
                status_code=409,
                detail="La capacidad es menor a los cupos de un viaje activo",
            )
    for field, value in changes.items():
        setattr(vehiculo, field, value)
    try:
        db.commit()
        db.refresh(vehiculo)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="La matrícula ya está registrada",
        ) from error
    return vehiculo


def desactivar_vehiculo(
    db: Session,
    vehiculo_id: int,
    propietario_id: int,
) -> Vehiculo:
    vehiculo = _vehiculo_del_propietario(db, vehiculo_id, propietario_id)
    if not vehiculo.activo:
        raise HTTPException(
            status_code=409,
            detail="El vehículo ya está inactivo",
        )
    vehiculo.activo = False
    try:
        db.commit()
        db.refresh(vehiculo)
    except SQLAlchemyError:
        db.rollback()
        raise
    return vehiculo
