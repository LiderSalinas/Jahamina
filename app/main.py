from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, viajes
from app.core.db import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(    title="Jahamina",
    version="0.1.0",
    description="API para viajes compartidos",
    docs_url="/docs",
    redoc_url=None,
    openapi_tags=[
        {"name": "Autenticación", "description": "Registro y Login"},
        {"name": "Viajes", "description": "Operaciones con viajes"},
    ],
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True
    }
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(viajes.router, prefix="/viajes", tags=["Viajes"])
