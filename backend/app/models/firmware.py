"""
Modelo de Firmware (Versiones de firmware para ESP32).

Permite gestionar versiones de firmware, con versionado semántico
y almacenamiento de binarios en disco.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index
from app.core.database import Base


class Firmware(Base):
    """
    Modelo para versiones de firmware ESP32.

    Gestiona versiones de firmware con versionado semántico (semver).
    Los binarios se almacenan en disco (no en BD por tamaño).

    Ejemplos: "1.0.0", "1.2.3-beta", "2.0.0-rc1"
    """

    __tablename__ = "firmware_versions"

    # Columnas
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    version = Column(String(20), nullable=False, unique=True, index=True,
                    comment="Versión semver (ej: 1.2.3, 2.0.0-beta)")
    file_path = Column(String(512), nullable=False,
                      comment="Path relativo del binario (ej: firmware/esp32_v1.2.3.bin)")
    file_size_bytes = Column(Integer, nullable=False,
                            comment="Tamaño del archivo en bytes")
    md5_checksum = Column(String(32), nullable=False,
                         comment="MD5 checksum para verificar integridad")
    release_notes = Column(Text, nullable=True,
                          comment="Notas de la release (changelog)")
    is_stable = Column(Boolean, nullable=False, default=True,
                      comment="True si es estable, False si es beta/rc")
    is_latest = Column(Boolean, nullable=False, default=False,
                      comment="True si es la versión más reciente")
    min_compatible_version = Column(String(20), nullable=True,
                                   comment="Versión mínima desde la cual se puede actualizar")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                       comment="Fecha de creación del registro")
    created_by_user_id = Column(Integer, nullable=True,
                                comment="ID del usuario que subió el firmware")

    # Índices
    __table_args__ = (
        Index("idx_firmware_version", "version"),
        Index("idx_firmware_is_latest", "is_latest"),
        Index("idx_firmware_created", "created_at"),
    )

    def __repr__(self):
        return f"<Firmware(version='{self.version}', stable={self.is_stable}, latest={self.is_latest})>"

    def __str__(self):
        return f"Firmware v{self.version} ({'stable' if self.is_stable else 'beta'})"

    @property
    def file_size_mb(self) -> float:
        """
        Retorna el tamaño del archivo en MB.
        """
        return round(self.file_size_bytes / (1024 * 1024), 2)
