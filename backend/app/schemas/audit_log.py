"""
Schemas Pydantic para Audit Log
Propósito: Validación de requests/responses para audit log
Fecha: 2025-10-29
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


# ============================================================
# Schema Base
# ============================================================
class AuditLogBase(BaseModel):
    """Schema base para Audit Log (campos comunes)."""

    user_id: Optional[int] = Field(None, description="ID del usuario que realizó la acción")
    user_role: Optional[str] = Field(None, max_length=32, description="Rol del usuario")
    device_id: Optional[int] = Field(None, description="ID del device relacionado")
    action_type: str = Field(..., max_length=64, description="Tipo de acción (USER_LOGIN, DEVICE_CREATED, etc)")
    entity_type: Optional[str] = Field(None, max_length=32, description="Tipo de entidad afectada")
    entity_id: Optional[int] = Field(None, description="ID de la entidad afectada")
    changes: Optional[Dict[str, Any]] = Field(None, description="Cambios realizados: {'before': {...}, 'after': {...}}")
    ip_address: Optional[str] = Field(None, description="Dirección IP de origen")
    user_agent: Optional[str] = Field(None, description="User-Agent del navegador")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Metadata adicional")


# ============================================================
# Schema para Creación (POST)
# ============================================================
class AuditLogCreate(AuditLogBase):
    """
    Schema para crear un nuevo registro de auditoría.

    Uso interno del sistema - NO expuesto vía API pública.
    """
    pass


# ============================================================
# Schema para Respuesta (Response)
# ============================================================
class AuditLogResponse(AuditLogBase):
    """Schema de respuesta con todos los campos incluyendo ID y timestamp."""

    id: int = Field(..., description="ID único del registro de auditoría")
    timestamp: datetime = Field(..., description="Timestamp UTC de la acción")

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Schema para Listado Paginado
# ============================================================
class AuditLogList(BaseModel):
    """Schema para respuesta paginada de audit logs."""

    items: list[AuditLogResponse] = Field(..., description="Lista de registros de auditoría")
    total: int = Field(..., description="Total de registros que cumplen los filtros")
    page: int = Field(..., ge=1, description="Página actual")
    page_size: int = Field(..., ge=1, le=100, description="Tamaño de página")
    total_pages: int = Field(..., description="Total de páginas disponibles")

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Schema para Filtros de Búsqueda
# ============================================================
class AuditLogFilters(BaseModel):
    """Schema para filtros de búsqueda en audit logs."""

    user_id: Optional[int] = Field(None, description="Filtrar por ID de usuario")
    device_id: Optional[int] = Field(None, description="Filtrar por ID de device")
    action_type: Optional[str] = Field(None, description="Filtrar por tipo de acción")
    entity_type: Optional[str] = Field(None, description="Filtrar por tipo de entidad")
    entity_id: Optional[int] = Field(None, description="Filtrar por ID de entidad")
    date_from: Optional[datetime] = Field(None, description="Fecha desde (UTC)")
    date_to: Optional[datetime] = Field(None, description="Fecha hasta (UTC)")
    allowed_device_ids: Optional[List[int]] = Field(None, description="IDs de devices permitidos (RBAC)")
    page: int = Field(1, ge=1, description="Número de página")
    page_size: int = Field(50, ge=1, le=100, description="Tamaño de página (máx 100)")

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Schema para Resumen de Actividad
# ============================================================
class AuditLogSummary(BaseModel):
    """Schema para resumen estadístico de actividad."""

    action_type: str = Field(..., description="Tipo de acción")
    count: int = Field(..., description="Cantidad de ocurrencias")
    last_occurrence: Optional[datetime] = Field(None, description="Última ocurrencia")

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Schema para Actividad de Usuario
# ============================================================
class UserActivitySummary(BaseModel):
    """Schema para resumen de actividad por usuario."""

    user_id: int = Field(..., description="ID del usuario")
    user_email: Optional[str] = Field(None, description="Email del usuario")
    total_actions: int = Field(..., description="Total de acciones realizadas")
    last_activity: Optional[datetime] = Field(None, description="Última actividad")
    most_common_action: Optional[str] = Field(None, description="Acción más frecuente")

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Enumeración de Action Types (para documentación)
# ============================================================
class ActionTypeEnum:
    """
    Enumeración de tipos de acciones para audit log.

    Categorías:
    - Autenticación
    - Gestión de usuarios
    - Gestión de devices
    - Telemetría
    - Alertas
    - Configuración
    - Sistema
    - Seguridad
    """

    # Autenticación
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    SESSION_EXPIRED = "SESSION_EXPIRED"

    # Gestión de usuarios
    USER_CREATED = "USER_CREATED"
    USER_UPDATED = "USER_UPDATED"
    USER_DELETED = "USER_DELETED"
    USER_ROLE_CHANGED = "USER_ROLE_CHANGED"
    USER_PASSWORD_CHANGED = "USER_PASSWORD_CHANGED"

    # Gestión de devices
    DEVICE_CREATED = "DEVICE_CREATED"
    DEVICE_UPDATED = "DEVICE_UPDATED"
    DEVICE_DELETED = "DEVICE_DELETED"
    DEVICE_API_KEY_REGENERATED = "DEVICE_API_KEY_REGENERATED"
    DEVICE_CONFIG_UPDATED = "DEVICE_CONFIG_UPDATED"
    DEVICE_WENT_OFFLINE = "DEVICE_WENT_OFFLINE"
    DEVICE_CAME_ONLINE = "DEVICE_CAME_ONLINE"

    # Telemetría
    READING_RECEIVED = "READING_RECEIVED"
    HEARTBEAT_RECEIVED = "HEARTBEAT_RECEIVED"

    # Alertas
    ALERT_RULE_CREATED = "ALERT_RULE_CREATED"
    ALERT_RULE_UPDATED = "ALERT_RULE_UPDATED"
    ALERT_RULE_DELETED = "ALERT_RULE_DELETED"
    ALERT_TRIGGERED = "ALERT_TRIGGERED"
    ALERT_ACKNOWLEDGED = "ALERT_ACKNOWLEDGED"

    # Configuración
    CONFIG_TEMPLATE_CREATED = "CONFIG_TEMPLATE_CREATED"
    CONFIG_TEMPLATE_UPDATED = "CONFIG_TEMPLATE_UPDATED"
    CONFIG_PUSHED_TO_DEVICE = "CONFIG_PUSHED_TO_DEVICE"

    # Sistema
    SYSTEM_STARTUP = "SYSTEM_STARTUP"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"
    BACKUP_CREATED = "BACKUP_CREATED"
    BACKUP_RESTORED = "BACKUP_RESTORED"

    # Seguridad
    UNAUTHORIZED_ACCESS_ATTEMPT = "UNAUTHORIZED_ACCESS_ATTEMPT"
    API_KEY_INVALID = "API_KEY_INVALID"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
