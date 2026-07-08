"""
Modelo de User (Usuarios del sistema).

Gestiona autenticación y control de acceso RBAC (Role-Based Access Control).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """
    Modelo para usuarios del sistema con RBAC.

    Gestiona autenticación (email + password_hash) y autorización mediante roles.
    El campo allowed_location_ids permite control granular de acceso por ubicación.

    Roles disponibles:
    - super_admin: Acceso total al sistema, ignora allowed_location_ids
    - service_admin: CRUD completo en sus locations asignadas
    - technician: Solo lectura en sus locations asignadas
    - guest: Solo dashboard público sin datos sensibles
    """

    __tablename__ = "users"

    # Columnas
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True, index=True,
                  comment="Email único del usuario (usado para login)")
    password_hash = Column(String(255), nullable=False,
                          comment="Hash bcrypt de la contraseña (NUNCA plaintext)")
    role = Column(String(32), nullable=False, index=True,
                  comment="Rol del usuario: super_admin, service_admin, technician, guest")
    allowed_location_ids = Column(ARRAY(Integer), nullable=True,
                                  comment="Array de IDs de locations que puede ver (NULL=todas si super_admin)")
    first_name = Column(String(64), nullable=False,
                       comment="Nombre del usuario")
    last_name = Column(String(64), nullable=False,
                      comment="Apellido del usuario")
    phone_number = Column(String(20), nullable=True,
                         comment="Número de teléfono para notificaciones Telegram")
    profile_picture_url = Column(String(512), nullable=True,
                                comment="URL de la foto de perfil del usuario")
    preferences = Column(JSONB, nullable=True,
                        comment="Preferencias de UI del usuario (notificaciones, tema, formato de fecha)")
    is_active = Column(Boolean, nullable=False, default=True, index=True,
                      comment="Permite desactivar usuarios sin eliminarlos")
    archived = Column(Boolean, nullable=False, default=False, index=True,
                     comment="Indica si el usuario está archivado (soft delete adicional)")
    archived_at = Column(DateTime, nullable=True,
                        comment="Fecha en que el usuario fue archivado")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                       comment="Fecha de creación del usuario")
    last_login_at = Column(DateTime, nullable=True,
                          comment="Fecha del último login exitoso")

    # Relaciones
    acknowledged_alerts = relationship("AlertHistory", back_populates="acknowledged_by_user",
                                      foreign_keys="AlertHistory.acknowledged_by",
                                      lazy="selectin")

    # Índices y constraints
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_role", "role"),
        Index("idx_users_active", "is_active"),
        CheckConstraint(
            "role IN ('super_admin', 'service_admin', 'technician', 'guest')",
            name="check_user_role"
        ),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def full_name(self) -> str:
        """Retorna el nombre completo del usuario."""
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self) -> bool:
        """Retorna True si el usuario es super_admin o service_admin."""
        return self.role in ("super_admin", "service_admin")

    @property
    def is_super_admin(self) -> bool:
        """Retorna True si el usuario es super_admin."""
        return self.role == "super_admin"

    def can_access_location(self, location_id: int) -> bool:
        """
        Verifica si el usuario tiene acceso a una location específica.

        Args:
            location_id: ID de la location a verificar

        Returns:
            True si tiene acceso, False si no
        """
        # Super admin tiene acceso a todo
        if self.is_super_admin:
            return True

        # Si no tiene allowed_location_ids configurado, no tiene acceso
        if not self.allowed_location_ids:
            return False

        # Verificar si la location está en la lista permitida
        return location_id in self.allowed_location_ids
