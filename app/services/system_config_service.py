import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig
from app.repositories.system_config_repository import SystemConfigRepository
from app.schemas.system_config import SystemConfigUpdate

logger = logging.getLogger(__name__)


class SystemConfigService:
    def __init__(self, db: Session):
        self.db = db
        self.config_repo = SystemConfigRepository(db)

    def get_config(self) -> SystemConfig:
        config = self.config_repo.get()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configuração do sistema não encontrada.",
            )
        return config

    def update_config(self, data: SystemConfigUpdate) -> SystemConfig:
        config = self.get_config()
        old_value = config.auto_approve_appointments
        config.auto_approve_appointments = data.auto_approve_appointments
        config = self.config_repo.update(config)

        logger.info(
            f"Configuração atualizada: auto_approve {old_value} → {data.auto_approve_appointments}"
        )

        return config
