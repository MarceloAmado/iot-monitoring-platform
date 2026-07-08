"""
Modelo de SensorReading (Mediciones de sensores).

TABLA CRÍTICA del sistema. Almacena todas las mediciones en formato JSONB
para máxima flexibilidad y escalabilidad.
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, Integer, String, Float, Boolean, DateTime, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class SensorReading(Base):
    """
    Modelo para mediciones de sensores (TABLA CRÍTICA).

    Almacena todas las lecturas de sensores en formato JSONB para permitir
    flexibilidad total: cualquier tipo de sensor puede agregar sus variables
    sin necesidad de modificar el esquema de base de datos.

    El campo data_payload contiene las mediciones reales:
    {"temp_c": 25.5, "humidity_pct": 60.2, "pressure_bar": 1.013, "battery_mv": 3750, ...}

    IMPORTANTE: Esta tabla crecerá a millones de registros. Los índices están
    optimizados para las queries más comunes (device_id + timestamp).
    """

    __tablename__ = "sensor_readings"

    # Columnas
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True,
                comment="ID autoincremental (BIGINT para millones de registros)")
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="SET NULL"),
                      nullable=True, index=True,
                      comment="ID del device que generó esta lectura (NULL si fue eliminado)")
    deleted_device_name = Column(String(255), nullable=True,
                                comment="Nombre del device eliminado (ej: 'Dispositivo Eliminado el 21/10/2025')")
    data_payload = Column(JSONB, nullable=False,
                         comment="Datos de la medición en formato JSON flexible")
    quality_score = Column(Float, nullable=True,
                          comment="Score de calidad de la lectura (0.0-1.0): 1.0=perfecto, 0.0=inválido")
    processed = Column(Boolean, nullable=False, default=False, index=True,
                      comment="Indica si ya fue procesado por el sistema de alertas")
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True,
                      comment="Momento de la medición (UTC)")

    # Relaciones
    device = relationship("Device", back_populates="sensor_readings")
    alert_history = relationship("AlertHistory", back_populates="sensor_reading",
                                cascade="all, delete-orphan",
                                lazy="selectin")

    # Índices y constraints
    __table_args__ = (
        # Índice compuesto para la query más común: filtrar por device y ordenar por timestamp
        Index("idx_readings_device_time", "device_id", "timestamp", postgresql_using="btree"),
        # Índice para encontrar readings no procesados por el job de alertas
        Index("idx_readings_processed", "processed"),
        # Índice GIN para búsquedas dentro del JSONB
        Index("idx_readings_payload", "data_payload", postgresql_using="gin"),
        # Constraint de calidad
        CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)",
            name="check_quality_score_range"
        ),
    )

    def __repr__(self):
        device_id_str = self.device_id if self.device_id else "N/A"
        timestamp_str = self.timestamp.isoformat() if self.timestamp else "N/A"
        return f"<SensorReading(id={self.id}, device_id={device_id_str}, timestamp='{timestamp_str}')>"

    def __str__(self):
        return f"Reading #{self.id} from Device {self.device_id} at {self.timestamp}"

    @property
    def is_valid(self) -> bool:
        """
        Determina si la lectura es válida basándose en el quality_score.

        Retorna True si quality_score es None (no evaluado) o >= 0.7
        """
        if self.quality_score is None:
            return True  # Asumimos válido si no fue evaluado
        return self.quality_score >= 0.7
