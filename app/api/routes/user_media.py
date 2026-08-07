from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.user_schema import UsuarioResponse
from app.services import media_service


router = APIRouter()


def _media_http_error(error: media_service.MediaError) -> HTTPException:
    if isinstance(error, media_service.MediaValidationError):
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error))
    if isinstance(error, media_service.MediaConfigurationError):
        return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error))


@router.post("/me/imagen", response_model=UsuarioResponse)
async def upload_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    try:
        previous_public_id = user.imagen_public_id
        asset = await media_service.upload_image(file, owner="users", owner_id=user.id)
        user.imagen_url = asset.secure_url
        user.imagen_public_id = asset.public_id
    except media_service.MediaError as error:
        raise _media_http_error(error) from error
    db.commit()
    db.refresh(user)
    if previous_public_id and previous_public_id != user.imagen_public_id:
        try:
            await media_service.delete_image(public_id=previous_public_id)
        except media_service.MediaError:
            pass
    return user


@router.delete("/me/imagen", response_model=UsuarioResponse)
async def delete_profile_image(
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
):
    previous_public_id = user.imagen_public_id
    user.imagen_url = None
    user.imagen_public_id = None
    db.commit()
    db.refresh(user)
    if previous_public_id:
        try:
            await media_service.delete_image(public_id=previous_public_id)
        except media_service.MediaError:
            pass
    return user
