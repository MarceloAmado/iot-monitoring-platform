"""
Schemas Pydantic para Password Reset.
"""

from pydantic import BaseModel, Field, EmailStr


class ForgotPasswordRequest(BaseModel):
    """Schema para solicitar recuperación de contraseña."""
    email: EmailStr = Field(..., description="Email del usuario que olvidó su contraseña")


class ForgotPasswordResponse(BaseModel):
    """Schema de respuesta para forgot password."""
    message: str = Field(..., description="Mensaje de confirmación")
    email: EmailStr = Field(..., description="Email al que se envió el token")


class ResetPasswordRequest(BaseModel):
    """Schema para resetear contraseña con token."""
    token: str = Field(..., min_length=1, description="Token UUID recibido por email")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña (min 8 caracteres)")


class ResetPasswordResponse(BaseModel):
    """Schema de respuesta para reset password."""
    message: str = Field(..., description="Mensaje de confirmación")
    success: bool = Field(..., description="Indica si el reset fue exitoso")


class ChangePasswordRequest(BaseModel):
    """Schema para cambiar contraseña (usuario logueado)."""
    old_password: str = Field(..., min_length=1, description="Contraseña actual")
    new_password: str = Field(..., min_length=8, description="Nueva contraseña (min 8 caracteres)")


class ChangePasswordResponse(BaseModel):
    """Schema de respuesta para change password."""
    message: str = Field(..., description="Mensaje de confirmación")
