"""
Schemas Pydantic para SensorReading (TABLA CRITICA).
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class SensorReadingBase(BaseModel):
    """Schema base para SensorReading (campos comunes)."""
    device_id: int = Field(..., description="ID del device que genero la lectura")
    data_payload: Dict[str, Any] = Field(..., description="Datos de la medicion en JSON")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de calidad 0.0-1.0")
    timestamp: Optional[datetime] = Field(None, description="Momento de la medicion (UTC)")

    @field_validator('quality_score')
    @classmethod
    def validate_quality_score(cls, v):
        """Valida que quality_score este entre 0 y 1."""
        if v is not None and (v < 0 or v > 1):
            raise ValueError('quality_score debe estar entre 0.0 y 1.0')
        return v


class SensorReadingCreate(BaseModel):
    """
    Schema para crear un SensorReading (usado por ESP32).

    Este es el formato que los devices ESP32 envian al endpoint POST /readings.
    """
    device_eui: str = Field(..., max_length=64, description="EUI del device (no el ID)")
    data_payload: Dict[str, Any] = Field(..., description="Datos de sensores en JSON")
    timestamp: Optional[datetime] = Field(None, description="Timestamp de la medicion")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "device_eui": "ESP32_LAB_001",
                "data_payload": {
                    "temp_c": 25.5,
                    "humidity_pct": 62.3,
                    "battery_mv": 3750,
                    "rssi_dbm": -65
                },
                "timestamp": "2025-10-16T18:30:00Z"
            }
        }
    )


class SensorReading(SensorReadingBase):
    """Schema para respuesta de SensorReading (incluye campos de DB)."""
    id: int
    processed: bool = False
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
