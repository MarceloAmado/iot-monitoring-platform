"""
Schemas Pydantic para Firmware.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class FirmwareBase(BaseModel):
    """Schema base para Firmware (campos comunes)."""
    version: str = Field(..., max_length=20, description="Versión semver (ej: 1.2.3)")
    release_notes: Optional[str] = Field(None, description="Notas de la release")
    is_stable: bool = Field(True, description="True si es estable, False si es beta/rc")
    min_compatible_version: Optional[str] = Field(None, max_length=20, description="Versión mínima compatible")


class FirmwareCreate(BaseModel):
    """
    Schema para crear un Firmware (usado al subir archivo).

    El archivo binario se sube por separado usando multipart/form-data.
    """
    version: str = Field(..., max_length=20, description="Versión semver (ej: 1.2.3)")
    release_notes: Optional[str] = Field(None, description="Notas de la release")
    is_stable: bool = Field(True, description="True si es estable, False si es beta/rc")
    min_compatible_version: Optional[str] = Field(None, max_length=20, description="Versión mínima compatible")


class FirmwareUpdate(BaseModel):
    """Schema para actualizar un Firmware (solo metadata, no el binario)."""
    release_notes: Optional[str] = None
    is_stable: Optional[bool] = None
    is_latest: Optional[bool] = None
    min_compatible_version: Optional[str] = Field(None, max_length=20)


class Firmware(FirmwareBase):
    """Schema para respuesta de Firmware (incluye campos de DB)."""
    id: int
    file_path: str
    file_size_bytes: int
    file_size_mb: float
    md5_checksum: str
    is_latest: bool
    created_at: datetime
    created_by_user_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class FirmwareLatestResponse(BaseModel):
    """
    Schema para respuesta de check de versión más reciente.

    Usado por ESP32 para verificar si hay updates disponibles.
    """
    latest_version: str = Field(..., description="Versión más reciente disponible")
    current_version: str = Field(..., description="Versión actual del device")
    update_available: bool = Field(..., description="True si hay update disponible")
    download_url: Optional[str] = Field(None, description="URL para descargar el binario")
    file_size_bytes: Optional[int] = Field(None, description="Tamaño del archivo en bytes")
    md5_checksum: Optional[str] = Field(None, description="MD5 checksum del binario")
    release_notes: Optional[str] = Field(None, description="Notas de la release")
    is_compatible: bool = Field(True, description="True si la actualización es compatible")
    message: str = Field(..., description="Mensaje informativo")
