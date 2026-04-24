from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_admin, require_super_admin
from app.models.user import User
from app.schemas.client import ClientResponse, ClientUpdate
from app.schemas.user import UserCreate
from app.services.client_service import ClientService

router = APIRouter(prefix="/api/clients", tags=["Clientes"])


@router.post("/{client_id}/promote", response_model=ClientResponse)
def promote_client(
    client_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    service = ClientService(db)
    return service.promote_to_admin(client_id)


@router.post("/{client_id}/demote", response_model=ClientResponse)
def demote_client(
    client_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    service = ClientService(db)
    return service.demote_to_client(client_id)


@router.post("", response_model=ClientResponse)
def create_client(
    data: UserCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = ClientService(db)
    return service.create_client(data)


from app.schemas.client import ClientResponse, ClientUpdate, ClientListResponse

@router.get("", response_model=ClientListResponse)
def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    search: str = Query(None, description="Busca por nome ou email"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = ClientService(db)
    clients, total = service.list_clients(skip=skip, limit=limit, search=search)
    return ClientListResponse(items=clients, total=total, skip=skip, limit=limit)


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = ClientService(db)
    return service.get_client_by_id(client_id)


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = ClientService(db)
    return service.update_client(client_id, data)
