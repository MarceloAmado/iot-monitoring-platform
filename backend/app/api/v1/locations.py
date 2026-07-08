"""
Endpoints de LocationGroup y Location (CRUD con RBAC).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.models.location import LocationGroup, Location
from app.models.user import User
from app.core.permissions import (
    is_super_admin,
    is_admin,
    filter_locations_by_permission,
    has_location_access,
    require_location_access,
)
from app.schemas.location import (
    LocationGroup as LocationGroupSchema,
    LocationGroupCreate,
    LocationGroupUpdate,
    Location as LocationSchema,
    LocationCreate,
    LocationUpdate,
)
from app.services.audit_service import AuditService


router = APIRouter(tags=["Locations"])


# ============================================
# LocationGroup Endpoints
# ============================================

@router.get("/location-groups", response_model=List[LocationGroupSchema], summary="Listar grupos de ubicación")
def list_location_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista todos los grupos de ubicación."""
    query = db.query(LocationGroup)
    groups = query.offset(skip).limit(limit).all()
    return groups


@router.post("/location-groups", response_model=LocationGroupSchema, status_code=status.HTTP_201_CREATED, summary="Crear grupo de ubicación")
def create_location_group(
    data: LocationGroupCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "service_admin")),
):
    """Crea un nuevo grupo de ubicación. Requiere rol admin."""
    existing = db.query(LocationGroup).filter(LocationGroup.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un grupo con el nombre '{data.name}'",
        )

    group = LocationGroup(**data.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)

    AuditService.log_from_request(
        db=db, request=request, action_type="LOCATION_GROUP_CREATED",
        current_user=current_user, entity_type="location_group", entity_id=group.id,
    )

    return group


@router.get("/location-groups/{group_id}", response_model=LocationGroupSchema, summary="Obtener grupo por ID")
def get_location_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene un grupo de ubicación por ID."""
    group = db.query(LocationGroup).filter(LocationGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado")
    return group


@router.patch("/location-groups/{group_id}", response_model=LocationGroupSchema, summary="Actualizar grupo")
def update_location_group(
    group_id: int,
    data: LocationGroupUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "service_admin")),
):
    """Actualiza un grupo de ubicación. Requiere rol admin."""
    group = db.query(LocationGroup).filter(LocationGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(group, key, value)

    db.commit()
    db.refresh(group)

    AuditService.log_from_request(
        db=db, request=request, action_type="LOCATION_GROUP_UPDATED",
        current_user=current_user, entity_type="location_group", entity_id=group.id,
        changes={"after": update_data},
    )

    return group


@router.delete("/location-groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar grupo")
def delete_location_group(
    group_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    """Elimina un grupo de ubicación y todas sus locations en cascada. Solo super_admin."""
    group = db.query(LocationGroup).filter(LocationGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo no encontrado")

    AuditService.log_from_request(
        db=db, request=request, action_type="LOCATION_GROUP_DELETED",
        current_user=current_user, entity_type="location_group", entity_id=group.id,
        changes={"before": {"name": group.name}},
    )

    db.delete(group)
    db.commit()


# ============================================
# Location Endpoints
# ============================================

@router.get("/locations", response_model=List[LocationSchema], summary="Listar ubicaciones")
def list_locations(
    skip: int = 0,
    limit: int = 100,
    location_group_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Lista ubicaciones con filtro RBAC.

    - super_admin: ve todas
    - otros roles: solo locations en allowed_location_ids
    """
    query = filter_locations_by_permission(current_user, db)

    if location_group_id:
        query = query.filter(Location.location_group_id == location_group_id)

    locations = query.offset(skip).limit(limit).all()
    return locations


@router.post("/locations", response_model=LocationSchema, status_code=status.HTTP_201_CREATED, summary="Crear ubicación")
def create_location(
    data: LocationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "service_admin")),
):
    """Crea una nueva ubicación. Requiere rol admin."""
    # Verificar que el grupo existe
    group = db.query(LocationGroup).filter(LocationGroup.id == data.location_group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"LocationGroup con ID {data.location_group_id} no existe",
        )

    # Verificar code único si se provee
    if data.code:
        existing = db.query(Location).filter(Location.code == data.code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una ubicación con el código '{data.code}'",
            )

    loc = Location(**data.model_dump())
    db.add(loc)
    db.commit()
    db.refresh(loc)

    AuditService.log_from_request(
        db=db, request=request, action_type="LOCATION_CREATED",
        current_user=current_user, entity_type="location", entity_id=loc.id,
    )

    return loc


@router.get("/locations/{location_id}", response_model=LocationSchema, summary="Obtener ubicación por ID")
def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene una ubicación por ID. Verifica acceso RBAC."""
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ubicación no encontrada")

    require_location_access(current_user, location_id)
    return loc


@router.patch("/locations/{location_id}", response_model=LocationSchema, summary="Actualizar ubicación")
def update_location(
    location_id: int,
    data: LocationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "service_admin")),
):
    """Actualiza una ubicación. Requiere rol admin."""
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ubicación no encontrada")

    update_data = data.model_dump(exclude_unset=True)

    # Validar code único si se cambia
    if "code" in update_data and update_data["code"]:
        existing = db.query(Location).filter(
            Location.code == update_data["code"], Location.id != location_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una ubicación con el código '{update_data['code']}'",
            )

    for key, value in update_data.items():
        setattr(loc, key, value)

    db.commit()
    db.refresh(loc)

    AuditService.log_from_request(
        db=db, request=request, action_type="LOCATION_UPDATED",
        current_user=current_user, entity_type="location", entity_id=loc.id,
        changes={"after": update_data},
    )

    return loc


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar ubicación")
def delete_location(
    location_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    """Elimina una ubicación y sus assets en cascada. Solo super_admin."""
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ubicación no encontrada")

    AuditService.log_from_request(
        db=db, request=request, action_type="LOCATION_DELETED",
        current_user=current_user, entity_type="location", entity_id=loc.id,
        changes={"before": {"name": loc.name, "code": loc.code}},
    )

    db.delete(loc)
    db.commit()
