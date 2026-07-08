"""
Endpoints de autenticacion (Login, Logout, Get Current User, Password Reset).
"""

from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.core.security import verify_password, create_access_token, hash_password
from app.core.config import settings
from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.schemas.auth import Token, LoginRequest
from app.schemas.user import User as UserSchema, UserPreferencesUpdate
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ChangePasswordRequest,
    ChangePasswordResponse
)
from app.services.email_service import EmailService, log_email_simulation
from app.services.audit_service import AuditService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token, summary="Login de usuario")
def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login de usuario con email y password.

    Retorna un token JWT que debe ser usado en requests subsiguientes
    en el header Authorization: Bearer <token>

    Args:
        login_data: Email y password del usuario
        request: FastAPI Request (para audit log)
        db: Sesion de base de datos

    Returns:
        Token: access_token y token_type

    Raises:
        HTTPException 401: Si las credenciales son incorrectas
    """
    # Buscar usuario por email
    user = db.query(User).filter(User.email == login_data.email).first()

    # Verificar que el usuario existe y la password es correcta
    if not user or not verify_password(login_data.password, user.password_hash):
        # Registrar intento de login fallido
        AuditService.log_from_request(
            db=db,
            request=request,
            action_type="USER_LOGIN_FAILED",
            extra_data={"email": login_data.email, "reason": "invalid_credentials"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar que el usuario este activo
    if not user.is_active:
        # Registrar intento de login con usuario inactivo
        AuditService.log_from_request(
            db=db,
            request=request,
            action_type="USER_LOGIN_FAILED",
            current_user=user,
            extra_data={"email": login_data.email, "reason": "user_inactive"}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario inactivo"
        )

    # Crear token JWT
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id}
    )

    # Actualizar last_login_at
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Registrar login exitoso
    AuditService.log_from_request(
        db=db,
        request=request,
        action_type="USER_LOGIN",
        current_user=user,
        extra_data={"login_method": "password"}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserSchema, summary="Obtener usuario actual")
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene informacion del usuario actualmente autenticado.

    Requiere token JWT valido en el header Authorization.

    Args:
        current_user: Usuario actual (de dependencia)

    Returns:
        UserSchema: Informacion del usuario
    """
    return current_user


@router.patch("/me/preferences", response_model=UserSchema, summary="Actualizar preferencias del usuario actual")
def update_my_preferences(
    payload: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Actualiza las preferencias de UI del usuario autenticado
    (notificaciones, tema, formato de fecha).

    Las preferencias existentes se mergean con las nuevas: solo se
    pisan las claves incluidas en el payload.

    Args:
        payload: Diccionario de preferencias a actualizar
        db: Sesion de base de datos
        current_user: Usuario actual (de dependencia)

    Returns:
        UserSchema: Usuario con las preferencias actualizadas
    """
    merged = dict(current_user.preferences or {})
    merged.update(payload.preferences)
    current_user.preferences = merged

    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/logout", summary="Logout de usuario")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Logout del usuario actual.

    NOTA: En esta implementacion simple, el logout es del lado del cliente
    (eliminar el token). En produccion, se podria implementar una blacklist
    de tokens en Redis.

    Args:
        request: FastAPI Request (para audit log)
        db: Sesión de base de datos
        current_user: Usuario actual

    Returns:
        dict: Mensaje de exito
    """
    # Registrar logout
    AuditService.log_from_request(
        db=db,
        request=request,
        action_type="USER_LOGOUT",
        current_user=current_user
    )

    return {"message": "Logout exitoso"}


@router.post("/forgot-password", response_model=ForgotPasswordResponse, summary="Solicitar recuperación de contraseña")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Solicita recuperación de contraseña.

    Genera un token único con expiración de 10 minutos y lo envía por email.
    Si el email no existe, retorna éxito igualmente (por seguridad).

    Args:
        request: Email del usuario
        db: Sesión de base de datos

    Returns:
        ForgotPasswordResponse: Mensaje de confirmación
    """
    # Buscar usuario por email
    user = db.query(User).filter(User.email == request.email).first()

    # Por seguridad, siempre retornamos éxito aunque el email no exista
    if not user:
        return ForgotPasswordResponse(
            message="Si el email existe, recibirás un link de recuperación",
            email=request.email
        )

    # Generar token único
    token = str(uuid.uuid4())
    expires_at = PasswordResetToken.create_token_expiration()

    # Crear registro en DB
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()

    # Construir URL de reset (usar frontend URL desde settings o hardcodear)
    # En producción, esto debería venir de una variable de entorno
    frontend_url = settings.cors_origins.split(',')[0].strip()  # Usar primer origin de CORS
    reset_url = f"{frontend_url}/reset-password?token={token}"

    # Enviar email de recuperación
    email_sent = EmailService.send_password_reset_email(
        to_email=user.email,
        user_name=f"{user.first_name} {user.last_name}",
        reset_token=token,
        reset_url=reset_url
    )

    # Si SMTP está deshabilitado, loguear el token para desarrollo
    if not settings.smtp_enabled or not email_sent:
        log_email_simulation(
            to_email=user.email,
            subject="Recuperación de Contraseña",
            content=f"Token: {token}\nURL: {reset_url}"
        )

    return ForgotPasswordResponse(
        message="Si el email existe, recibirás un link de recuperación",
        email=request.email
    )


@router.post("/reset-password", response_model=ResetPasswordResponse, summary="Resetear contraseña con token")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Resetea la contraseña usando un token válido.

    El token debe ser válido (no usado, no expirado).

    Args:
        request: Token y nueva contraseña
        db: Sesión de base de datos

    Returns:
        ResetPasswordResponse: Confirmación de éxito

    Raises:
        HTTPException 400: Si el token es inválido o expirado
    """
    # Buscar token
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == request.token
    ).first()

    if not reset_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )

    # Verificar que el token sea válido
    if not reset_token.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado o ya usado"
        )

    # Obtener usuario
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Actualizar contraseña
    user.password_hash = hash_password(request.new_password)

    # Marcar token como usado
    reset_token.used = True

    db.commit()

    return ResetPasswordResponse(
        message="Contraseña actualizada exitosamente",
        success=True
    )


@router.post("/change-password", response_model=ChangePasswordResponse, summary="Cambiar contraseña (usuario logueado)")
def change_password(
    change_request: ChangePasswordRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cambia la contraseña del usuario actualmente logueado.

    Requiere la contraseña actual para confirmar identidad.

    Args:
        change_request: Contraseña actual y nueva
        http_request: FastAPI Request (para audit log)
        db: Sesión de base de datos
        current_user: Usuario actual

    Returns:
        ChangePasswordResponse: Confirmación de éxito

    Raises:
        HTTPException 400: Si la contraseña actual es incorrecta
    """
    # Verificar contraseña actual
    if not verify_password(change_request.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )

    # Actualizar contraseña
    current_user.password_hash = hash_password(change_request.new_password)
    db.commit()

    # Registrar cambio de contraseña
    AuditService.log_from_request(
        db=db,
        request=http_request,
        action_type="USER_PASSWORD_CHANGED",
        current_user=current_user,
        entity_type="user",
        entity_id=current_user.id
    )

    return ChangePasswordResponse(
        message="Contraseña cambiada exitosamente"
    )
