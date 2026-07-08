"""
Modelo SQLAlchemy para SensorCatalog.

Catálogo de sensores personalizados que pueden ser asignados a devices.
Permite configurar sensores custom con sus parámetros de calibración.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class SensorCatalog(Base):
    """
    Modelo de catálogo de sensores personalizados.

    Permite definir sensores custom con:
    - Tipo de sensor (temperature, humidity, pressure, analog, digital)
    - Pin GPIO de lectura
    - Parámetros de calibración (offset, factor, min, max)
    - Configuración JSON flexible para sensores especiales
    """
    __tablename__ = "sensor_catalog"

    # Campos base
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), nullable=False, unique=True, comment="Nombre único del sensor")
    sensor_type = Column(
        String(64),
        nullable=False,
        comment="Tipo: temperature, humidity, pressure, analog, digital, custom"
    )
    description = Column(Text, nullable=True, comment="Descripción del sensor")

    # Configuración de hardware
    gpio_pin = Column(Integer, nullable=True, comment="Pin GPIO para lectura ADC/Digital")
    protocol = Column(
        String(32),
        nullable=True,
        comment="Protocolo de comunicación: OneWire, I2C, SPI, ADC, Digital"
    )
    i2c_address = Column(String(10), nullable=True, comment="Dirección I2C si aplica (ej: 0x76)")

    # Calibración
    calibration_offset = Column(Float, default=0.0, comment="Offset de calibración")
    calibration_factor = Column(Float, default=1.0, comment="Factor multiplicador de calibración")
    value_min = Column(Float, nullable=True, comment="Valor mínimo esperado")
    value_max = Column(Float, nullable=True, comment="Valor máximo esperado")

    # Unidades y formato
    unit = Column(String(32), nullable=True, comment="Unidad de medida: °C, %, kPa, bar, V, mA")
    decimal_places = Column(Integer, default=2, comment="Decimales para mostrar")

    # Configuración avanzada (JSON flexible)
    config = Column(
        JSON,
        nullable=True,
        comment="Config JSON: {'adc_bits': 12, 'voltage_divider': 2, 'samples': 10}"
    )

    # Metadatos
    manufacturer = Column(String(128), nullable=True, comment="Fabricante del sensor")
    model = Column(String(128), nullable=True, comment="Modelo del sensor")
    datasheet_url = Column(Text, nullable=True, comment="URL del datasheet")

    # Estado
    is_active = Column(Boolean, default=True, comment="Sensor activo en el sistema")
    is_builtin = Column(
        Boolean,
        default=False,
        comment="Sensor built-in (DS18B20, DHT22, MPX5700) no se puede eliminar"
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SensorCatalog(id={self.id}, name='{self.name}', type='{self.sensor_type}')>"

    def to_dict(self):
        """Convierte el modelo a diccionario."""
        return {
            "id": self.id,
            "name": self.name,
            "sensor_type": self.sensor_type,
            "description": self.description,
            "gpio_pin": self.gpio_pin,
            "protocol": self.protocol,
            "i2c_address": self.i2c_address,
            "calibration_offset": self.calibration_offset,
            "calibration_factor": self.calibration_factor,
            "value_min": self.value_min,
            "value_max": self.value_max,
            "unit": self.unit,
            "decimal_places": self.decimal_places,
            "config": self.config,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "datasheet_url": self.datasheet_url,
            "is_active": self.is_active,
            "is_builtin": self.is_builtin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
