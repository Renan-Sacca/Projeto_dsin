from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import require_super_admin
from app.models.user import User
from app.schemas.system_config import SystemConfigUpdate, SystemConfigResponse
from app.services.system_config_service import SystemConfigService

router = APIRouter(prefix="/api/config", tags=["Configuração"])


@router.get("", response_model=SystemConfigResponse)
def get_config(
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    service = SystemConfigService(db)
    return service.get_config()


@router.put("", response_model=SystemConfigResponse)
def update_config(
    data: SystemConfigUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    service = SystemConfigService(db)
    return service.update_config(data)
