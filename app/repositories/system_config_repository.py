import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)


class SystemConfigRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self) -> Optional[SystemConfig]:
        return self.db.query(SystemConfig).first()

    def update(self, config: SystemConfig) -> SystemConfig:
        self.db.commit()
        self.db.refresh(config)
        logger.info(
            f"Configuração atualizada: auto_approve={config.auto_approve_appointments}"
        )
        return config
