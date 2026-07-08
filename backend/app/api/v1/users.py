"""
Endpoints de Users (CRUD completo, solo para admins).
"""

import logging
from typing import List
from datetime import datetime
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.core.config import settings
from app.core.security import hash_password
from app.core.permissions import is_super_admin
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.services.audit_service import AuditService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=List[UserSchema], summary="Listar usuarios")
def list_users(
    skip: int = 0,
    limit: int = 100,
    include_archived: bool = Query(False, description="Incluir usuarios archivados"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista todos los usuarios (solo super_admin).

    Args:
        skip: Número de registros a saltar (paginación)
        limit: Número máximo de registros a retornar
        include_archived: Si True, incluye usuarios archivados
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        List[UserSchema]: Lista de usuarios

    Raises:
        HTTPException 403: Si no es super_admin
    """
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super_admin puede listar usuarios"
        )

    query = db.query(User)

    if not include_archived:
        query = query.filter(User.archived == False)

    users = query.offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserSchema, summary="Obtener usuario por ID")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene un usuario por ID (solo super_admin).

    Args:
        user_id: ID del usuario
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        UserSchema: Usuario encontrado

    Raises:
        HTTPException 403: Si no es super_admin
        HTTPException 404: Si el usuario no existe
    """
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super_admin puede ver detalles de usuarios"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )

    return user


@router.post("", response_model=UserSchema, status_code=status.HTTP_201_CREATED, summary="Crear usuario")
def create_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Crea un nuevo usuario (solo super_admin).

    La contraseña se hashea automáticamente con bcrypt.

    Args:
        user_data: Datos del nuevo usuario
        request: FastAPI Request (para audit log)
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        UserSchema: Usuario creado

    Raises:
        HTTPException 403: Si no es super_admin
        HTTPException 400: Si el email ya existe
    """
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super_admin puede crear usuarios"
        )

    # Verificar que el email no exista
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario con el email {user_data.email}"
        )

    # Crear usuario
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        allowed_location_ids=user_data.allowed_location_ids,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=user_data.is_active,
        archived=user_data.archived
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Registrar creación de usuario
    AuditService.log_from_request(
        db=db,
        request=request,
        action_type="USER_CREATED",
        current_user=current_user,
        entity_type="user",
        entity_id=user.id,
        changes={
            "after": {
                "email": user.email,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active
            }
        }
    )

    return user


@router.patch("/{user_id}", response_model=UserSchema, summary="Actualizar usuario")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Actualiza un usuario existente (solo super_admin).

    Solo se actualizan los campos proporcionados (PATCH).

    Args:
        user_id: ID del usuario a actualizar
        user_data: Datos a actualizar
        request: FastAPI Request (para audit log)
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        UserSchema: Usuario actualizado

    Raises:
        HTTPException 403: Si no es super_admin
        HTTPException 404: Si el usuario no existe
        HTTPException 400: Si el email ya existe
    """
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super_admin puede actualizar usuarios"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )

    # Guardar estado anterior para audit log
    before_state = {
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "phone_number": user.phone_number
    }

    # Actualizar solo campos proporcionados
    update_data = user_data.model_dump(exclude_unset=True)

    # Si se proporciona email, verificar que no exista
    if "email" in update_data:
        existing_user = db.query(User).filter(
            User.email == update_data["email"],
            User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe otro usuario con el email {update_data['email']}"
            )

    # Si se proporciona password, hashear
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))

    # Aplicar actualizaciones
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)

    # Guardar estado posterior para audit log
    after_state = {
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
        "phone_number": user.phone_number
    }

    # Registrar actualización de usuario
    AuditService.log_from_request(
        db=db,
        request=request,
        action_type="USER_UPDATED",
        current_user=current_user,
        entity_type="user",
        entity_id=user.id,
        changes={
            "before": before_state,
            "after": after_state
        }
    )

    return user


@router.patch("/{user_id}/deactivate", response_model=UserSchema, summary="Desactivar usuario")
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Desactiva un usuario (soft delete).

    El usuario no podrá hacer login pero sus datos se mantienen.

    Args:
        user_id: ID del usuario a desactivar
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        UserSchema: Usuario desactivado

    Raises:
        HTTPException 403: Si no es super_admin
        HTTPException 404: Si el usuario no existe
        HTTPException 400: Si intenta desactivarse a sí mismo
    """
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super_admin puede desactivar usuarios"
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivarte a ti mismo"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )

    user.is_active = False
    db.commit()
    db.refresh(user)

    return user


@router.patch("/{user_id}/activate", response_model=UserSchema, summary="Activar usuario")
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Activa un usuario desactivado.

    Args:
        user_id: ID del usuario a activar
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        UserSchema: Usuario activado

    Raises:
        HTTPException 403: Si no es super_admin
        HTTPException 404: Si el usuario no existe
    """
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super_admin puede activar usuarios"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )

    user.is_active = True
    db.commit()
    db.refresh(user)

    return user


@router.patch("/{user_id}/archive", response_model=UserSchema, summary="Archivar usuario")
def archive_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Archiva un usuario (soft delete adicional).

    El usuario queda archivado para mantener orden en la lista principal.
    También se desactiva automáticamente.

    Args:
        user_id: ID del usuario a archivar
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        UserSchema: Usuario archivado

    Raises:
        HTTPException 403: Si no es super_admin
        HTTPException 404: Si el usuario no existe
        HTTPException 400: Si intenta archivarse a sí mismo
    """
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super_admin puede archivar usuarios"
        )

    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes archivarte a ti mismo"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )

    user.archived = True
    user.archived_at = datetime.utcnow()
    user.is_active = False  # También desactivar

    db.commit()
    db.refresh(user)

    return user


@router.patch("/{user_id}/unarchive", response_model=UserSchema, summary="Desarchivar usuario")
def unarchive_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Desarchiva un usuario previamente archivado.

    Args:
        user_id: ID del usuario a desarchivar
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        UserSchema: Usuario desarchivado

    Raises:
        HTTPException 403: Si no es super_admin
        HTTPException 404: Si el usuario no existe
    """
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super_admin puede desarchivar usuarios"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )

    user.archived = False
    user.archived_at = None
    # No activamos automáticamente, el admin debe hacerlo explícitamente

    db.commit()
    db.refresh(user)

    return user


@router.post("/{user_id}/reset-password", summary="Blanquear contraseña de usuario")
def reset_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Blanquea la contraseña de un usuario y envía una temporal por email.

    Genera una contraseña temporal aleatoria de 12 caracteres.

    Args:
        user_id: ID del usuario
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        dict: Mensaje de confirmación y contraseña temporal (en desarrollo)

    Raises:
        HTTPException 403: Si no es super_admin
        HTTPException 404: Si el usuario no existe
    """
    if not is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super_admin puede blanquear contraseñas"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario con ID {user_id} no encontrado"
        )

    # Generar contraseña temporal (12 caracteres, letras y números)
    temp_password = secrets.token_urlsafe(9)  # ~12 caracteres en base64

    # Actualizar contraseña
    user.password_hash = hash_password(temp_password)
    db.commit()

    # Enviar la contraseña temporal por email
    email_sent = EmailService.send_temp_password_email(
        to_email=user.email,
        user_name=user.full_name,
        temp_password=temp_password,
    )

    response = {
        "message": (
            "Contraseña blanqueada. Se envió una contraseña temporal por email"
            if email_sent
            else "Contraseña blanqueada, pero el email no pudo enviarse (SMTP deshabilitado o con error)"
        ),
        "email": user.email,
        "email_sent": email_sent,
    }

    # La contraseña NUNCA viaja en la respuesta en producción.
    # Fuera de producción, si el email no salió (SMTP deshabilitado en dev),
    # se incluye para no bloquear el testing manual.
    if not email_sent and settings.environment != "production":
        logger.warning(
            f"[PASSWORD RESET] SMTP no disponible; contraseña temporal para "
            f"{user.email} incluida en la respuesta (solo entorno {settings.environment})"
        )
        response["temp_password"] = temp_password

    return response
