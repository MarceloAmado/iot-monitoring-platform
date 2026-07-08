"""
Schemas Pydantic para Asset.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AssetBase(BaseModel):
    """Schema base para Asset (campos comunes)."""
    location_id: int = Field(..., description="ID de la ubicacion donde esta el asset")
    name: str = Field(..., max_length=128, description="Nombre del asset")
    type: str = Field(..., max_length=64, description="Tipo: refrigerator, compressor, room, etc.")
    description: Optional[str] = Field(None, description="Descripcion detallada")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Metadata adicional en JSON")


class AssetCreate(AssetBase):
    """Schema para crear un Asset."""
    pass


class AssetUpdate(BaseModel):
    """Schema para actualizar un Asset (todos los campos opcionales)."""
    location_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=128)
    type: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class Asset(AssetBase):
    """Schema para respuesta de Asset (incluye campos de DB)."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
