"""
Schemas Pydantic para SensorCatalog.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class SensorCatalogBase(BaseModel):
    """Schema base para SensorCatalog (campos comunes)."""
    name: str = Field(..., max_length=128, description="Nombre único del sensor")
    sensor_type: str = Field(
        ...,
        max_length=64,
        description="Tipo: temperature, humidity, pressure, analog, digital, custom"
    )
    description: Optional[str] = Field(None, description="Descripción del sensor")

    # Configuración de hardware
    gpio_pin: Optional[int] = Field(None, ge=0, le=39, description="Pin GPIO (0-39 para ESP32)")
    protocol: Optional[str] = Field(
        None,
        max_length=32,
        description="Protocolo: OneWire, I2C, SPI, ADC, Digital"
    )
    i2c_address: Optional[str] = Field(None, max_length=10, description="Dirección I2C (ej: 0x76)")

    # Calibración
    calibration_offset: float = Field(default=0.0, description="Offset de calibración")
    calibration_factor: float = Field(default=1.0, gt=0, description="Factor de calibración (>0)")
    value_min: Optional[float] = Field(None, description="Valor mínimo esperado")
    value_max: Optional[float] = Field(None, description="Valor máximo esperado")

    # Unidades y formato
    unit: Optional[str] = Field(None, max_length=32, description="Unidad: °C, %, kPa, V, mA")
    decimal_places: int = Field(default=2, ge=0, le=6, description="Decimales (0-6)")

    # Configuración avanzada
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Config JSON: {'adc_bits': 12, 'samples': 10}"
    )

    # Metadatos
    manufacturer: Optional[str] = Field(None, max_length=128, description="Fabricante")
    model: Optional[str] = Field(None, max_length=128, description="Modelo")
    datasheet_url: Optional[str] = Field(None, description="URL del datasheet")

    # Estado
    is_active: bool = Field(default=True, description="Sensor activo")


class SensorCatalogCreate(SensorCatalogBase):
    """
    Schema para crear un SensorCatalog.

    Todos los campos heredados de SensorCatalogBase.
    """
    pass


class SensorCatalogUpdate(BaseModel):
    """Schema para actualizar un SensorCatalog (todos los campos opcionales)."""
    name: Optional[str] = Field(None, max_length=128)
    sensor_type: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None

    gpio_pin: Optional[int] = Field(None, ge=0, le=39)
    protocol: Optional[str] = Field(None, max_length=32)
    i2c_address: Optional[str] = Field(None, max_length=10)

    calibration_offset: Optional[float] = None
    calibration_factor: Optional[float] = Field(None, gt=0)
    value_min: Optional[float] = None
    value_max: Optional[float] = None

    unit: Optional[str] = Field(None, max_length=32)
    decimal_places: Optional[int] = Field(None, ge=0, le=6)

    config: Optional[Dict[str, Any]] = None

    manufacturer: Optional[str] = Field(None, max_length=128)
    model: Optional[str] = Field(None, max_length=128)
    datasheet_url: Optional[str] = None

    is_active: Optional[bool] = None


class SensorCatalog(SensorCatalogBase):
    """
    Schema para respuesta de SensorCatalog (incluye campos de DB).
    """
    id: int
    is_builtin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SensorCatalogStats(BaseModel):
    """Schema para estadísticas del catálogo de sensores."""
    total: int = Field(..., description="Total de sensores")
    active: int = Field(..., description="Sensores activos")
    inactive: int = Field(..., description="Sensores inactivos")
    builtin: int = Field(..., description="Sensores built-in")
    custom: int = Field(..., description="Sensores personalizados")
    by_type: Dict[str, int] = Field(..., description="Cantidad por tipo de sensor")
    by_protocol: Dict[str, int] = Field(..., description="Cantidad por protocolo")
