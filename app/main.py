from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models as _models  # noqa: F401
from app.api.routes import auth, chat, maps, meeting, notifications, roadmap, solicitudes, tracking, vehiculos, viajes
from app.core.db import get_db
from app.core.settings import settings

app = FastAPI(
    title="Jahamina",
    version="1.0.0",
    description="API para viajes compartidos",
    docs_url="/docs",
    redoc_url=None,
    openapi_tags=[
        {"name": "Sistema", "description": "Estado del servicio"},
        {"name": "Autenticación", "description": "Registro, login y perfil"},
        {"name": "Vehículos", "description": "Vehículos del conductor"},
        {"name": "Viajes", "description": "Operaciones con viajes"},
        {"name": "Solicitudes", "description": "Reservas y aprobaciones"},
        {"name": "Chat", "description": "Conversaciones privadas"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(vehiculos.router, prefix="/vehiculos", tags=["Vehículos"])
app.include_router(viajes.router, prefix="/viajes", tags=["Viajes"])
app.include_router(solicitudes.router, tags=["Solicitudes"])
app.include_router(chat.router, tags=["Chat"])
app.include_router(maps.router, tags=["Mapas"])
app.include_router(meeting.router, tags=["Punto de encuentro"])
app.include_router(tracking.router, tags=["Seguimiento"])
app.include_router(roadmap.router, tags=["Hoja de ruta"])
app.include_router(notifications.router, tags=["Notificaciones"])


@app.get("/health", tags=["Sistema"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible",
        ) from error
    return {"status": "ok"}
