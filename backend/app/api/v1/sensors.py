"""
Endpoints REST para gestión de SensorCatalog.

CRUD completo para catálogo de sensores personalizados.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api.deps import get_db, get_current_user
from app.models.sensor_catalog import SensorCatalog
from app.models.user import User
from app.schemas import sensor_catalog as schemas

router = APIRouter(prefix="/sensors", tags=["Sensors"])


@router.get("/", response_model=List[schemas.SensorCatalog])
def list_sensors(
    skip: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(100, ge=1, le=500, description="Límite de resultados"),
    sensor_type: Optional[str] = Query(None, description="Filtrar por tipo de sensor"),
    protocol: Optional[str] = Query(None, description="Filtrar por protocolo"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    include_builtin: bool = Query(True, description="Incluir sensores built-in"),
    search: Optional[str] = Query(None, description="Buscar en nombre, descripción o modelo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Listar sensores del catálogo.

    **Permisos:** Todos los usuarios autenticados.

    **Filtros disponibles:**
    - `sensor_type`: Filtrar por tipo (temperature, humidity, pressure, etc.)
    - `protocol`: Filtrar por protocolo (OneWire, I2C, ADC, etc.)
    - `is_active`: true/false para filtrar por estado
    - `include_builtin`: Incluir o excluir sensores built-in
    - `search`: Buscar por nombre, descripción o modelo
    """
    query = db.query(SensorCatalog)

    # Filtros
    if sensor_type:
        query = query.filter(SensorCatalog.sensor_type == sensor_type)

    if protocol:
        query = query.filter(SensorCatalog.protocol == protocol)

    if is_active is not None:
        query = query.filter(SensorCatalog.is_active == is_active)

    if not include_builtin:
        query = query.filter(SensorCatalog.is_builtin == False)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                SensorCatalog.name.ilike(search_pattern),
                SensorCatalog.description.ilike(search_pattern),
                SensorCatalog.model.ilike(search_pattern),
                SensorCatalog.manufacturer.ilike(search_pattern),
            )
        )

    # Paginación
    sensors = query.offset(skip).limit(limit).all()
    return sensors


@router.get("/stats", response_model=schemas.SensorCatalogStats)
def get_sensor_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtener estadísticas del catálogo de sensores.

    **Permisos:** Todos los usuarios autenticados.
    """
    all_sensors = db.query(SensorCatalog).all()

    # Contadores
    total = len(all_sensors)
    active = sum(1 for s in all_sensors if s.is_active)
    inactive = total - active
    builtin = sum(1 for s in all_sensors if s.is_builtin)
    custom = total - builtin

    # Por tipo
    by_type = {}
    for sensor in all_sensors:
        sensor_type = sensor.sensor_type or "unknown"
        by_type[sensor_type] = by_type.get(sensor_type, 0) + 1

    # Por protocolo
    by_protocol = {}
    for sensor in all_sensors:
        protocol = sensor.protocol or "unknown"
        by_protocol[protocol] = by_protocol.get(protocol, 0) + 1

    return {
        "total": total,
        "active": active,
        "inactive": inactive,
        "builtin": builtin,
        "custom": custom,
        "by_type": by_type,
        "by_protocol": by_protocol,
    }


@router.get("/{sensor_id}", response_model=schemas.SensorCatalog)
def get_sensor(
    sensor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Obtener un sensor específico por ID.

    **Permisos:** Todos los usuarios autenticados.
    """
    sensor = db.query(SensorCatalog).filter(SensorCatalog.id == sensor_id).first()

    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor con ID {sensor_id} no encontrado"
        )

    return sensor


@router.post("/", response_model=schemas.SensorCatalog, status_code=status.HTTP_201_CREATED)
def create_sensor(
    sensor_data: schemas.SensorCatalogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crear un nuevo sensor en el catálogo.

    **Permisos:** Solo super_admin y service_admin.
    """
    # Verificar permisos
    if current_user.role not in ["super_admin", "service_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear sensores"
        )

    # Verificar que no exista otro sensor con el mismo nombre
    existing = db.query(SensorCatalog).filter(SensorCatalog.name == sensor_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un sensor con el nombre '{sensor_data.name}'"
        )

    # Validar value_min < value_max
    if sensor_data.value_min is not None and sensor_data.value_max is not None:
        if sensor_data.value_min >= sensor_data.value_max:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="value_min debe ser menor que value_max"
            )

    # Crear sensor
    new_sensor = SensorCatalog(
        **sensor_data.model_dump(),
        is_builtin=False,  # Los sensores creados por usuario nunca son builtin
    )

    db.add(new_sensor)
    db.commit()
    db.refresh(new_sensor)

    return new_sensor


@router.patch("/{sensor_id}", response_model=schemas.SensorCatalog)
def update_sensor(
    sensor_id: int,
    sensor_data: schemas.SensorCatalogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Actualizar un sensor existente.

    **Permisos:** Solo super_admin y service_admin.
    """
    # Verificar permisos
    if current_user.role not in ["super_admin", "service_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar sensores"
        )

    # Buscar sensor
    sensor = db.query(SensorCatalog).filter(SensorCatalog.id == sensor_id).first()
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor con ID {sensor_id} no encontrado"
        )

    # Validar que no se edite el nombre a uno existente
    if sensor_data.name and sensor_data.name != sensor.name:
        existing = db.query(SensorCatalog).filter(SensorCatalog.name == sensor_data.name).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un sensor con el nombre '{sensor_data.name}'"
            )

    # Actualizar solo campos proporcionados
    update_data = sensor_data.model_dump(exclude_unset=True)

    # Validar value_min < value_max si ambos están presentes
    final_min = update_data.get("value_min", sensor.value_min)
    final_max = update_data.get("value_max", sensor.value_max)
    if final_min is not None and final_max is not None and final_min >= final_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="value_min debe ser menor que value_max"
        )

    for field, value in update_data.items():
        setattr(sensor, field, value)

    db.commit()
    db.refresh(sensor)

    return sensor


@router.delete("/{sensor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sensor(
    sensor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eliminar un sensor del catálogo.

    **Permisos:** Solo super_admin.

    **IMPORTANTE:** No se pueden eliminar sensores built-in (DS18B20, DHT22, MPX5700).
    """
    # Solo super_admin puede eliminar
    if current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo super_admin puede eliminar sensores"
        )

    # Buscar sensor
    sensor = db.query(SensorCatalog).filter(SensorCatalog.id == sensor_id).first()
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor con ID {sensor_id} no encontrado"
        )

    # No permitir eliminar sensores built-in
    if sensor.is_builtin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar el sensor built-in '{sensor.name}'"
        )

    # Eliminar sensor
    db.delete(sensor)
    db.commit()

    return None


@router.patch("/{sensor_id}/activate", response_model=schemas.SensorCatalog)
def activate_sensor(
    sensor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Activar un sensor desactivado.

    **Permisos:** super_admin y service_admin.
    """
    if current_user.role not in ["super_admin", "service_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para activar sensores"
        )

    sensor = db.query(SensorCatalog).filter(SensorCatalog.id == sensor_id).first()
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor con ID {sensor_id} no encontrado"
        )

    sensor.is_active = True
    db.commit()
    db.refresh(sensor)

    return sensor


@router.patch("/{sensor_id}/deactivate", response_model=schemas.SensorCatalog)
def deactivate_sensor(
    sensor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Desactivar un sensor (soft delete).

    **Permisos:** super_admin y service_admin.
    """
    if current_user.role not in ["super_admin", "service_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para desactivar sensores"
        )

    sensor = db.query(SensorCatalog).filter(SensorCatalog.id == sensor_id).first()
    if not sensor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor con ID {sensor_id} no encontrado"
        )

    sensor.is_active = False
    db.commit()
    db.refresh(sensor)

    return sensor
