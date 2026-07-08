"""
Endpoints de Firmware (gestión de versiones OTA para ESP32).
"""

import os
import hashlib
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from packaging import version as pkg_version

from app.api.deps import get_db, get_current_active_user, require_admin, validate_device_api_key
from app.models.firmware import Firmware
from app.models.device import Device
from app.models.user import User
from app.schemas.firmware import (
    Firmware as FirmwareSchema,
    FirmwareCreate,
    FirmwareUpdate,
    FirmwareLatestResponse
)
from app.core.config import settings


router = APIRouter(prefix="/firmware", tags=["Firmware OTA"])


# Directorio donde se almacenan los binarios
FIRMWARE_STORAGE_DIR = os.path.join(os.path.dirname(__file__), "../../../uploads/firmware")


def ensure_firmware_directory():
    """Crea el directorio de firmware si no existe."""
    os.makedirs(FIRMWARE_STORAGE_DIR, exist_ok=True)


def calculate_md5(file_path: str) -> str:
    """Calcula el MD5 checksum de un archivo."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def is_version_compatible(current_ver: str, min_ver: Optional[str]) -> bool:
    """
    Verifica si la versión actual es compatible con la mínima requerida.

    Args:
        current_ver: Versión actual del device (ej: "1.0.0")
        min_ver: Versión mínima compatible (ej: "0.9.0")

    Returns:
        True si current_ver >= min_ver o si min_ver es None
    """
    if not min_ver:
        return True

    try:
        return pkg_version.parse(current_ver) >= pkg_version.parse(min_ver)
    except Exception:
        # Si falla el parsing, asumir compatible
        return True


@router.post("/upload", response_model=FirmwareSchema, status_code=status.HTTP_201_CREATED, summary="Subir firmware (Admin)")
async def upload_firmware(
    version: str = Form(..., description="Versión semver (ej: 1.2.3)"),
    release_notes: Optional[str] = Form(None, description="Notas de la release"),
    is_stable: bool = Form(True, description="True si es estable"),
    min_compatible_version: Optional[str] = Form(None, description="Versión mínima compatible"),
    file: UploadFile = File(..., description="Archivo binario (.bin)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Sube una nueva versión de firmware al sistema (solo Admin).

    **Proceso:**
    1. Valida que la versión no exista
    2. Guarda el binario en disco
    3. Calcula MD5 checksum
    4. Registra en base de datos

    **Formato de archivo:** .bin (ESP32 binary)

    **Versionado semántico (semver):**
    - MAJOR.MINOR.PATCH (ej: 1.2.3)
    - MAJOR.MINOR.PATCH-label (ej: 2.0.0-beta, 1.5.0-rc1)

    Args:
        version: Versión del firmware (semver)
        release_notes: Notas de la release (changelog)
        is_stable: True si es release estable
        min_compatible_version: Versión mínima desde la cual se puede actualizar
        file: Archivo binario del firmware
        db: Sesión de base de datos
        current_user: Usuario admin autenticado

    Returns:
        FirmwareSchema: Firmware creado

    Raises:
        HTTPException 400: Si la versión ya existe o el archivo es inválido
    """
    # Validar que la versión no exista
    existing = db.query(Firmware).filter(Firmware.version == version).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La versión {version} ya existe"
        )

    # Validar extensión del archivo
    if not file.filename.endswith('.bin'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo debe ser un binario ESP32 (.bin)"
        )

    # Crear directorio si no existe
    ensure_firmware_directory()

    # Generar nombre de archivo
    safe_version = version.replace('.', '_').replace('-', '_')
    filename = f"esp32_v{safe_version}.bin"
    file_path_absolute = os.path.join(FIRMWARE_STORAGE_DIR, filename)
    file_path_relative = f"firmware/{filename}"

    # Guardar archivo
    try:
        contents = await file.read()
        with open(file_path_absolute, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el archivo: {str(e)}"
        )

    # Calcular MD5 y tamaño
    file_size_bytes = os.path.getsize(file_path_absolute)
    md5_checksum = calculate_md5(file_path_absolute)

    # Si es la primera versión, marcarla como latest
    is_latest = db.query(Firmware).count() == 0

    # Crear registro en BD
    firmware = Firmware(
        version=version,
        file_path=file_path_relative,
        file_size_bytes=file_size_bytes,
        md5_checksum=md5_checksum,
        release_notes=release_notes,
        is_stable=is_stable,
        is_latest=is_latest,
        min_compatible_version=min_compatible_version,
        created_by_user_id=current_user.id
    )

    db.add(firmware)
    db.commit()
    db.refresh(firmware)

    return firmware


@router.get("/versions", response_model=List[FirmwareSchema], summary="Listar versiones de firmware")
def list_firmware_versions(
    only_stable: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Lista todas las versiones de firmware disponibles.

    Args:
        only_stable: Si True, solo retorna versiones estables
        db: Sesión de base de datos
        current_user: Usuario autenticado

    Returns:
        List[FirmwareSchema]: Lista de versiones ordenadas por fecha (más recientes primero)
    """
    query = db.query(Firmware)

    if only_stable:
        query = query.filter(Firmware.is_stable == True)

    versions = query.order_by(Firmware.created_at.desc()).all()
    return versions


@router.get("/latest", response_model=FirmwareLatestResponse, summary="Obtener versión más reciente")
def get_latest_firmware(
    current_version: str,
    device: Device = Depends(validate_device_api_key),
    db: Session = Depends(get_db)
):
    """
    Obtiene la versión más reciente de firmware y verifica si hay update disponible.

    **Usado por ESP32** para chequear si debe actualizarse.

    **Autenticación requerida:**
    - Header `X-API-Key`: API Key del device
    - Header `X-Device-EUI`: Device EUI

    **Flujo:**
    1. ESP32 envía su versión actual
    2. Backend compara con la versión más reciente
    3. Si hay update y es compatible, retorna URL de descarga

    Args:
        current_version: Versión actual del device (ej: "1.0.0")
        device: Device autenticado mediante API Key
        db: Sesión de base de datos

    Returns:
        FirmwareLatestResponse: Información sobre update disponible

    Ejemplo de respuesta:
    ```json
    {
      "latest_version": "1.2.3",
      "current_version": "1.0.0",
      "update_available": true,
      "download_url": "/api/v1/firmware/download/1.2.3",
      "file_size_bytes": 1048576,
      "md5_checksum": "abc123...",
      "is_compatible": true,
      "message": "Update disponible: 1.0.0 → 1.2.3"
    }
    ```
    """
    # Buscar versión más reciente estable
    latest = db.query(Firmware).filter(
        Firmware.is_stable == True
    ).order_by(Firmware.created_at.desc()).first()

    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay versiones de firmware disponibles"
        )

    # Comparar versiones
    try:
        current_ver = pkg_version.parse(current_version)
        latest_ver = pkg_version.parse(latest.version)
        update_available = latest_ver > current_ver
    except Exception:
        # Si falla el parsing, asumir que hay update
        update_available = current_version != latest.version

    # Verificar compatibilidad
    is_compatible = is_version_compatible(current_version, latest.min_compatible_version)

    # Construir respuesta
    response = FirmwareLatestResponse(
        latest_version=latest.version,
        current_version=current_version,
        update_available=update_available,
        is_compatible=is_compatible,
        message=""
    )

    if not update_available:
        response.message = f"Ya estás en la versión más reciente ({current_version})"
    elif not is_compatible:
        response.message = f"Update no compatible. Versión mínima requerida: {latest.min_compatible_version}"
        response.download_url = None
    else:
        response.message = f"Update disponible: {current_version} → {latest.version}"
        response.download_url = f"/api/v1/firmware/download/{latest.version}"
        response.file_size_bytes = latest.file_size_bytes
        response.md5_checksum = latest.md5_checksum
        response.release_notes = latest.release_notes

    return response


@router.get("/download/{version}", summary="Descargar binario de firmware")
def download_firmware(
    version: str,
    device: Device = Depends(validate_device_api_key),
    db: Session = Depends(get_db)
):
    """
    Descarga el binario de una versión específica de firmware.

    **Autenticación requerida:**
    - Header `X-API-Key`: API Key del device
    - Header `X-Device-EUI`: Device EUI

    Args:
        version: Versión del firmware a descargar (ej: "1.2.3")
        device: Device autenticado
        db: Sesión de base de datos

    Returns:
        FileResponse: Archivo binario del firmware

    Raises:
        HTTPException 404: Si la versión no existe
        HTTPException 410: Si el archivo físico no existe
    """
    # Buscar versión en BD
    firmware = db.query(Firmware).filter(Firmware.version == version).first()

    if not firmware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Versión {version} no encontrada"
        )

    # Construir path absoluto
    file_path_absolute = os.path.join(
        os.path.dirname(__file__),
        "../../../uploads",
        firmware.file_path
    )

    # Verificar que el archivo existe
    if not os.path.exists(file_path_absolute):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"El archivo de firmware v{version} no está disponible"
        )

    # Retornar archivo
    return FileResponse(
        path=file_path_absolute,
        media_type="application/octet-stream",
        filename=os.path.basename(firmware.file_path),
        headers={
            "Content-MD5": firmware.md5_checksum,
            # HTTPUpdate del core ESP32 lee "x-MD5" para verificar
            # la integridad del binario antes de flashear
            "x-MD5": firmware.md5_checksum,
            "X-Firmware-Version": firmware.version,
            "X-File-Size": str(firmware.file_size_bytes)
        }
    )


@router.patch("/{firmware_id}", response_model=FirmwareSchema, summary="Actualizar metadata de firmware (Admin)")
def update_firmware_metadata(
    firmware_id: int,
    update_data: FirmwareUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Actualiza metadata de un firmware (no el binario).

    Solo Admin puede ejecutar este endpoint.

    Args:
        firmware_id: ID del firmware
        update_data: Datos a actualizar
        db: Sesión de base de datos
        current_user: Usuario admin

    Returns:
        FirmwareSchema: Firmware actualizado

    Raises:
        HTTPException 404: Si el firmware no existe
    """
    firmware = db.query(Firmware).filter(Firmware.id == firmware_id).first()

    if not firmware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Firmware con ID {firmware_id} no encontrado"
        )

    # Actualizar campos
    if update_data.release_notes is not None:
        firmware.release_notes = update_data.release_notes

    if update_data.is_stable is not None:
        firmware.is_stable = update_data.is_stable

    if update_data.is_latest is not None:
        # Si se marca como latest, desmarcar todos los demás
        if update_data.is_latest:
            db.query(Firmware).update({"is_latest": False})
        firmware.is_latest = update_data.is_latest

    if update_data.min_compatible_version is not None:
        firmware.min_compatible_version = update_data.min_compatible_version

    db.commit()
    db.refresh(firmware)

    return firmware


@router.delete("/{firmware_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar firmware (Admin)")
def delete_firmware(
    firmware_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Elimina un firmware del sistema (solo Admin).

    **IMPORTANTE:** También elimina el archivo físico del disco.

    Args:
        firmware_id: ID del firmware
        db: Sesión de base de datos
        current_user: Usuario admin

    Raises:
        HTTPException 404: Si el firmware no existe
    """
    firmware = db.query(Firmware).filter(Firmware.id == firmware_id).first()

    if not firmware:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Firmware con ID {firmware_id} no encontrado"
        )

    # Eliminar archivo físico
    file_path_absolute = os.path.join(
        os.path.dirname(__file__),
        "../../../uploads",
        firmware.file_path
    )

    if os.path.exists(file_path_absolute):
        try:
            os.remove(file_path_absolute)
        except Exception as e:
            # No fallar si no se puede eliminar el archivo
            import logging
            logging.getLogger(__name__).warning(
                f"No se pudo eliminar archivo {file_path_absolute}: {str(e)}"
            )

    # Eliminar registro de BD
    db.delete(firmware)
    db.commit()

    return None
