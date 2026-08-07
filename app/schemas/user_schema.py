from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# ✅ Esquema para registro
class UsuarioCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return value

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, value: EmailStr) -> str:
        return str(value).lower()

    @field_validator("password")
    @classmethod
    def validar_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña no puede superar 72 bytes")
        return value

# ✅ Esquema para login
class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

# ✅ Esquema de respuesta (opcional para retornar datos del usuario)
class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: EmailStr
    imagen_url: str | None = None

# ✅ Token de respuesta JWT
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
