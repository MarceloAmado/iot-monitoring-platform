"""
Modelo de Devices (Hardware ESP32 físico).

Device representa el hardware IoT (ESP32) que realiza las mediciones.
Puede moverse entre assets y mantiene su propia configuración y estado.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, CheckConstraint, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Device(Base):
    """
    Modelo para hardware ESP32 físico.

    Representa el dispositivo IoT (ESP32) que captura datos de sensores.
    Puede ser reasignado a diferentes assets manteniendo historial.

    Ejemplos: "ESP32_LAB_001", "ESP32_SALA_A", "ESP32_TEMP_05"
    """

    __tablename__ = "devices"

    # Columnas
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    asset_id = Column(Integer, ForeignKey("assets.id", ondelete="SET NULL"),
                     nullable=True, index=True,
                     comment="ID del asset al que está asignado actualmente (NULL si no asignado)")
    device_eui = Column(String(64), nullable=False, unique=True, index=True,
                       comment="ID único del device (MAC address o custom)")
    name = Column(String(128), nullable=False,
                  comment="Nombre amigable del device")
    status = Column(String(32), nullable=False, default="active", index=True,
                   comment="Estado: active, inactive, maintenance, error")
    firmware_version = Column(String(20), nullable=True,
                             comment="Versión del firmware (para OTA updates)")
    last_seen_at = Column(DateTime, nullable=True, index=True,
                         comment="Última comunicación exitosa con el backend")
    config = Column(JSONB, nullable=True,
                   comment="Configuración del device (sampling_interval_sec, wifi_ssid, etc.)")
    extra_data = Column(JSONB, nullable=True,
                       comment="Metadata adicional (mac_address, rssi_dbm, battery_mv, etc.)")
    api_key = Column(String(255), nullable=True, index=True,
                    comment="API Key en texto plano (DEPRECATED - usar api_key_encrypted)")
    api_key_encrypted = Column(Text, nullable=True,
                               comment="API Key encriptada con Fernet (AES-128 CBC + HMAC SHA256)")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                       comment="Fecha de creación del registro")

    # Relaciones
    asset = relationship("Asset", back_populates="devices")
    sensor_readings = relationship("SensorReading", back_populates="device",
                                  cascade="all, delete-orphan",
                                  lazy="selectin")
    alert_rules = relationship("AlertRule", back_populates="device",
                              cascade="all, delete-orphan",
                              lazy="selectin")
    alert_history = relationship("AlertHistory", back_populates="device",
                                cascade="all, delete-orphan",
                                lazy="selectin")

    # Índices y constraints
    __table_args__ = (
        Index("idx_devices_eui", "device_eui"),
        Index("idx_devices_asset", "asset_id"),
        Index("idx_devices_last_seen", "last_seen_at"),
        CheckConstraint(
            "status IN ('active', 'inactive', 'maintenance', 'error')",
            name="check_device_status"
        ),
    )

    def __repr__(self):
        return f"<Device(id={self.id}, eui='{self.device_eui}', status='{self.status}')>"

    def __str__(self):
        return f"{self.name} ({self.device_eui})"

    @property
    def is_online(self) -> bool:
        """
        Determina si el device está online basándose en last_seen_at.

        Retorna True si la última comunicación fue hace menos de 10 minutos.
        """
        if not self.last_seen_at:
            return False

        from datetime import timedelta
        threshold = datetime.utcnow() - timedelta(minutes=10)
        return self.last_seen_at > threshold
