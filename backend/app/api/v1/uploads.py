"""
Endpoints para manejo de archivos (uploads)

Funcionalidades:
- Upload de imágenes de perfil
- Validación de tipo y tamaño
- Generación de nombres únicos
- Servir archivos estáticos
"""

import logging
import os
import uuid
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuración
UPLOAD_DIR = Path("uploads")
PROFILE_PICTURES_DIR = UPLOAD_DIR / "profile_pictures"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}

# Crear directorios si no existen
PROFILE_PICTURES_DIR.mkdir(parents=True, exist_ok=True)


def validate_image_file(file: UploadFile) -> None:
    """
    Valida que el archivo sea una imagen válida

    Args:
        file: Archivo subido

    Raises:
        HTTPException: Si el archivo no es válido
    """
    # Validar content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Debe ser: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # Validar extensión
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión no permitida. Debe ser: {', '.join(ALLOWED_EXTENSIONS)}",
        )


def generate_unique_filename(original_filename: str) -> str:
    """
    Genera un nombre único para el archivo

    Args:
        original_filename: Nombre original del archivo

    Returns:
        Nombre único con formato: uuid_originalname.ext
    """
    file_ext = Path(original_filename).suffix.lower()
    unique_id = uuid.uuid4().hex[:12]
    safe_name = Path(original_filename).stem[:50]  # Limitar longitud
    return f"{unique_id}_{safe_name}{file_ext}"


@router.post("/upload-profile-picture", status_code=status.HTTP_201_CREATED)
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload de foto de perfil del usuario actual

    Args:
        file: Archivo de imagen
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        URL de la imagen subida

    Raises:
        HTTPException: Si el archivo no es válido o hay error al guardar
    """
    # Validar archivo
    validate_image_file(file)

    # Leer contenido
    contents = await file.read()

    # Validar tamaño
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo excede el tamaño máximo permitido ({MAX_FILE_SIZE / 1024 / 1024}MB)",
        )

    # Generar nombre único
    unique_filename = generate_unique_filename(file.filename or "profile.jpg")
    file_path = PROFILE_PICTURES_DIR / unique_filename

    # Eliminar foto anterior si existe
    if current_user.profile_picture_url:
        old_filename = Path(current_user.profile_picture_url).name
        old_file_path = PROFILE_PICTURES_DIR / old_filename
        if old_file_path.exists():
            try:
                old_file_path.unlink()
            except Exception as e:
                # Log error pero no fallar
                logger.warning(f"Error al eliminar foto anterior: {e}")

    # Guardar archivo
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el archivo: {str(e)}",
        )

    # Construir URL
    file_url = f"/api/v1/uploads/profile-pictures/{unique_filename}"

    # Actualizar usuario en base de datos
    current_user.profile_picture_url = file_url
    db.commit()
    db.refresh(current_user)

    return {
        "url": file_url,
        "filename": unique_filename,
        "message": "Imagen subida exitosamente",
    }


@router.get("/profile-pictures/{filename}")
async def get_profile_picture(filename: str):
    """
    Servir imagen de perfil

    Args:
        filename: Nombre del archivo

    Returns:
        Archivo de imagen

    Raises:
        HTTPException: Si el archivo no existe
    """
    file_path = PROFILE_PICTURES_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada",
        )

    return FileResponse(
        file_path,
        media_type="image/jpeg",  # Será detectado automáticamente
        headers={"Cache-Control": "public, max-age=86400"},  # Cache por 1 día
    )


@router.delete("/profile-pictures/{filename}")
async def delete_profile_picture(
    filename: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Eliminar foto de perfil

    Args:
        filename: Nombre del archivo
        current_user: Usuario autenticado
        db: Sesión de base de datos

    Returns:
        Mensaje de confirmación

    Raises:
        HTTPException: Si el archivo no existe o no pertenece al usuario
    """
    # Verificar que sea la foto del usuario
    if current_user.profile_picture_url:
        current_filename = Path(current_user.profile_picture_url).name
        if current_filename != filename:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para eliminar esta imagen",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tienes foto de perfil",
        )

    # Eliminar archivo
    file_path = PROFILE_PICTURES_DIR / filename
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al eliminar el archivo: {str(e)}",
            )

    # Actualizar base de datos
    current_user.profile_picture_url = None
    db.commit()

    return {"message": "Imagen eliminada exitosamente"}
