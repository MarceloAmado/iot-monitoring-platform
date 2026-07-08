"""
Modelos de Ubicaciones: LocationGroup y Location.

LocationGroup: Nivel más alto de jerarquía (Hospital, Empresa, Cliente)
Location: Áreas/Zonas dentro de un LocationGroup (Laboratorio, Sala, etc.)
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class LocationGroup(Base):
    """
    Modelo para grupos de ubicaciones (nivel más alto de jerarquía).

    Representa organizaciones, clientes, hospitales, empresas, etc.
    Ejemplo: "Hospital Rawson", "Acme Industries", "Planta Mendoza"
    """

    __tablename__ = "location_groups"

    # Columnas
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True, index=True,
                  comment="Nombre único del grupo de ubicación")
    description = Column(Text, nullable=True,
                        comment="Descripción opcional del grupo")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                       comment="Fecha de creación del registro")

    # Relaciones
    locations = relationship("Location", back_populates="location_group",
                            cascade="all, delete-orphan",
                            lazy="selectin")

    def __repr__(self):
        return f"<LocationGroup(id={self.id}, name='{self.name}')>"

    def __str__(self):
        return self.name


class Location(Base):
    """
    Modelo para ubicaciones específicas dentro de un LocationGroup.

    Representa áreas, zonas, sectores dentro de una organización.
    Ejemplo: "Laboratorio - Química", "Sala de Urgencias", "Almacén Principal"
    """

    __tablename__ = "locations"

    # Columnas
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    location_group_id = Column(Integer, ForeignKey("location_groups.id", ondelete="CASCADE"),
                               nullable=False, index=True,
                               comment="ID del grupo al que pertenece")
    name = Column(String(128), nullable=False,
                  comment="Nombre de la ubicación")
    code = Column(String(32), unique=True, nullable=True, index=True,
                  comment="Código corto único (ej: LAB-QUI, SALA-URG)")
    timezone = Column(String(50), nullable=False, default='UTC',
                     comment="Zona horaria de la ubicación (ej: America/Argentina/Buenos_Aires)")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                       comment="Fecha de creación del registro")

    # Relaciones
    location_group = relationship("LocationGroup", back_populates="locations")
    assets = relationship("Asset", back_populates="location",
                         cascade="all, delete-orphan",
                         lazy="selectin")
    alert_rules = relationship("AlertRule", back_populates="location",
                              cascade="all, delete-orphan",
                              lazy="selectin")

    # Índices compuestos
    __table_args__ = (
        Index("idx_locations_group", "location_group_id"),
    )

    def __repr__(self):
        return f"<Location(id={self.id}, name='{self.name}', code='{self.code}')>"

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name
