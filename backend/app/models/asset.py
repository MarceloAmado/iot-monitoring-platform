"""
Modelo de Assets (Equipos físicos monitoreados).

Asset representa equipos, máquinas o lugares físicos que son monitoreados
por devices IoT. Separado de Device para permitir trazabilidad cuando
se mueven sensores entre equipos.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Asset(Base):
    """
    Modelo para equipos/cosas físicas monitoreadas.

    Representa el objeto físico que está siendo monitoreado (heladera, compresor,
    sala, etc.), separado del device (ESP32) que lo monitorea para mantener
    trazabilidad cuando se mueven sensores entre equipos.

    Ejemplos: "Heladera_Química_001", "Compresor_Aire_A", "Sala_Limpia_01"
    """

    __tablename__ = "assets"

    # Columnas
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"),
                        nullable=False, index=True,
                        comment="ID de la ubicación donde está el asset")
    name = Column(String(128), nullable=False,
                  comment="Nombre del asset (ej: Heladera_Química_001)")
    type = Column(String(64), nullable=False, index=True,
                  comment="Tipo de asset: refrigerator, compressor, room, etc.")
    description = Column(Text, nullable=True,
                        comment="Descripción detallada del asset")
    extra_data = Column(JSONB, nullable=True,
                       comment="Metadata adicional en formato JSON (capacidad, marca, modelo, etc.)")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                       comment="Fecha de creación del registro")

    # Relaciones
    location = relationship("Location", back_populates="assets")
    devices = relationship("Device", back_populates="asset",
                          cascade="all, delete-orphan",
                          lazy="selectin")

    # Índices compuestos
    __table_args__ = (
        Index("idx_assets_location", "location_id"),
        Index("idx_assets_type", "type"),
    )

    def __repr__(self):
        return f"<Asset(id={self.id}, name='{self.name}', type='{self.type}')>"

    def __str__(self):
        return f"{self.name} ({self.type})"
