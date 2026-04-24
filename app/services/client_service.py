import logging
from typing import List, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.user import User, UserType
from app.core.security import hash_password
from app.repositories.client_repository import ClientRepository
from app.repositories.user_repository import UserRepository
from app.schemas.client import ClientUpdate
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)


class ClientService:
    def __init__(self, db: Session):
        self.db = db
        self.client_repo = ClientRepository(db)
        self.user_repo = UserRepository(db)

    def create_client(self, data: UserCreate) -> Client:
        existing = self.user_repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado.",
            )

        user = User(
            nome=data.nome,
            email=data.email,
            senha_hash=hash_password(data.senha or "leila123"),
            tipo=UserType.CLIENT,
            ativo=True,
        )
        user = self.user_repo.create(user)

        client = Client(
            user_id=user.id,
            telefone=data.telefone,
        )
        return self.client_repo.create(client)

    def get_client_by_id(self, client_id: int) -> Client:
        client = self.client_repo.get_by_id(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado.",
            )
        return client

    def get_client_by_user_id(self, user_id: int) -> Client:
        client = self.client_repo.get_by_user_id(user_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente não encontrado para este usuário.",
            )
        return client

    def list_clients(self, skip: int = 0, limit: int = 50, search: str = None) -> Tuple[List[Client], int]:
        clients = self.client_repo.get_all(skip=skip, limit=limit, search=search)
        total = self.client_repo.count(search=search)
        return clients, total

    def update_client(self, client_id: int, data: ClientUpdate) -> Client:
        client = self.get_client_by_id(client_id)
        user = client.user

        if data.telefone is not None:
            client.telefone = data.telefone
        if data.nome is not None:
            user.nome = data.nome
        if data.email is not None:
            existing = self.user_repo.get_by_email(data.email)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email já está em uso.",
                )
            user.email = data.email
        if data.ativo is not None:
            user.ativo = data.ativo
            action = "ativado" if data.ativo else "desativado"
            logger.info(f"Cliente {client_id} {action}")

        self.user_repo.update(user)
        self.client_repo.update(client)
        return client

    def promote_to_admin(self, client_id: int) -> Client:
        client = self.get_client_by_id(client_id)
        user = client.user
        user.tipo = UserType.ADMIN
        self.user_repo.update(user)
        logger.info(f"Usuário #{user.id} promovido a ADMIN")
        return client

    def demote_to_client(self, client_id: int) -> Client:
        client = self.get_client_by_id(client_id)
        user = client.user
        user.tipo = UserType.CLIENT
        self.user_repo.update(user)
        logger.info(f"Usuário #{user.id} rebaixado a CLIENT")
        return client
