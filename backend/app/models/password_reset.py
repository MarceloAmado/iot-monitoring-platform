"""
Modelo de PasswordResetToken.

Gestiona tokens de recuperación de contraseña con expiración.
"""

from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class PasswordResetToken(Base):
    """
    Modelo para tokens de recuperación de contraseña.

    Almacena tokens únicos con expiración de 10 minutos para resetear contraseñas.
    Los tokens son de un solo uso (campo 'used').
    """

    __tablename__ = "password_reset_tokens"

    # Columnas
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                    nullable=False, index=True,
                    comment="ID del usuario que solicita el reset")
    token = Column(String(255), nullable=False, unique=True, index=True,
                  comment="Token único UUID para validación")
    expires_at = Column(DateTime, nullable=False,
                       comment="Fecha de expiración del token (10 minutos desde creación)")
    used = Column(Boolean, nullable=False, default=False, index=True,
                 comment="Indica si el token ya fue utilizado")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow,
                       comment="Fecha de creación del token")

    # Relaciones
    user = relationship("User", backref="password_reset_tokens")

    # Índices
    __table_args__ = (
        Index("idx_password_reset_token", "token"),
        Index("idx_password_reset_user", "user_id"),
        Index("idx_password_reset_used", "used"),
    )

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, used={self.used})>"

    def __str__(self):
        return f"Token for User {self.user_id} - {'Used' if self.used else 'Active'}"

    @property
    def is_expired(self) -> bool:
        """
        Verifica si el token está expirado.

        Returns:
            True si el token está expirado, False si aún es válido
        """
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """
        Verifica si el token es válido (no usado y no expirado).

        Returns:
            True si es válido, False si no
        """
        return not self.used and not self.is_expired

    @classmethod
    def create_token_expiration(cls) -> datetime:
        """
        Crea una fecha de expiración 10 minutos en el futuro.

        Returns:
            datetime: Fecha/hora de expiración
        """
        return datetime.utcnow() + timedelta(minutes=10)
