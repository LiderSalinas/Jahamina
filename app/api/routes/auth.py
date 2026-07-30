from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.jwt import create_access_token
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.user_schema import TokenResponse, UsuarioCreate, UsuarioResponse
from app.services import user_service

router = APIRouter()

@router.get("/me", response_model=UsuarioResponse)
def obtener_usuario_actual(
    usuario: Usuario = Depends(get_current_user),
):
    return usuario

@router.post(
    "/registro",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    return user_service.crear_usuario(db, usuario)

@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = user_service.autenticar_usuario(
        db,
        form_data.username,
        form_data.password,
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": usuario.email})
    return {"access_token": access_token, "token_type": "bearer"}
