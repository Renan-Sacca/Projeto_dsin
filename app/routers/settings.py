from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.dependencies.auth import require_super_admin
from app.models.user import User
from app.repositories.system_config_repository import SystemConfigRepository
from app.models.system_config import SystemConfig
from app.schemas.system_config import SystemConfigResponse, SystemConfigUpdate

router = APIRouter(prefix="/api/settings", tags=["Configurações"])

@router.get("", response_model=SystemConfigResponse)
def get_settings(
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    repo = SystemConfigRepository(db)
    config = repo.get()
    if not config:
        config = SystemConfig(auto_approve_appointments=False)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

@router.put("", response_model=SystemConfigResponse)
def update_settings(
    data: SystemConfigUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin)
):
    repo = SystemConfigRepository(db)
    config = repo.get()
    if not config:
        config = SystemConfig()
        db.add(config)
    
    config.auto_approve_appointments = data.auto_approve_appointments
    return repo.update(config)
