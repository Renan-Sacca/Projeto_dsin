import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.service import Service

logger = logging.getLogger(__name__)


class ServiceRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, service_id: int) -> Optional[Service]:
        return self.db.query(Service).filter(Service.id == service_id).first()

    def get_active(self, skip: int = 0, limit: int = 50, search: str = None) -> List[Service]:
        query = self.db.query(Service).filter(Service.ativo == True)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                Service.nome.ilike(pattern) | Service.descricao.ilike(pattern)
            )
        return query.offset(skip).limit(limit).all()

    def get_all(self, skip: int = 0, limit: int = 50, search: str = None) -> List[Service]:
        query = self.db.query(Service)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                Service.nome.ilike(pattern) | Service.descricao.ilike(pattern)
            )
        return query.offset(skip).limit(limit).all()

    def count(self, only_active: bool = False, search: str = None) -> int:
        query = self.db.query(Service)
        if only_active:
            query = query.filter(Service.ativo == True)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                Service.nome.ilike(pattern) | Service.descricao.ilike(pattern)
            )
        return query.count()

    def create(self, service: Service) -> Service:
        self.db.add(service)
        self.db.commit()
        self.db.refresh(service)
        logger.info(f"Serviço criado: id={service.id}, nome={service.nome}")
        return service

    def update(self, service: Service) -> Service:
        self.db.commit()
        self.db.refresh(service)
        logger.info(f"Serviço atualizado: id={service.id}")
        return service
