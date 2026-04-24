from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_admin, get_current_user
from app.models.user import User
from app.schemas.service import ServiceCreate, ServiceUpdate, ServiceResponse, ServiceListResponse
from app.services.service_service import ServiceService

router = APIRouter(prefix="/api/services", tags=["Serviços"])


@router.get("")
def list_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    only_active: bool = Query(True),
    search: str = Query(None, description="Busca por nome ou descrição"),
    db: Session = Depends(get_db),
):
    service = ServiceService(db)
    services, total = service.list_services(
        skip=skip, limit=limit, only_active=only_active, search=search,
    )
    return ServiceListResponse(items=services, total=total, skip=skip, limit=limit)


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
):
    service = ServiceService(db)
    return service.get_service_by_id(service_id)


@router.post("", response_model=ServiceResponse, status_code=201)
def create_service(
    data: ServiceCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = ServiceService(db)
    return service.create_service(data)


@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: int,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = ServiceService(db)
    return service.update_service(service_id, data)
