"""
Schemas Pydantic para LocationGroup y Location.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================
# LocationGroup Schemas
# ============================================

class LocationGroupBase(BaseModel):
    """Schema base para LocationGroup (campos comunes)."""
    name: str = Field(..., max_length=128, description="Nombre del grupo de ubicacion")
    description: Optional[str] = Field(None, description="Descripcion opcional")


class LocationGroupCreate(LocationGroupBase):
    """Schema para crear un LocationGroup."""
    pass


class LocationGroupUpdate(BaseModel):
    """Schema para actualizar un LocationGroup (todos los campos opcionales)."""
    name: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = None


class LocationGroup(LocationGroupBase):
    """Schema para respuesta de LocationGroup (incluye campos de DB)."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Location Schemas
# ============================================

class LocationBase(BaseModel):
    """Schema base para Location (campos comunes)."""
    location_group_id: int = Field(..., description="ID del grupo al que pertenece")
    name: str = Field(..., max_length=128, description="Nombre de la ubicacion")
    code: Optional[str] = Field(None, max_length=32, description="Codigo corto unico")
    timezone: str = Field(default='UTC', max_length=50, description="Zona horaria (ej: America/Argentina/Buenos_Aires)")


class LocationCreate(LocationBase):
    """Schema para crear una Location."""
    pass


class LocationUpdate(BaseModel):
    """Schema para actualizar una Location (todos los campos opcionales)."""
    location_group_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=128)
    code: Optional[str] = Field(None, max_length=32)
    timezone: Optional[str] = Field(None, max_length=50)


class Location(LocationBase):
    """Schema para respuesta de Location (incluye campos de DB)."""
    id: int
    timezone: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
