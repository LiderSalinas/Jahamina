from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.models.usuario import Usuario
from app.schemas.user_schema import UsuarioCreate, UsuarioResponse, TokenResponse
from app.core.db import get_db
from app.core.security import obtener_password_hash, verificar_contraseña
from app.core.security import get_current_user
from app.core.jwt import create_access_token

router = APIRouter()

@router.get("/me", response_model=UsuarioResponse)
def obtener_usuario_actual(
    usuario: Usuario = Depends(get_current_user),
):
    return usuario

@router.post("/registro", response_model=UsuarioResponse)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    usuario_existente = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    hashed_password = obtener_password_hash(usuario.password)
    nuevo_usuario = Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        hashed_password=hashed_password
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    email = form_data.username.strip().lower()
    usuario = db.query(Usuario).filter(Usuario.email == email).first()
    if not usuario or not verificar_contraseña(form_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": usuario.email})
    return {"access_token": access_token, "token_type": "bearer"}
