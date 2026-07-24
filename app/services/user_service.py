from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.schemas.user_schema import UsuarioCreate
from app.core.security import obtener_password_hash, verificar_contraseña


# ✅ Crear un nuevo usuario
def crear_usuario(db: Session, usuario: UsuarioCreate) -> Usuario:
    usuario_db = Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        hashed_password=obtener_password_hash(usuario.password)
    )
    db.add(usuario_db)
    db.commit()
    db.refresh(usuario_db)
    return usuario_db


# ✅ Autenticar usuario (verifica que exista y que la contraseña coincida)
def autenticar_usuario(db: Session, email: str, password: str):
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario:
        return None
    if not verificar_contraseña(password, usuario.hashed_password):
        return None
    return usuario
