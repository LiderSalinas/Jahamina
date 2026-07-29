from datetime import timedelta

from app.core.jwt import create_access_token

def crear_token_acceso(data: dict, expires_delta: timedelta = timedelta(minutes=30)):
    return create_access_token(data, expires_delta)
