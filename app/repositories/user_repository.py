import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.user import User, UserType

logger = logging.getLogger(__name__)


class UserRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        tipo: Optional[UserType] = None,
    ) -> List[User]:
        query = self.db.query(User)
        if tipo:
            query = query.filter(User.tipo == tipo)
        return query.offset(skip).limit(limit).all()

    def count(self, tipo: Optional[UserType] = None) -> int:
        query = self.db.query(User)
        if tipo:
            query = query.filter(User.tipo == tipo)
        return query.count()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"Usuário criado: id={user.id}, email={user.email}")
        return user

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        logger.info(f"Usuário atualizado: id={user.id}")
        return user
