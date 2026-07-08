"""
Modelos SQLAlchemy del Sistema de Monitoreo IoT.

Este modulo exporta todos los modelos ORM para facilitar su importacion.

Jerarquia de modelos:
    LocationGroup (1:N) Location (1:N) Asset (1:N) Device (1:N) SensorReading
    User (para autenticacion y permisos)
    AlertRule + AlertHistory (sistema de alertas)
"""

from app.models.location import LocationGroup, Location
from app.models.asset import Asset
from app.models.device import Device
from app.models.sensor_reading import SensorReading
from app.models.user import User
from app.models.alert import AlertRule, AlertHistory
from app.models.password_reset import PasswordResetToken

__all__ = [
    "LocationGroup",
    "Location",
    "Asset",
    "Device",
    "SensorReading",
    "User",
    "AlertRule",
    "AlertHistory",
    "PasswordResetToken",
]
