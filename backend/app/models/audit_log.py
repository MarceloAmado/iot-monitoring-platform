"""
Modelo SQLAlchemy para Audit Log
Propósito: Trazabilidad inmutable de acciones del sistema (compliance IEC 62443, FDA 21 CFR Part 11)
Fecha: 2025-10-29
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB, INET
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """
    Registro de auditoría inmutable para compliance normativo.

    Características:
    - Inmutable: No hay UPDATE ni DELETE (solo INSERT)
    - Trazabilidad completa: user, acción, timestamp, IP, cambios
    - JSONB para flexibilidad en cambios (before/after)
    - Índices optimizados para queries frecuentes

    Cumple con:
    - GxP ALCOA+ (Attributable, Legible, Contemporaneous, Original, Accurate)
    - FDA 21 CFR Part 11 (Electronic Records)
    - IEC 62443-4-2 (Security audit trails)
    """

    __tablename__ = "audit_log"

    # Primary Key
    id = Column(
        BigInteger,
        primary_key=True,
        index=True,
        comment="ID autoincremental (BIGINT para millones de registros)"
    )

    # Usuario que realizó la acción
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID del usuario (NULL si acción de sistema)"
    )

    user_role = Column(
        String(32),
        nullable=True,
        comment="Rol del usuario al momento de la acción (snapshot)"
    )

    # Device relacionado (si aplica)
    device_id = Column(
        Integer,
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID del device relacionado (NULL si no aplica)"
    )

    # Tipo de acción
    action_type = Column(
        String(64),
        nullable=False,
        index=True,
        comment="Tipo de acción realizada (ej: USER_LOGIN, DEVICE_CREATED, CONFIG_UPDATED)"
    )

    # Entidad afectada
    entity_type = Column(
        String(32),
        nullable=True,
        comment="Tipo de entidad afectada (ej: user, device, alert_rule)"
    )

    entity_id = Column(
        Integer,
        nullable=True,
        comment="ID de la entidad afectada"
    )

    # Cambios realizados (before/after en JSON)
    changes = Column(
        JSONB,
        nullable=True,
        comment="Cambios realizados: {'before': {...}, 'after': {...}}"
    )

    # Información de red
    ip_address = Column(
        INET,
        nullable=True,
        comment="Dirección IP de origen (IPv4 o IPv6)"
    )

    user_agent = Column(
        Text,
        nullable=True,
        comment="User-Agent del navegador o cliente"
    )

    # Timestamp (inmutable, generado por servidor)
    timestamp = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Timestamp UTC de la acción (generado por DB)"
    )

    # Metadata adicional (flexible para futuras extensiones)
    # NOTA: 'metadata' está reservado por SQLAlchemy, usamos 'extra_data'
    extra_data = Column(
        JSONB,
        nullable=True,
        comment="Metadata adicional: {'request_id': '...', 'severity': 'high', ...}"
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action_type}, user_id={self.user_id}, timestamp={self.timestamp})>"

    def to_dict(self):
        """Convierte el registro a diccionario para serialización."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "device_id": self.device_id,
            "action_type": self.action_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "changes": self.changes,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "extra_data": self.extra_data
        }


# ============================================================
# Tipos de Acciones (Action Types) - Enumeración de referencia
# ============================================================
# NO se usa ENUM de PostgreSQL para mantener flexibilidad
# Se documenta aquí para consistencia en el código

"""
CATEGORÍAS DE ACCIONES:

1. AUTENTICACIÓN Y SESIONES:
   - USER_LOGIN: Usuario inicia sesión
   - USER_LOGOUT: Usuario cierra sesión
   - USER_LOGIN_FAILED: Intento de login fallido
   - SESSION_EXPIRED: Sesión expirada automáticamente

2. GESTIÓN DE USUARIOS:
   - USER_CREATED: Nuevo usuario creado
   - USER_UPDATED: Usuario actualizado
   - USER_DELETED: Usuario eliminado
   - USER_ROLE_CHANGED: Rol de usuario modificado
   - USER_PASSWORD_CHANGED: Contraseña cambiada

3. GESTIÓN DE DEVICES:
   - DEVICE_CREATED: Nuevo device registrado
   - DEVICE_UPDATED: Device actualizado
   - DEVICE_DELETED: Device eliminado
   - DEVICE_API_KEY_REGENERATED: API Key regenerada
   - DEVICE_CONFIG_UPDATED: Configuración remota actualizada
   - DEVICE_WENT_OFFLINE: Device detectado como offline
   - DEVICE_CAME_ONLINE: Device volvió a estar online

4. DATOS DE TELEMETRÍA:
   - READING_RECEIVED: Lectura de sensor recibida
   - HEARTBEAT_RECEIVED: Heartbeat de device recibido

5. ALERTAS:
   - ALERT_RULE_CREATED: Nueva regla de alerta creada
   - ALERT_RULE_UPDATED: Regla de alerta modificada
   - ALERT_RULE_DELETED: Regla de alerta eliminada
   - ALERT_TRIGGERED: Alerta disparada
   - ALERT_ACKNOWLEDGED: Alerta reconocida por operador

6. CONFIGURACIÓN REMOTA:
   - CONFIG_TEMPLATE_CREATED: Template de config creado
   - CONFIG_TEMPLATE_UPDATED: Template modificado
   - CONFIG_PUSHED_TO_DEVICE: Config enviada a device

7. SISTEMA:
   - SYSTEM_STARTUP: Sistema iniciado
   - SYSTEM_SHUTDOWN: Sistema detenido
   - BACKUP_CREATED: Backup de BD creado
   - BACKUP_RESTORED: Backup restaurado

8. SEGURIDAD:
   - UNAUTHORIZED_ACCESS_ATTEMPT: Intento de acceso no autorizado
   - API_KEY_INVALID: API Key inválida recibida
   - RATE_LIMIT_EXCEEDED: Límite de requests excedido
"""
