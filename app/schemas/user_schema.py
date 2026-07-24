from pydantic import BaseModel, EmailStr

# ✅ Esquema para registro
class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str

# ✅ Esquema para login
class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

# ✅ Esquema de respuesta (opcional para retornar datos del usuario)
class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: EmailStr

    class Config:
        orm_mode = True

# ✅ Token de respuesta JWT
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
