"""
Schemas Pydantic para autenticacion (JWT).
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class Token(BaseModel):
    """
    Schema para respuesta de token JWT.

    Retornado por el endpoint POST /auth/login.
    """
    access_token: str = Field(..., description="Token JWT")
    token_type: str = Field(default="bearer", description="Tipo de token")


class TokenData(BaseModel):
    """
    Schema para datos contenidos en el token JWT.

    Usado internamente para decodificar y validar tokens.
    """
    email: Optional[str] = None
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    """
    Schema para request de login.

    Usado por el endpoint POST /auth/login.
    """
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=1, description="Contrasena")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@iot-monitoring.com",
                "password": "securepassword123"
            }
        }
