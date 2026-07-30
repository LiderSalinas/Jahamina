from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import obtener_password_hash, verificar_contraseña
from app.models.usuario import Usuario
from app.schemas.user_schema import UsuarioCreate


def crear_usuario(db: Session, usuario: UsuarioCreate) -> Usuario:
    existente = db.scalar(select(Usuario).where(Usuario.email == usuario.email))
    if existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya existe",
        )

    usuario_db = Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        hashed_password=obtener_password_hash(usuario.password),
    )
    try:
        db.add(usuario_db)
        db.commit()
        db.refresh(usuario_db)
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El usuario ya existe",
        ) from error
    return usuario_db


def autenticar_usuario(
    db: Session,
    email: str,
    password: str,
) -> Usuario | None:
    usuario = db.scalar(
        select(Usuario).where(Usuario.email == email.strip().lower())
    )
    if not usuario:
        return None
    if not verificar_contraseña(password, usuario.hashed_password):
        return None
    return usuario
