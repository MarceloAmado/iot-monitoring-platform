"""
Servicio de Audit Logging
Propósito: Gestión centralizada de registros de auditoría para compliance
Fecha: 2025-10-29
"""

import ipaddress
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from fastapi import Request

from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit_log import (
    AuditLogCreate,
    AuditLogResponse,
    AuditLogList,
    AuditLogFilters,
    AuditLogSummary,
    UserActivitySummary
)


class AuditService:
    """
    Servicio centralizado para audit logging.

    Características:
    - Registro inmutable de acciones
    - Captura automática de IP y User-Agent
    - Soporte para cambios before/after
    - Queries optimizadas con paginación
    """

    @staticmethod
    def log(
        db: Session,
        action_type: str,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        device_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Registra una acción en el audit log.

        Args:
            db: Sesión de base de datos
            action_type: Tipo de acción (ej: USER_LOGIN, DEVICE_CREATED)
            user_id: ID del usuario que realizó la acción
            user_role: Rol del usuario (snapshot)
            device_id: ID del device relacionado
            entity_type: Tipo de entidad afectada (user, device, alert_rule)
            entity_id: ID de la entidad afectada
            changes: Diccionario con before/after: {"before": {...}, "after": {...}}
            ip_address: IP de origen
            user_agent: User-Agent del cliente
            metadata: Metadata adicional

        Returns:
            AuditLog: Registro creado

        Ejemplo:
            >>> AuditService.log(
            ...     db=db,
            ...     action_type="USER_LOGIN",
            ...     user_id=5,
            ...     user_role="service_admin",
            ...     ip_address="192.168.1.100",
            ...     extra_data={"login_method": "password"}
            ... )
        """
        # Validar que ip_address sea una IP válida para PostgreSQL INET
        if ip_address:
            try:
                ipaddress.ip_address(ip_address)
            except ValueError:
                ip_address = None

        audit_log = AuditLog(
            user_id=user_id,
            user_role=user_role,
            device_id=device_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        return audit_log

    @staticmethod
    def log_from_request(
        db: Session,
        request: Request,
        action_type: str,
        current_user: Optional[User] = None,
        device_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        changes: Optional[Dict[str, Any]] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Registra una acción extrayendo automáticamente IP y User-Agent del Request.

        Args:
            db: Sesión de base de datos
            request: FastAPI Request object
            action_type: Tipo de acción
            current_user: Usuario actual (opcional)
            device_id: ID del device relacionado
            entity_type: Tipo de entidad afectada
            entity_id: ID de la entidad afectada
            changes: Cambios before/after
            metadata: Metadata adicional

        Returns:
            AuditLog: Registro creado

        Ejemplo:
            >>> AuditService.log_from_request(
            ...     db=db,
            ...     request=request,
            ...     action_type="DEVICE_CREATED",
            ...     current_user=current_user,
            ...     entity_type="device",
            ...     entity_id=new_device.id
            ... )
        """
        # Extraer IP (considerar X-Forwarded-For si está detrás de proxy)
        ip_address = request.client.host if request.client else None
        if "x-forwarded-for" in request.headers:
            ip_address = request.headers["x-forwarded-for"].split(",")[0].strip()

        # Extraer User-Agent
        user_agent = request.headers.get("user-agent")

        # Datos del usuario
        user_id = current_user.id if current_user else None
        user_role = current_user.role if current_user else None

        return AuditService.log(
            db=db,
            action_type=action_type,
            user_id=user_id,
            user_role=user_role,
            device_id=device_id,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data
        )

    @staticmethod
    def get_logs(
        db: Session,
        filters: AuditLogFilters
    ) -> AuditLogList:
        """
        Obtiene logs con filtros y paginación.

        Args:
            db: Sesión de base de datos
            filters: Filtros de búsqueda

        Returns:
            AuditLogList: Lista paginada de logs

        Ejemplo:
            >>> filters = AuditLogFilters(
            ...     user_id=5,
            ...     action_type="USER_LOGIN",
            ...     page=1,
            ...     page_size=50
            ... )
            >>> result = AuditService.get_logs(db, filters)
        """
        # Query base
        query = db.query(AuditLog)

        # Aplicar filtros
        if filters.user_id:
            query = query.filter(AuditLog.user_id == filters.user_id)

        if filters.device_id:
            query = query.filter(AuditLog.device_id == filters.device_id)

        if filters.action_type:
            query = query.filter(AuditLog.action_type == filters.action_type)

        if filters.entity_type:
            query = query.filter(AuditLog.entity_type == filters.entity_type)

        if filters.entity_id:
            query = query.filter(AuditLog.entity_id == filters.entity_id)

        if filters.allowed_device_ids is not None:
            # RBAC: service_admin solo ve logs de sus devices o sus propias acciones
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    AuditLog.device_id.in_(filters.allowed_device_ids),
                    AuditLog.device_id.is_(None)
                )
            )

        if filters.date_from:
            query = query.filter(AuditLog.timestamp >= filters.date_from)

        if filters.date_to:
            query = query.filter(AuditLog.timestamp <= filters.date_to)

        # Contar total
        total = query.count()

        # Ordenar por timestamp DESC (más recientes primero)
        query = query.order_by(desc(AuditLog.timestamp))

        # Paginación
        offset = (filters.page - 1) * filters.page_size
        items = query.offset(offset).limit(filters.page_size).all()

        # Calcular total de páginas
        total_pages = (total + filters.page_size - 1) // filters.page_size

        return AuditLogList(
            items=[AuditLogResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages
        )

    @staticmethod
    def get_by_id(db: Session, audit_log_id: int) -> Optional[AuditLog]:
        """
        Obtiene un registro de audit log por ID.

        Args:
            db: Sesión de base de datos
            audit_log_id: ID del registro

        Returns:
            AuditLog o None si no existe
        """
        return db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()

    @staticmethod
    def get_summary_by_action(
        db: Session,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 10
    ) -> List[AuditLogSummary]:
        """
        Obtiene resumen de actividad agrupado por tipo de acción.

        Args:
            db: Sesión de base de datos
            date_from: Fecha desde
            date_to: Fecha hasta
            limit: Cantidad máxima de resultados

        Returns:
            Lista de AuditLogSummary

        Ejemplo:
            >>> summary = AuditService.get_summary_by_action(db, limit=5)
            >>> # Retorna: [
            >>> #   {"action_type": "USER_LOGIN", "count": 150, "last_occurrence": "..."},
            >>> #   {"action_type": "DEVICE_CREATED", "count": 45, ...},
            >>> #   ...
            >>> # ]
        """
        query = db.query(
            AuditLog.action_type,
            func.count(AuditLog.id).label("count"),
            func.max(AuditLog.timestamp).label("last_occurrence")
        )

        # Filtros de fecha
        if date_from:
            query = query.filter(AuditLog.timestamp >= date_from)
        if date_to:
            query = query.filter(AuditLog.timestamp <= date_to)

        # Agrupar y ordenar
        results = (
            query
            .group_by(AuditLog.action_type)
            .order_by(desc("count"))
            .limit(limit)
            .all()
        )

        return [
            AuditLogSummary(
                action_type=row.action_type,
                count=row.count,
                last_occurrence=row.last_occurrence
            )
            for row in results
        ]

    @staticmethod
    def get_user_activity_summary(
        db: Session,
        limit: int = 10
    ) -> List[UserActivitySummary]:
        """
        Obtiene resumen de actividad por usuario.

        Args:
            db: Sesión de base de datos
            limit: Cantidad máxima de usuarios

        Returns:
            Lista de UserActivitySummary
        """
        # Subquery para acción más común por usuario
        most_common_subquery = (
            db.query(
                AuditLog.user_id,
                AuditLog.action_type,
                func.count(AuditLog.id).label("action_count"),
                func.row_number()
                .over(
                    partition_by=AuditLog.user_id,
                    order_by=desc(func.count(AuditLog.id))
                )
                .label("row_num")
            )
            .group_by(AuditLog.user_id, AuditLog.action_type)
            .subquery()
        )

        # Query principal
        results = (
            db.query(
                AuditLog.user_id,
                User.email,
                func.count(AuditLog.id).label("total_actions"),
                func.max(AuditLog.timestamp).label("last_activity")
            )
            .join(User, AuditLog.user_id == User.id, isouter=True)
            .filter(AuditLog.user_id.isnot(None))
            .group_by(AuditLog.user_id, User.email)
            .order_by(desc("total_actions"))
            .limit(limit)
            .all()
        )

        summaries = []
        for row in results:
            # Obtener acción más común
            most_common = (
                db.query(most_common_subquery.c.action_type)
                .filter(
                    and_(
                        most_common_subquery.c.user_id == row.user_id,
                        most_common_subquery.c.row_num == 1
                    )
                )
                .scalar()
            )

            summaries.append(
                UserActivitySummary(
                    user_id=row.user_id,
                    user_email=row.email,
                    total_actions=row.total_actions,
                    last_activity=row.last_activity,
                    most_common_action=most_common
                )
            )

        return summaries

    @staticmethod
    def delete_old_logs(db: Session, days: int = 365) -> int:
        """
        Elimina logs más antiguos que X días (para limpieza periódica).

        NOTA: En producción esto debería archivarse en lugar de eliminarse.

        Args:
            db: Sesión de base de datos
            days: Días de retención

        Returns:
            int: Cantidad de registros eliminados

        Ejemplo:
            >>> # Eliminar logs de más de 2 años
            >>> deleted = AuditService.delete_old_logs(db, days=730)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted_count = (
            db.query(AuditLog)
            .filter(AuditLog.timestamp < cutoff_date)
            .delete()
        )

        db.commit()
        return deleted_count
