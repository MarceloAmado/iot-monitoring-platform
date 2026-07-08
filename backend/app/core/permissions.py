"""
Sistema de permisos RBAC (Role-Based Access Control).

Define roles y funciones helper para verificar permisos.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.location import Location
from app.models.device import Device


# ============================================
# Definición de Roles
# ============================================

class UserRole:
    """Enum-like class para roles de usuario."""
    SUPER_ADMIN = "super_admin"
    SERVICE_ADMIN = "service_admin"
    TECHNICIAN = "technician"
    GUEST = "guest"

    @classmethod
    def all_roles(cls) -> List[str]:
        """Retorna lista de todos los roles válidos."""
        return [cls.SUPER_ADMIN, cls.SERVICE_ADMIN, cls.TECHNICIAN, cls.GUEST]

    @classmethod
    def admin_roles(cls) -> List[str]:
        """Retorna roles con permisos de administración."""
        return [cls.SUPER_ADMIN, cls.SERVICE_ADMIN]


# ============================================
# Funciones de Verificación de Permisos
# ============================================

def is_super_admin(user: User) -> bool:
    """
    Verifica si el usuario es super_admin.

    Super admin tiene acceso total sin restricciones.
    """
    return user.role == UserRole.SUPER_ADMIN


def is_admin(user: User) -> bool:
    """
    Verifica si el usuario tiene rol de admin (super_admin o service_admin).
    """
    return user.role in UserRole.admin_roles()


def can_manage_users(user: User) -> bool:
    """
    Verifica si el usuario puede gestionar otros usuarios.

    Solo super_admin puede crear/editar/eliminar usuarios.
    """
    return user.role == UserRole.SUPER_ADMIN


def can_manage_alert_rules(user: User) -> bool:
    """
    Verifica si el usuario puede gestionar reglas de alertas.

    Super_admin y service_admin pueden gestionar reglas.
    """
    return user.role in [UserRole.SUPER_ADMIN, UserRole.SERVICE_ADMIN]


def can_manage_devices(user: User) -> bool:
    """
    Verifica si el usuario puede gestionar devices.

    Super_admin y service_admin pueden crear/editar/eliminar devices.
    """
    return user.role in [UserRole.SUPER_ADMIN, UserRole.SERVICE_ADMIN]


def has_location_access(user: User, location_id: int) -> bool:
    """
    Verifica si el usuario tiene acceso a una location específica.

    Args:
        user: Usuario a verificar
        location_id: ID de la location

    Returns:
        bool: True si tiene acceso, False si no

    Lógica:
        - super_admin: acceso a todas las locations (ignora allowed_location_ids)
        - otros roles: solo locations en allowed_location_ids
        - si allowed_location_ids es NULL/empty: sin acceso (excepto super_admin)
    """
    # Super admin tiene acceso a todo
    if is_super_admin(user):
        return True

    # Sin locations permitidas = sin acceso
    if not user.allowed_location_ids:
        return False

    # Verificar si location_id está en la lista permitida
    return location_id in user.allowed_location_ids


def has_device_access(user: User, device: Device, db: Session) -> bool:
    """
    Verifica si el usuario tiene acceso a un device específico.

    Args:
        user: Usuario a verificar
        device: Device a verificar
        db: Sesión de base de datos

    Returns:
        bool: True si tiene acceso, False si no

    Lógica:
        - super_admin: acceso a todos los devices
        - otros roles: solo devices cuyo asset.location_id esté en allowed_location_ids
    """
    # Super admin tiene acceso a todo
    if is_super_admin(user):
        return True

    # Si el device no tiene asset asignado, solo super_admin puede verlo
    if not device.asset_id:
        return False

    # Obtener location_id del asset del device
    from app.models.asset import Asset
    asset = db.query(Asset).filter(Asset.id == device.asset_id).first()

    if not asset:
        return False

    # Verificar acceso a la location del asset
    return has_location_access(user, asset.location_id)


def filter_locations_by_permission(user: User, db: Session):
    """
    Retorna un query filtrado de locations según permisos del usuario.

    Args:
        user: Usuario actual
        db: Sesión de base de datos

    Returns:
        Query de SQLAlchemy filtrado

    Usage:
        query = filter_locations_by_permission(current_user, db)
        locations = query.all()
    """
    from app.models.location import Location

    query = db.query(Location)

    # Super admin ve todas las locations
    if is_super_admin(user):
        return query

    # Otros roles: solo locations permitidas
    if user.allowed_location_ids:
        query = query.filter(Location.id.in_(user.allowed_location_ids))
    else:
        # Sin locations permitidas: query vacío
        query = query.filter(Location.id == -1)  # Never matches

    return query


def filter_assets_by_permission(user: User, db: Session):
    """
    Retorna un query filtrado de assets según permisos del usuario.

    Args:
        user: Usuario actual
        db: Sesión de base de datos

    Returns:
        Query de SQLAlchemy filtrado
    """
    from app.models.asset import Asset

    query = db.query(Asset)

    if is_super_admin(user):
        return query

    if user.allowed_location_ids:
        query = query.filter(Asset.location_id.in_(user.allowed_location_ids))
    else:
        query = query.filter(Asset.id == -1)

    return query


def filter_devices_by_permission(user: User, db: Session):
    """
    Retorna un query filtrado de devices según permisos del usuario.

    Args:
        user: Usuario actual
        db: Sesión de base de datos

    Returns:
        Query de SQLAlchemy filtrado con joins necesarios

    Usage:
        query = filter_devices_by_permission(current_user, db)
        devices = query.all()
    """
    from app.models.device import Device
    from app.models.asset import Asset

    query = db.query(Device).join(Asset, Device.asset_id == Asset.id, isouter=True)

    # Super admin ve todos los devices
    if is_super_admin(user):
        return query

    # Otros roles: solo devices cuyo asset esté en locations permitidas
    if user.allowed_location_ids:
        query = query.filter(Asset.location_id.in_(user.allowed_location_ids))
    else:
        # Sin locations permitidas: query vacío
        query = query.filter(Device.id == -1)  # Never matches

    return query


def require_permission(
    user: User,
    required_roles: List[str],
    error_message: Optional[str] = None
) -> None:
    """
    Lanza HTTPException si el usuario no tiene uno de los roles requeridos.

    Args:
        user: Usuario a verificar
        required_roles: Lista de roles permitidos
        error_message: Mensaje de error personalizado (opcional)

    Raises:
        HTTPException: 403 Forbidden si no tiene permiso

    Usage:
        require_permission(current_user, [UserRole.SUPER_ADMIN, UserRole.SERVICE_ADMIN])
    """
    if user.role not in required_roles:
        if not error_message:
            roles_str = ", ".join(required_roles)
            error_message = f"Acceso denegado. Roles permitidos: {roles_str}"

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_message
        )


def require_location_access(user: User, location_id: int) -> None:
    """
    Lanza HTTPException si el usuario no tiene acceso a la location.

    Args:
        user: Usuario a verificar
        location_id: ID de la location

    Raises:
        HTTPException: 403 Forbidden si no tiene acceso

    Usage:
        require_location_access(current_user, location_id)
    """
    if not has_location_access(user, location_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes acceso a la location con ID {location_id}"
        )


def require_device_access(user: User, device: Device, db: Session) -> None:
    """
    Lanza HTTPException si el usuario no tiene acceso al device.

    Args:
        user: Usuario a verificar
        device: Device a verificar
        db: Sesión de base de datos

    Raises:
        HTTPException: 403 Forbidden si no tiene acceso

    Usage:
        require_device_access(current_user, device, db)
    """
    if not has_device_access(user, device, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes acceso al device '{device.name}'"
        )
