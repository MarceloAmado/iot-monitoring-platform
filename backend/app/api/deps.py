"""
Dependencias de FastAPI para los endpoints.

Incluye:
- get_db: Dependencia para obtener sesion de base de datos
- get_current_user: Dependencia para obtener usuario autenticado
- get_current_active_user: Usuario autenticado y activo
- require_admin: Requiere que el usuario sea admin
"""

from typing import Generator, Optional, Callable
from functools import wraps
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from app.core.database import SessionLocal
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.auth import TokenData


# Security scheme para JWT
security = HTTPBearer()


def get_db() -> Generator:
    """
    Dependencia que provee una sesion de base de datos.

    Yields:
        Session: Sesion de SQLAlchemy

    Uso:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependencia que obtiene el usuario actual desde el token JWT.

    Args:
        credentials: Credenciales HTTP Bearer (token JWT)
        db: Sesion de base de datos

    Returns:
        User: Usuario autenticado

    Raises:
        HTTPException: Si el token es invalido o el usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extraer token del header
        token = credentials.credentials

        # Decodificar token
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception

        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if email is None or user_id is None:
            raise credentials_exception

        token_data = TokenData(email=email, user_id=user_id)

    except JWTError:
        raise credentials_exception

    # Buscar usuario en DB
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependencia que verifica que el usuario este activo.

    Args:
        current_user: Usuario actual (de get_current_user)

    Returns:
        User: Usuario activo

    Raises:
        HTTPException: Si el usuario esta inactivo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependencia que requiere que el usuario sea admin.

    Args:
        current_user: Usuario actual

    Returns:
        User: Usuario admin

    Raises:
        HTTPException: Si el usuario no es admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos de administrador"
        )
    return current_user


async def require_super_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependencia que requiere que el usuario sea super admin.

    Args:
        current_user: Usuario actual

    Returns:
        User: Usuario super admin

    Raises:
        HTTPException: Si el usuario no es super admin
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere permisos de super administrador"
        )
    return current_user


def get_accessible_location_ids(user: User) -> Optional[list[int]]:
    """
    Obtiene los IDs de locations que el usuario puede acceder.

    Args:
        user: Usuario autenticado

    Returns:
        None si el usuario es super_admin (acceso a todo)
        Lista de location_ids si el usuario tiene restricciones

    Uso en queries:
        location_ids = get_accessible_location_ids(current_user)
        if location_ids is not None:
            query = query.filter(Model.location_id.in_(location_ids))
    """
    if user.role == 'super_admin':
        return None  # Acceso a todas las locations

    return user.allowed_location_ids or []


def filter_by_user_permissions(query, model_class, user: User):
    """
    Filtra un query de SQLAlchemy según los permisos del usuario.

    Args:
        query: Query de SQLAlchemy
        model_class: Clase del modelo (Location, Asset, Device, etc.)
        user: Usuario autenticado

    Returns:
        Query filtrado según permisos

    Ejemplo:
        query = db.query(Location)
        query = filter_by_user_permissions(query, Location, current_user)
    """
    location_ids = get_accessible_location_ids(user)

    if location_ids is None:
        return query  # Super admin ve todo

    # Si no tiene locations permitidas, no ve nada
    if not location_ids:
        return query.filter(False)  # Query que no retorna nada

    # Filtrar según el modelo
    if hasattr(model_class, 'location_id'):
        # Modelos con location_id directa (Location, Asset, AlertRule)
        return query.filter(model_class.location_id.in_(location_ids))

    elif hasattr(model_class, 'asset'):
        # Device tiene asset → asset.location_id
        from app.models.asset import Asset
        return query.join(Asset).filter(Asset.location_id.in_(location_ids))

    elif hasattr(model_class, 'device'):
        # SensorReading, AlertHistory tienen device → asset → location
        from app.models.device import Device
        from app.models.asset import Asset
        return query.join(Device).join(Asset).filter(Asset.location_id.in_(location_ids))

    else:
        # Si no tiene relación con location, permitir acceso
        # (ej: User, SensorCatalog)
        return query


async def require_location_access(
    location_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> int:
    """
    Dependencia que verifica acceso a una location específica.

    Args:
        location_id: ID de la location a verificar
        current_user: Usuario actual
        db: Sesión de base de datos

    Returns:
        location_id si tiene acceso

    Raises:
        HTTPException 403: Si no tiene acceso a esa location

    Uso:
        @app.get("/locations/{location_id}")
        def get_location(
            location_id: int = Depends(require_location_access),
            ...
        ):
    """
    location_ids = get_accessible_location_ids(current_user)

    # Super admin tiene acceso a todo
    if location_ids is None:
        return location_id

    # Verificar si tiene acceso
    if location_id not in location_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a esta ubicación"
        )

    return location_id


async def validate_device_api_key(
    x_api_key: str = Header(..., description="API Key del device"),
    x_device_eui: str = Header(..., description="Device EUI"),
    db: Session = Depends(get_db)
):
    """
    Valida API Key de device desde headers.

    Este middleware valida la API Key encriptada almacenada en la base de datos.
    Soporta backward compatibility con API keys en plaintext (temporal).

    Args:
        x_api_key: API Key en texto plano del ESP32 (header X-API-Key)
        x_device_eui: Device EUI del ESP32 (header X-Device-EUI)
        db: Sesión de base de datos

    Returns:
        Device: Device autenticado

    Raises:
        HTTPException 401: Si el device no existe, la API key es inválida o está corrupta

    Ejemplo de headers desde ESP32:
        X-API-Key: mi_api_key_secreta_123
        X-Device-EUI: ESP32_LAB_001
    """
    from app.models.device import Device
    from app.core.security import decrypt_api_key
    from app.services.audit_service import AuditService

    # Buscar device por EUI
    device = db.query(Device).filter(Device.device_eui == x_device_eui).first()
    if not device:
        # Registrar intento de acceso con device inexistente
        AuditService.log(
            db=db,
            action_type="API_KEY_INVALID",
            extra_data={"device_eui": x_device_eui, "reason": "device_not_found"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device no encontrado"
        )

    # Intentar validar con api_key_encrypted (nuevo método)
    if device.api_key_encrypted:
        decrypted_key = decrypt_api_key(device.api_key_encrypted)

        if not decrypted_key:
            # API key corrupta o ENCRYPTION_KEY cambió
            AuditService.log(
                db=db,
                action_type="API_KEY_INVALID",
                device_id=device.id,
                extra_data={"device_eui": x_device_eui, "reason": "decryption_failed"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key corrupta - contacte al administrador"
            )

        # Comparar la key desencriptada con la provista
        if decrypted_key != x_api_key:
            # Registrar intento fallido de autenticación
            AuditService.log(
                db=db,
                action_type="API_KEY_INVALID",
                device_id=device.id,
                extra_data={"device_eui": x_device_eui, "reason": "key_mismatch"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key inválida"
            )

        # ✅ Autenticación exitosa con key encriptada
        return device

    # Fallback: Intentar con api_key plaintext (backward compatibility)
    elif device.api_key:
        if device.api_key != x_api_key:
            # Registrar intento fallido
            AuditService.log(
                db=db,
                action_type="API_KEY_INVALID",
                device_id=device.id,
                extra_data={"device_eui": x_device_eui, "reason": "plaintext_key_mismatch"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key inválida"
            )

        # ✅ Autenticación exitosa con key plaintext (legacy)
        import logging
        logging.getLogger(__name__).warning(
            f"Device {device.device_eui} autenticado con API key plaintext. "
            "Migrar a api_key_encrypted para mayor seguridad."
        )
        return device

    else:
        # Device no tiene API key configurada
        AuditService.log(
            db=db,
            action_type="API_KEY_INVALID",
            device_id=device.id,
            extra_data={"device_eui": x_device_eui, "reason": "no_api_key_configured"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device no tiene API Key configurada"
        )


def require_role(*allowed_roles: str):
    """
    Decorador de dependencia para verificar roles de usuario.

    Args:
        *allowed_roles: Roles permitidos ('super_admin', 'service_admin', 'technician', 'guest')

    Returns:
        Función de dependencia que valida el rol

    Raises:
        HTTPException 403: Si el usuario no tiene el rol requerido

    Ejemplo de uso:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: User = Depends(require_role('super_admin', 'service_admin'))
        ):
            return {"message": "Solo admins pueden ver esto"}

        @router.post("/devices")
        async def create_device(
            device: DeviceCreate,
            current_user: User = Depends(require_role('super_admin'))
        ):
            # Solo super_admin puede crear devices
            ...
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requiere uno de estos roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker
