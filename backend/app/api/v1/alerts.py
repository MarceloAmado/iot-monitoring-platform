"""
Endpoints REST para AlertRules y AlertHistory.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.alert import AlertRule, AlertHistory
from app.schemas.alert import (
    AlertRule as AlertRuleSchema,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertHistory as AlertHistorySchema,
)

router = APIRouter()


# ============================================
# CRUD AlertRules
# ============================================

@router.get("/alert-rules", response_model=List[AlertRuleSchema])
def list_alert_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    location_id: Optional[int] = Query(None, description="Filtrar por location_id"),
    device_id: Optional[int] = Query(None, description="Filtrar por device_id"),
    enabled: Optional[bool] = Query(None, description="Filtrar por enabled"),
    skip: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(100, ge=1, le=500, description="Límite de resultados"),
):
    """
    Listar todas las alert_rules con filtros opcionales.

    **Filtros disponibles:**
    - location_id: Reglas de una location específica
    - device_id: Reglas de un device específico
    - enabled: Solo reglas activas (True) o inactivas (False)

    **Paginación:**
    - skip: Cantidad de registros a saltar
    - limit: Cantidad máxima de resultros (default 100, max 500)
    """
    query = db.query(AlertRule)

    # Aplicar filtros
    if location_id is not None:
        query = query.filter(AlertRule.location_id == location_id)

    if device_id is not None:
        query = query.filter(AlertRule.device_id == device_id)

    if enabled is not None:
        query = query.filter(AlertRule.enabled == enabled)

    # Ordenar por ID descendente (más recientes primero)
    query = query.order_by(AlertRule.id.desc())

    # Aplicar paginación
    rules = query.offset(skip).limit(limit).all()

    return rules


@router.get("/alert-rules/{rule_id}", response_model=AlertRuleSchema)
def get_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtener detalle de una alert_rule específica por ID.
    """
    rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()

    if not rule:
        raise HTTPException(status_code=404, detail=f"AlertRule con ID {rule_id} no encontrada")

    return rule


@router.post("/alert-rules", response_model=AlertRuleSchema, status_code=201)
def create_alert_rule(
    rule_data: AlertRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crear una nueva alert_rule.

    **Validaciones:**
    - check_type debe ser uno de: THRESHOLD_ABOVE, THRESHOLD_BELOW, THRESHOLD_RANGE,
      RATE_OF_CHANGE, DEVICE_OFFLINE, SENSOR_FAULT
    - threshold_value requerido para THRESHOLD_ABOVE/BELOW
    - threshold_min y threshold_max requeridos para THRESHOLD_RANGE
    - time_window_minutes requerido para RATE_OF_CHANGE y DEVICE_OFFLINE
    - notification_channels no puede estar vacío
    - webhook_url requerido si "webhook" está en notification_channels

    **Roles permitidos:** super_admin, service_admin
    """
    # Validar rol (solo admins pueden crear reglas)
    if current_user.role not in ["super_admin", "service_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Solo super_admin y service_admin pueden crear alert_rules"
        )

    # Validar check_type
    valid_check_types = [
        "THRESHOLD_ABOVE",
        "THRESHOLD_BELOW",
        "THRESHOLD_RANGE",
        "RATE_OF_CHANGE",
        "DEVICE_OFFLINE",
        "SENSOR_FAULT",
    ]

    if rule_data.check_type not in valid_check_types:
        raise HTTPException(
            status_code=400,
            detail=f"check_type inválido. Debe ser uno de: {', '.join(valid_check_types)}"
        )

    # Validaciones específicas por tipo
    if rule_data.check_type in ["THRESHOLD_ABOVE", "THRESHOLD_BELOW"]:
        if rule_data.threshold_value is None:
            raise HTTPException(
                status_code=400,
                detail=f"threshold_value es requerido para check_type {rule_data.check_type}"
            )

    if rule_data.check_type == "THRESHOLD_RANGE":
        if rule_data.threshold_min is None or rule_data.threshold_max is None:
            raise HTTPException(
                status_code=400,
                detail="threshold_min y threshold_max son requeridos para THRESHOLD_RANGE"
            )
        if rule_data.threshold_min >= rule_data.threshold_max:
            raise HTTPException(
                status_code=400,
                detail="threshold_min debe ser menor que threshold_max"
            )

    if rule_data.check_type in ["RATE_OF_CHANGE", "DEVICE_OFFLINE"]:
        if rule_data.time_window_minutes is None:
            raise HTTPException(
                status_code=400,
                detail=f"time_window_minutes es requerido para check_type {rule_data.check_type}"
            )

    # Validar notification_channels
    if not rule_data.notification_channels:
        raise HTTPException(
            status_code=400,
            detail="notification_channels no puede estar vacío"
        )

    valid_channels = ["email", "telegram", "webhook"]
    for channel in rule_data.notification_channels:
        if channel not in valid_channels:
            raise HTTPException(
                status_code=400,
                detail=f"Canal inválido '{channel}'. Canales válidos: {', '.join(valid_channels)}"
            )

    # Validar webhook_url si webhook está en channels
    if "webhook" in rule_data.notification_channels and not rule_data.webhook_url:
        raise HTTPException(
            status_code=400,
            detail="webhook_url es requerido cuando 'webhook' está en notification_channels"
        )

    # Crear la regla
    db_rule = AlertRule(**rule_data.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)

    return db_rule


@router.patch("/alert-rules/{rule_id}", response_model=AlertRuleSchema)
def update_alert_rule(
    rule_id: int,
    rule_data: AlertRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Actualizar una alert_rule existente (PATCH parcial).

    **Roles permitidos:** super_admin, service_admin
    """
    # Validar rol
    if current_user.role not in ["super_admin", "service_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Solo super_admin y service_admin pueden actualizar alert_rules"
        )

    # Buscar regla
    db_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail=f"AlertRule con ID {rule_id} no encontrada")

    # Actualizar solo los campos enviados
    update_data = rule_data.model_dump(exclude_unset=True)

    # Validar check_type si se actualiza
    if "check_type" in update_data:
        valid_check_types = [
            "THRESHOLD_ABOVE", "THRESHOLD_BELOW", "THRESHOLD_RANGE",
            "RATE_OF_CHANGE", "DEVICE_OFFLINE", "SENSOR_FAULT"
        ]
        if update_data["check_type"] not in valid_check_types:
            raise HTTPException(
                status_code=400,
                detail=f"check_type inválido. Debe ser uno de: {', '.join(valid_check_types)}"
            )

    # Validar notification_channels si se actualiza
    if "notification_channels" in update_data:
        if not update_data["notification_channels"]:
            raise HTTPException(
                status_code=400,
                detail="notification_channels no puede estar vacío"
            )
        valid_channels = ["email", "telegram", "webhook"]
        for channel in update_data["notification_channels"]:
            if channel not in valid_channels:
                raise HTTPException(
                    status_code=400,
                    detail=f"Canal inválido '{channel}'. Canales válidos: {', '.join(valid_channels)}"
                )

    # Aplicar actualizaciones
    for field, value in update_data.items():
        setattr(db_rule, field, value)

    db.commit()
    db.refresh(db_rule)

    return db_rule


@router.delete("/alert-rules/{rule_id}", status_code=204)
def delete_alert_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eliminar una alert_rule.

    **Nota:** Esto también eliminará el historial asociado (CASCADE).

    **Roles permitidos:** super_admin, service_admin
    """
    # Validar rol
    if current_user.role not in ["super_admin", "service_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Solo super_admin y service_admin pueden eliminar alert_rules"
        )

    # Buscar regla
    db_rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail=f"AlertRule con ID {rule_id} no encontrada")

    # Eliminar
    db.delete(db_rule)
    db.commit()

    return None


# ============================================
# AlertHistory Endpoints
# ============================================

@router.get("/alert-history", response_model=List[AlertHistorySchema])
def list_alert_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rule_id: Optional[int] = Query(None, description="Filtrar por alert_rule_id"),
    device_id: Optional[int] = Query(None, description="Filtrar por device_id"),
    acknowledged: Optional[bool] = Query(None, description="Filtrar por acknowledged"),
    skip: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(100, ge=1, le=500, description="Límite de resultados"),
):
    """
    Listar historial de alertas disparadas con filtros opcionales.

    **Filtros disponibles:**
    - rule_id: Alertas de una regla específica
    - device_id: Alertas de un device específico
    - acknowledged: Alertas vistas (True) o no vistas (False)

    **Orden:** Más recientes primero (triggered_at DESC)
    """
    query = db.query(AlertHistory)

    # Aplicar filtros
    if rule_id is not None:
        query = query.filter(AlertHistory.alert_rule_id == rule_id)

    if device_id is not None:
        query = query.filter(AlertHistory.device_id == device_id)

    if acknowledged is not None:
        if acknowledged:
            query = query.filter(AlertHistory.acknowledged_by.isnot(None))
        else:
            query = query.filter(AlertHistory.acknowledged_by.is_(None))

    # Ordenar por fecha descendente
    query = query.order_by(AlertHistory.triggered_at.desc())

    # Aplicar paginación
    history = query.offset(skip).limit(limit).all()

    return history


@router.get("/alert-history/{alert_id}", response_model=AlertHistorySchema)
def get_alert_history_detail(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtener detalle de una alerta específica del historial.
    """
    alert = db.query(AlertHistory).filter(AlertHistory.id == alert_id).first()

    if not alert:
        raise HTTPException(status_code=404, detail=f"AlertHistory con ID {alert_id} no encontrada")

    return alert


@router.patch("/alert-history/{alert_id}/acknowledge", response_model=AlertHistorySchema)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Marcar una alerta como vista/reconocida (acknowledge).

    Actualiza los campos:
    - acknowledged_by: ID del usuario que la marcó
    - acknowledged_at: Timestamp actual
    """
    from datetime import datetime

    # Buscar alerta
    alert = db.query(AlertHistory).filter(AlertHistory.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"AlertHistory con ID {alert_id} no encontrada")

    # Verificar si ya fue acknowledged
    if alert.acknowledged_by is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Esta alerta ya fue acknowledged por usuario ID {alert.acknowledged_by}"
        )

    # Marcar como acknowledged
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()

    db.commit()
    db.refresh(alert)

    return alert


@router.get("/alert-stats")
def get_alert_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtener estadísticas generales de alertas.

    **Retorna:**
    - total_rules: Total de reglas configuradas
    - active_rules: Reglas activas (enabled=True)
    - inactive_rules: Reglas inactivas (enabled=False)
    - total_alerts_triggered: Total de alertas disparadas
    - unacknowledged_alerts: Alertas sin reconocer
    - acknowledged_alerts: Alertas reconocidas
    """
    # Contar reglas
    total_rules = db.query(AlertRule).count()
    active_rules = db.query(AlertRule).filter(AlertRule.enabled == True).count()
    inactive_rules = db.query(AlertRule).filter(AlertRule.enabled == False).count()

    # Contar alertas
    total_alerts = db.query(AlertHistory).count()
    unack_alerts = db.query(AlertHistory).filter(AlertHistory.acknowledged_by.is_(None)).count()
    ack_alerts = db.query(AlertHistory).filter(AlertHistory.acknowledged_by.isnot(None)).count()

    return {
        "total_rules": total_rules,
        "active_rules": active_rules,
        "inactive_rules": inactive_rules,
        "total_alerts_triggered": total_alerts,
        "unacknowledged_alerts": unack_alerts,
        "acknowledged_alerts": ack_alerts,
    }
