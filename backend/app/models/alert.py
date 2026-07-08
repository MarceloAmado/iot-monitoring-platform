"""
Modelos de Alertas: AlertRule y AlertHistory.

AlertRule: Configuración dinámica de reglas de alertas
AlertHistory: Log histórico de alertas disparadas
"""

from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Text, Float, Boolean, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class AlertRule(Base):
    """
    Modelo para reglas de alertas configurables.

    Define las condiciones bajo las cuales se debe disparar una alerta.
    Soporta múltiples tipos de chequeos: umbrales, rangos, tasa de cambio,
    device offline, sensor fault, etc.

    Ejemplos:
    - Alerta si temperatura > 25°C
    - Alerta si humedad NO está entre 40% y 60%
    - Alerta si temperatura cambia más de 5°C en 10 minutos
    - Alerta si device no reporta en 5 minutos
    """

    __tablename__ = "alert_rules"

    # Columnas
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"),
                        nullable=True, index=True,
                        comment="ID de location específica (NULL = regla global)")
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"),
                      nullable=True, index=True,
                      comment="ID de device específico (NULL = aplica a todos los devices de la location)")
    name = Column(String(128), nullable=False,
                  comment="Nombre descriptivo de la regla")
    check_type = Column(String(32), nullable=False, index=True,
                       comment="Tipo de chequeo: THRESHOLD_ABOVE, THRESHOLD_BELOW, THRESHOLD_RANGE, etc.")
    variable_key = Column(String(64), nullable=True,
                         comment="Key del JSONB a evaluar (ej: temp_c, humidity_pct). NULL para DEVICE_OFFLINE")
    threshold_value = Column(Float, nullable=True,
                            comment="Valor umbral para THRESHOLD_ABOVE/BELOW")
    threshold_min = Column(Float, nullable=True,
                          comment="Valor mínimo para THRESHOLD_RANGE")
    threshold_max = Column(Float, nullable=True,
                          comment="Valor máximo para THRESHOLD_RANGE")
    time_window_minutes = Column(Integer, nullable=True,
                                 comment="Ventana de tiempo para RATE_OF_CHANGE y DEVICE_OFFLINE")
    enabled = Column(Boolean, nullable=False, default=True, index=True,
                    comment="Permite desactivar reglas sin eliminarlas")
    cooldown_minutes = Column(Integer, nullable=False, default=30,
                             comment="Tiempo mínimo entre alertas consecutivas (evita spam)")
    notification_channels = Column(JSONB, nullable=False,
                                   comment='Canales de notificación: ["email", "telegram", "webhook"]')
    webhook_url = Column(Text, nullable=True,
                        comment="URL para POST si webhook está en notification_channels")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                       comment="Fecha de creación de la regla")

    # Relaciones
    location = relationship("Location", back_populates="alert_rules")
    device = relationship("Device", back_populates="alert_rules")
    alert_history = relationship("AlertHistory", back_populates="alert_rule",
                                cascade="all, delete-orphan",
                                lazy="selectin")

    # Índices y constraints
    __table_args__ = (
        Index("idx_alert_rules_location", "location_id"),
        Index("idx_alert_rules_device", "device_id"),
        Index("idx_alert_rules_enabled", "enabled"),
        CheckConstraint(
            """check_type IN (
                'THRESHOLD_ABOVE',
                'THRESHOLD_BELOW',
                'THRESHOLD_RANGE',
                'RATE_OF_CHANGE',
                'DEVICE_OFFLINE',
                'SENSOR_FAULT',
                'ANOMALY_ML'
            )""",
            name="check_alert_rule_type"
        ),
    )

    def __repr__(self):
        return f"<AlertRule(id={self.id}, name='{self.name}', type='{self.check_type}')>"

    def __str__(self):
        status = "enabled" if self.enabled else "disabled"
        return f"{self.name} ({self.check_type}) - {status}"


class AlertHistory(Base):
    """
    Modelo para historial de alertas disparadas.

    Registra cada vez que una regla de alerta se dispara, incluyendo
    el valor observado, mensaje generado, resultado de notificaciones,
    y quién/cuándo reconoció la alerta.

    Útil para auditoría, debugging y análisis de tendencias.
    """

    __tablename__ = "alert_history"

    # Columnas
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True,
                comment="ID autoincremental (BIGINT para muchos registros)")
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id", ondelete="CASCADE"),
                          nullable=False, index=True,
                          comment="ID de la regla que disparó la alerta")
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"),
                      nullable=False, index=True,
                      comment="ID del device que causó la alerta")
    sensor_reading_id = Column(BigInteger, ForeignKey("sensor_readings.id", ondelete="SET NULL"),
                              nullable=True, index=True,
                              comment="ID del reading que disparó (NULL si DEVICE_OFFLINE)")
    triggered_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True,
                         comment="Momento en que se disparó la alerta")
    value_observed = Column(Float, nullable=True,
                           comment="Valor que causó la alerta (si aplica)")
    message = Column(Text, nullable=False,
                    comment="Mensaje generado describiendo la alerta")
    notification_sent = Column(JSONB, nullable=True,
                              comment='Resultado de notificaciones: {"email": "success", "telegram": "failed"}')
    acknowledged_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"),
                            nullable=True, index=True,
                            comment="ID del usuario que reconoció/vio la alerta")
    acknowledged_at = Column(DateTime, nullable=True,
                            comment="Momento en que fue reconocida la alerta")

    # Relaciones
    alert_rule = relationship("AlertRule", back_populates="alert_history")
    device = relationship("Device", back_populates="alert_history")
    sensor_reading = relationship("SensorReading", back_populates="alert_history")
    acknowledged_by_user = relationship("User", back_populates="acknowledged_alerts",
                                       foreign_keys=[acknowledged_by])

    # Índices
    __table_args__ = (
        Index("idx_alert_history_rule", "alert_rule_id"),
        Index("idx_alert_history_device", "device_id"),
        Index("idx_alert_history_triggered", "triggered_at", postgresql_using="btree"),
        Index("idx_alert_history_ack_by", "acknowledged_by"),
    )

    def __repr__(self):
        return f"<AlertHistory(id={self.id}, rule_id={self.alert_rule_id}, triggered_at='{self.triggered_at}')>"

    def __str__(self):
        ack_status = "acknowledged" if self.acknowledged_by else "pending"
        return f"Alert #{self.id} - {self.message[:50]}... ({ack_status})"

    @property
    def is_acknowledged(self) -> bool:
        """Retorna True si la alerta fue reconocida."""
        return self.acknowledged_by is not None
