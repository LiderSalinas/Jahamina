from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.usuario import Usuario
from app.core.settings import settings

# Contexto para encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de autenticación con OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Hashea una contraseña en texto plano
def obtener_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Verifica si una contraseña en texto plano coincide con su hash
def verificar_contraseña(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Decodifica el token JWT y devuelve los datos del payload
def decodificar_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
        )

# Obtiene el usuario autenticado a partir del token JWT
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    payload = decodificar_token(token)
    email = payload.get("sub")
    if email is None:
        raise HTTPException(status_code=401, detail="Token inválido: no contiene email")

    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return usuario
