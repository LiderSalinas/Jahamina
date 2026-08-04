from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.map_schema import GeocodingResult, RouteRequest, RouteResponse
from app.services import map_service

router = APIRouter()


@router.get("/mapas/geocodificar", response_model=list[GeocodingResult])
async def geocodificar(
    q: str = Query(min_length=3, max_length=150),
    _: Usuario = Depends(get_current_user),
):
    return await map_service.geocode(q)


@router.post("/mapas/ruta", response_model=RouteResponse)
async def calcular_ruta(
    data: RouteRequest,
    _: Usuario = Depends(get_current_user),
):
    return await map_service.route(data.origin, data.destination)
