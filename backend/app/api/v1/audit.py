"""
Endpoints REST para Audit Log
Propósito: API para consultar registros de auditoría
Fecha: 2025-10-29
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.api.deps import get_db, get_current_active_user
from app.models.user import User
from app.core.permissions import filter_devices_by_permission
from app.services.audit_service import AuditService
from app.schemas.audit_log import (
    AuditLogResponse,
    AuditLogList,
    AuditLogFilters,
    AuditLogSummary,
    UserActivitySummary
)


router = APIRouter()


@router.get("/", response_model=AuditLogList)
def get_audit_logs(
    user_id: Optional[int] = Query(None, description="Filtrar por ID de usuario"),
    device_id: Optional[int] = Query(None, description="Filtrar por ID de device"),
    action_type: Optional[str] = Query(None, description="Filtrar por tipo de acción"),
    entity_type: Optional[str] = Query(None, description="Filtrar por tipo de entidad"),
    entity_id: Optional[int] = Query(None, description="Filtrar por ID de entidad"),
    date_from: Optional[datetime] = Query(None, description="Fecha desde (UTC)"),
    date_to: Optional[datetime] = Query(None, description="Fecha hasta (UTC)"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(50, ge=1, le=100, description="Tamaño de página"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene registros de audit log con filtros opcionales y paginación.

    Permisos:
    - super_admin: Ve todos los logs
    - service_admin: Ve logs de sus locations
    - technician, guest: NO tienen acceso

    Returns:
        AuditLogList: Lista paginada de logs
    """
    # Validar permisos
    if current_user.role not in ["super_admin", "service_admin"]:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para acceder a los audit logs"
        )

    # RBAC: service_admin solo ve logs de devices en sus locations
    allowed_device_ids = None
    if current_user.role == "service_admin":
        devices_query = filter_devices_by_permission(current_user, db)
        allowed_device_ids = [d.id for d in devices_query.all()]

    # Crear filtros
    filters = AuditLogFilters(
        user_id=user_id,
        device_id=device_id,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
        allowed_device_ids=allowed_device_ids,
        page=page,
        page_size=page_size
    )

    # Obtener logs
    return AuditService.get_logs(db=db, filters=filters)


@router.get("/{audit_log_id}", response_model=AuditLogResponse)
def get_audit_log_by_id(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene un registro de audit log por ID.

    Permisos:
    - super_admin, service_admin: Acceso completo

    Returns:
        AuditLogResponse: Registro de audit log
    """
    # Validar permisos
    if current_user.role not in ["super_admin", "service_admin"]:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para acceder a los audit logs"
        )

    # Buscar log
    audit_log = AuditService.get_by_id(db=db, audit_log_id=audit_log_id)

    if not audit_log:
        raise HTTPException(
            status_code=404,
            detail=f"Audit log con ID {audit_log_id} no encontrado"
        )

    return AuditLogResponse.model_validate(audit_log)


@router.get("/summary/by-action", response_model=list[AuditLogSummary])
def get_summary_by_action(
    date_from: Optional[datetime] = Query(None, description="Fecha desde (UTC)"),
    date_to: Optional[datetime] = Query(None, description="Fecha hasta (UTC)"),
    limit: int = Query(10, ge=1, le=50, description="Cantidad de resultados"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene resumen de actividad agrupado por tipo de acción.

    Útil para dashboards y métricas.

    Permisos:
    - super_admin, service_admin: Acceso completo

    Returns:
        List[AuditLogSummary]: Lista de acciones con conteo
    """
    # Validar permisos
    if current_user.role not in ["super_admin", "service_admin"]:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para acceder a las estadísticas"
        )

    return AuditService.get_summary_by_action(
        db=db,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )


@router.get("/summary/by-user", response_model=list[UserActivitySummary])
def get_user_activity_summary(
    limit: int = Query(10, ge=1, le=50, description="Cantidad de usuarios"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene resumen de actividad por usuario.

    Muestra los usuarios más activos del sistema.

    Permisos:
    - super_admin: Acceso completo

    Returns:
        List[UserActivitySummary]: Lista de usuarios con actividad
    """
    # Validar permisos (solo super_admin)
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=403,
            detail="Solo super_admin puede ver actividad de todos los usuarios"
        )

    return AuditService.get_user_activity_summary(db=db, limit=limit)


@router.get("/me/activity", response_model=AuditLogList)
def get_my_activity(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene el historial de actividad del usuario actual.

    Cualquier usuario puede ver su propia actividad.

    Returns:
        AuditLogList: Logs del usuario actual
    """
    filters = AuditLogFilters(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )

    return AuditService.get_logs(db=db, filters=filters)
