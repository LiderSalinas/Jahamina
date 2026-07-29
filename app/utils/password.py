from app.core.security import obtener_password_hash, verificar_contraseña

def hash_password(password: str) -> str:
    return obtener_password_hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return verificar_contraseña(plain_password, hashed_password)
