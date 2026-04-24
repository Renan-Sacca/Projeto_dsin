import logging
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload

from app.models.client import Client
from app.models.user import User

logger = logging.getLogger(__name__)


class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, client_id: int) -> Optional[Client]:
        return (
            self.db.query(Client)
            .options(joinedload(Client.user))
            .filter(Client.id == client_id)
            .first()
        )

    def get_by_user_id(self, user_id: int) -> Optional[Client]:
        return (
            self.db.query(Client)
            .options(joinedload(Client.user))
            .filter(Client.user_id == user_id)
            .first()
        )

    def get_all(self, skip: int = 0, limit: int = 50, search: str = None) -> List[Client]:
        query = self.db.query(Client).options(joinedload(Client.user)).join(User)
        if search:
            query = query.filter(
                (User.nome.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
            )
        return query.offset(skip).limit(limit).all()

    def count(self, search: str = None) -> int:
        query = self.db.query(Client).join(User)
        if search:
            query = query.filter(
                (User.nome.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%"))
            )
        return query.count()

    def create(self, client: Client) -> Client:
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        logger.info(f"Cliente criado: id={client.id}, user_id={client.user_id}")
        return client

    def update(self, client: Client) -> Client:
        self.db.commit()
        self.db.refresh(client)
        logger.info(f"Cliente atualizado: id={client.id}")
        return client
