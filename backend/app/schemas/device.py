"""
Schemas Pydantic para Device.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class DeviceBase(BaseModel):
    """Schema base para Device (campos comunes)."""
    asset_id: Optional[int] = Field(None, description="ID del asset al que esta asignado")
    device_eui: str = Field(..., max_length=64, description="ID unico del device")
    name: str = Field(..., max_length=128, description="Nombre amigable del device")
    status: str = Field(default="active", max_length=32, description="Estado: active, inactive, maintenance, error")
    firmware_version: Optional[str] = Field(None, max_length=20, description="Version del firmware")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuracion del device")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Metadata adicional")


class DeviceCreate(DeviceBase):
    """Schema para crear un Device."""
    api_key: Optional[str] = Field(None, max_length=255, description="API Key del device (será encriptada automáticamente)")


class DeviceUpdate(BaseModel):
    """Schema para actualizar un Device (todos los campos opcionales)."""
    asset_id: Optional[int] = None
    device_eui: Optional[str] = Field(None, max_length=64)
    name: Optional[str] = Field(None, max_length=128)
    status: Optional[str] = Field(None, max_length=32)
    firmware_version: Optional[str] = Field(None, max_length=20)
    config: Optional[Dict[str, Any]] = None
    extra_data: Optional[Dict[str, Any]] = None


class Device(DeviceBase):
    """Schema para respuesta de Device (incluye campos de DB)."""
    id: int
    last_seen_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DeviceCreateResponse(Device):
    """
    Schema para respuesta al crear un Device.

    Incluye la API key en plaintext (SOLO al crear).
    Esta es la única vez que se mostrará la API key al usuario.
    """
    api_key: Optional[str] = Field(None, description="API Key en texto plano (solo al crear)")


# ============================================
# Schema Discovery Schemas (para auto-generar graficos)
# ============================================

class DeviceVariableSchema(BaseModel):
    """
    Schema para una variable de sensor.

    Describe una variable individual que el device mide
    (temperatura, humedad, presion, etc.)
    """
    key: str = Field(..., description="Key en el JSONB: temp_c, humidity_pct, etc.")
    label: str = Field(..., description="Etiqueta amigable: Temperatura, Humedad, etc.")
    unit: str = Field(..., description="Unidad de medida: C, %, bar, etc.")
    type: str = Field(..., description="Tipo de dato: float, int, string")
    color: Optional[str] = Field(None, description="Color para graficos en hex: #ff6b6b")


class DeviceSchema(BaseModel):
    """
    Schema de variables que un device envia.

    Permite al frontend auto-generar graficos sin conocer
    de antemano que variables envia cada device.
    """
    device_id: int
    variables: List[DeviceVariableSchema]

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Heartbeat Schema (para devices sin sensores)
# ============================================

class DeviceHeartbeat(BaseModel):
    """
    Schema para heartbeat de dispositivos.

    Permite a los ESP32 reportar que están vivos aunque no tengan
    sensores conectados. Actualiza last_seen_at y metadata.

    Ejemplo de uso:
    {
        "device_eui": "ESP32_LAB_001",
        "firmware_version": "1.2.0",
        "metadata": {
            "rssi_dbm": -65,
            "free_heap_bytes": 245000,
            "uptime_sec": 3600,
            "wifi_ssid": "MiWiFi_5G"
        }
    }
    """
    device_eui: str = Field(..., max_length=64, description="ID único del device (EUI)")
    firmware_version: Optional[str] = Field(None, max_length=20, description="Versión del firmware actual")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadata del sistema (RSSI, heap, uptime, etc.)"
    )


class DeviceHeartbeatResponse(BaseModel):
    """
    Respuesta del endpoint de heartbeat.

    Confirma que el heartbeat fue recibido y procesado.
    """
    device_id: int = Field(..., description="ID del device en la base de datos")
    device_eui: str = Field(..., description="EUI del device")
    last_seen_at: datetime = Field(..., description="Timestamp del último heartbeat")
    is_online: bool = Field(..., description="Estado online del device")
    message: str = Field(default="Heartbeat recibido correctamente", description="Mensaje de confirmación")


# ============================================
# Health Dashboard Schema
# ============================================

class DeviceHealthMetrics(BaseModel):
    """
    Métricas de salud individuales de un device.

    Incluye uptime, conectividad, recursos de sistema, y estado general.
    """
    device_id: int = Field(..., description="ID del device")
    device_eui: str = Field(..., description="EUI del device")
    name: str = Field(..., description="Nombre amigable del device")
    status: str = Field(..., description="Estado: active, inactive, maintenance, error")
    is_online: bool = Field(..., description="True si reportó en últimos 10 minutos")

    # Timestamps
    last_seen_at: Optional[datetime] = Field(None, description="Última comunicación exitosa")
    created_at: datetime = Field(..., description="Fecha de creación del device")
    uptime_hours: Optional[float] = Field(None, description="Horas desde último reinicio")

    # Conectividad
    rssi_dbm: Optional[int] = Field(None, description="Fuerza de señal WiFi en dBm (-90 a -30)")
    wifi_quality: Optional[str] = Field(None, description="Calidad WiFi: Excellent, Good, Fair, Poor")

    # Recursos del sistema
    free_heap_bytes: Optional[int] = Field(None, description="Memoria libre en bytes")
    battery_mv: Optional[int] = Field(None, description="Voltaje de batería en mV")
    battery_percentage: Optional[int] = Field(None, description="Porcentaje de batería estimado")

    # Firmware
    firmware_version: Optional[str] = Field(None, description="Versión del firmware actual")

    # Estadísticas de datos
    total_readings: int = Field(default=0, description="Total de readings enviados")
    readings_last_24h: int = Field(default=0, description="Readings en últimas 24 horas")
    avg_readings_per_day: float = Field(default=0.0, description="Promedio de readings por día")

    # Alertas relacionadas
    active_alerts_count: int = Field(default=0, description="Cantidad de alertas activas")

    # Location info
    location_name: Optional[str] = Field(None, description="Nombre de la location")
    asset_name: Optional[str] = Field(None, description="Nombre del asset asignado")

    model_config = ConfigDict(from_attributes=True)


class DeviceHealthDashboard(BaseModel):
    """
    Dashboard completo de salud de todos los devices.

    Incluye métricas individuales de cada device y estadísticas generales.
    """
    total_devices: int = Field(..., description="Total de devices registrados")
    devices_online: int = Field(..., description="Devices online (reportaron en últimos 10 min)")
    devices_offline: int = Field(..., description="Devices offline")
    devices_with_alerts: int = Field(..., description="Devices con alertas activas")

    # Métricas de calidad de conexión
    avg_rssi: Optional[float] = Field(None, description="RSSI promedio de devices online")
    devices_poor_signal: int = Field(default=0, description="Devices con señal débil (<-80 dBm)")

    # Lista de devices con sus métricas
    devices: List[DeviceHealthMetrics] = Field(default_factory=list, description="Métricas de cada device")

    model_config = ConfigDict(from_attributes=True)
