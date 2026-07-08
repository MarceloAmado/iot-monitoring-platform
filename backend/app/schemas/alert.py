"""
Schemas Pydantic para AlertRule y AlertHistory.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================
# AlertRule Schemas
# ============================================

class AlertRuleBase(BaseModel):
    """Schema base para AlertRule (campos comunes)."""
    location_id: Optional[int] = Field(None, description="ID de location (NULL = global)")
    device_id: Optional[int] = Field(None, description="ID de device (NULL = todos)")
    name: str = Field(..., max_length=128, description="Nombre descriptivo")
    check_type: str = Field(..., max_length=32, description="THRESHOLD_ABOVE, THRESHOLD_BELOW, etc.")
    variable_key: str = Field(..., max_length=64, description="Key del JSONB: temp_c, humidity_pct")
    threshold_value: Optional[float] = Field(None, description="Valor umbral")
    threshold_min: Optional[float] = Field(None, description="Valor minimo para RANGE")
    threshold_max: Optional[float] = Field(None, description="Valor maximo para RANGE")
    time_window_minutes: Optional[int] = Field(None, description="Ventana de tiempo en minutos")
    enabled: bool = Field(default=True, description="Regla activa")
    cooldown_minutes: int = Field(default=30, description="Tiempo minimo entre alertas")
    notification_channels: List[str] = Field(..., description='Canales: ["email", "telegram", "webhook"]')
    webhook_url: Optional[str] = Field(None, description="URL para webhook")


class AlertRuleCreate(AlertRuleBase):
    """Schema para crear una AlertRule."""
    pass


class AlertRuleUpdate(BaseModel):
    """Schema para actualizar una AlertRule (todos los campos opcionales)."""
    location_id: Optional[int] = None
    device_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=128)
    check_type: Optional[str] = Field(None, max_length=32)
    variable_key: Optional[str] = Field(None, max_length=64)
    threshold_value: Optional[float] = None
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    time_window_minutes: Optional[int] = None
    enabled: Optional[bool] = None
    cooldown_minutes: Optional[int] = None
    notification_channels: Optional[List[str]] = None
    webhook_url: Optional[str] = None


class AlertRule(AlertRuleBase):
    """Schema para respuesta de AlertRule (incluye campos de DB)."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# AlertHistory Schemas
# ============================================

class AlertHistoryBase(BaseModel):
    """Schema base para AlertHistory (campos comunes)."""
    alert_rule_id: int = Field(..., description="ID de la regla que disparo")
    device_id: int = Field(..., description="ID del device que causo la alerta")
    sensor_reading_id: Optional[int] = Field(None, description="ID del reading (NULL si DEVICE_OFFLINE)")
    value_observed: Optional[float] = Field(None, description="Valor que causo la alerta")
    message: str = Field(..., description="Mensaje descriptivo")
    notification_sent: Optional[Dict[str, str]] = Field(None, description='Resultado: {"email": "success"}')


class AlertHistoryCreate(AlertHistoryBase):
    """Schema para crear un AlertHistory."""
    pass


class AlertHistory(AlertHistoryBase):
    """Schema para respuesta de AlertHistory (incluye campos de DB)."""
    id: int
    triggered_at: datetime
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
