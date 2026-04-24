import logging
from typing import List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.service import Service
from app.repositories.service_repository import ServiceRepository
from app.schemas.service import ServiceCreate, ServiceUpdate

logger = logging.getLogger(__name__)


class ServiceService:
    def __init__(self, db: Session):
        self.db = db
        self.service_repo = ServiceRepository(db)

    def get_service_by_id(self, service_id: int) -> Service:
        service = self.service_repo.get_by_id(service_id)
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Serviço não encontrado.",
            )
        return service

    def list_services(
        self, skip: int = 0, limit: int = 50, only_active: bool = False,
        search: str = None,
    ) -> Tuple[List[Service], int]:
        if only_active:
            services = self.service_repo.get_active(skip=skip, limit=limit, search=search)
        else:
            services = self.service_repo.get_all(skip=skip, limit=limit, search=search)
        total = self.service_repo.count(only_active=only_active, search=search)
        return services, total

    def create_service(self, data: ServiceCreate) -> Service:
        service = Service(
            nome=data.nome,
            descricao=data.descricao,
            duracao_minutos=data.duracao_minutos,
            preco=data.preco,
            ativo=True,
        )
        return self.service_repo.create(service)

    def update_service(self, service_id: int, data: ServiceUpdate) -> Service:
        service = self.get_service_by_id(service_id)

        if data.nome is not None:
            service.nome = data.nome
        if data.descricao is not None:
            service.descricao = data.descricao
        if data.duracao_minutos is not None:
            service.duracao_minutos = data.duracao_minutos
        if data.preco is not None:
            service.preco = data.preco
        if data.ativo is not None:
            service.ativo = data.ativo
            action = "ativado" if data.ativo else "desativado"
            logger.info(f"Serviço {service_id} ({service.nome}) {action}")

        return self.service_repo.update(service)
