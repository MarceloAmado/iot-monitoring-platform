"""
Schemas Pydantic del Sistema de Monitoreo IoT.

Este modulo exporta todos los schemas para requests y responses de la API.
"""

from app.schemas.location import (
    LocationGroupBase,
    LocationGroupCreate,
    LocationGroupUpdate,
    LocationGroup,
    LocationBase,
    LocationCreate,
    LocationUpdate,
    Location,
)

from app.schemas.asset import (
    AssetBase,
    AssetCreate,
    AssetUpdate,
    Asset,
)

from app.schemas.device import (
    DeviceBase,
    DeviceCreate,
    DeviceUpdate,
    Device,
    DeviceSchema,
    DeviceVariableSchema,
)

from app.schemas.sensor_reading import (
    SensorReadingBase,
    SensorReadingCreate,
    SensorReading,
)

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    User,
)

from app.schemas.alert import (
    AlertRuleBase,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRule,
    AlertHistoryBase,
    AlertHistoryCreate,
    AlertHistory,
)

from app.schemas.auth import (
    Token,
    TokenData,
    LoginRequest,
)

__all__ = [
    # Location schemas
    "LocationGroupBase",
    "LocationGroupCreate",
    "LocationGroupUpdate",
    "LocationGroup",
    "LocationBase",
    "LocationCreate",
    "LocationUpdate",
    "Location",
    # Asset schemas
    "AssetBase",
    "AssetCreate",
    "AssetUpdate",
    "Asset",
    # Device schemas
    "DeviceBase",
    "DeviceCreate",
    "DeviceUpdate",
    "Device",
    "DeviceSchema",
    "DeviceVariableSchema",
    # SensorReading schemas
    "SensorReadingBase",
    "SensorReadingCreate",
    "SensorReading",
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "User",
    # Alert schemas
    "AlertRuleBase",
    "AlertRuleCreate",
    "AlertRuleUpdate",
    "AlertRule",
    "AlertHistoryBase",
    "AlertHistoryCreate",
    "AlertHistory",
    # Auth schemas
    "Token",
    "TokenData",
    "LoginRequest",
]
