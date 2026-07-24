from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ViajeCreate(BaseModel):
    origen: str
    destino: str
    fecha: datetime

class ViajeResponse(BaseModel):
    id: int
    origen: str
    destino: str
    fecha: datetime
    cancelado: bool
    creador_id: int

    class Config:
        from_attributes = True

class ViajeUnidoResponse(BaseModel):
    id: int
    viaje_id: int
    usuario_id: int

    class Config:
        from_attributes = True
