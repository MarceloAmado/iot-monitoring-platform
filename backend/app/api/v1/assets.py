"""
Endpoints de Assets (CRUD con RBAC).
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_role
from app.models.asset import Asset
from app.models.location import Location
from app.models.user import User
from app.core.permissions import (
    is_super_admin,
    has_location_access,
    require_location_access,
)
from app.schemas.asset import (
    Asset as AssetSchema,
    AssetCreate,
    AssetUpdate,
)
from app.services.audit_service import AuditService


router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("", response_model=List[AssetSchema], summary="Listar assets")
def list_assets(
    skip: int = 0,
    limit: int = 100,
    location_id: Optional[int] = Query(None, description="Filtrar por ubicación"),
    asset_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Lista assets con filtro RBAC.

    - super_admin: ve todos
    - otros roles: solo assets en locations permitidas
    """
    query = db.query(Asset)

    # Filtro RBAC
    if not is_super_admin(current_user):
        if current_user.allowed_location_ids:
            query = query.filter(Asset.location_id.in_(current_user.allowed_location_ids))
        else:
            query = query.filter(Asset.id == -1)

    if location_id:
        query = query.filter(Asset.location_id == location_id)

    if asset_type:
        query = query.filter(Asset.type == asset_type)

    assets = query.offset(skip).limit(limit).all()
    return assets


@router.post("", response_model=AssetSchema, status_code=status.HTTP_201_CREATED, summary="Crear asset")
def create_asset(
    data: AssetCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "service_admin")),
):
    """Crea un nuevo asset. Requiere rol admin."""
    # Verificar que la location existe
    loc = db.query(Location).filter(Location.id == data.location_id).first()
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Location con ID {data.location_id} no existe",
        )

    # Verificar acceso a la location (service_admin solo en sus locations)
    require_location_access(current_user, data.location_id)

    asset = Asset(**data.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)

    AuditService.log_from_request(
        db=db, request=request, action_type="ASSET_CREATED",
        current_user=current_user, entity_type="asset", entity_id=asset.id,
    )

    return asset


@router.get("/{asset_id}", response_model=AssetSchema, summary="Obtener asset por ID")
def get_asset(
    asset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene un asset por ID. Verifica acceso RBAC."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset no encontrado")

    require_location_access(current_user, asset.location_id)
    return asset


@router.patch("/{asset_id}", response_model=AssetSchema, summary="Actualizar asset")
def update_asset(
    asset_id: int,
    data: AssetUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin", "service_admin")),
):
    """Actualiza un asset. Requiere rol admin."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset no encontrado")

    update_data = data.model_dump(exclude_unset=True)

    # Si cambia location_id, verificar acceso a la nueva location
    if "location_id" in update_data:
        loc = db.query(Location).filter(Location.id == update_data["location_id"]).first()
        if not loc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Location con ID {update_data['location_id']} no existe",
            )
        require_location_access(current_user, update_data["location_id"])

    for key, value in update_data.items():
        setattr(asset, key, value)

    db.commit()
    db.refresh(asset)

    AuditService.log_from_request(
        db=db, request=request, action_type="ASSET_UPDATED",
        current_user=current_user, entity_type="asset", entity_id=asset.id,
        changes={"after": update_data},
    )

    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Eliminar asset")
def delete_asset(
    asset_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("super_admin")),
):
    """Elimina un asset y sus devices en cascada. Solo super_admin."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset no encontrado")

    AuditService.log_from_request(
        db=db, request=request, action_type="ASSET_DELETED",
        current_user=current_user, entity_type="asset", entity_id=asset.id,
        changes={"before": {"name": asset.name, "type": asset.type}},
    )

    db.delete(asset)
    db.commit()
