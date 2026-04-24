import logging
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserType
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def get_user_by_id(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado.",
            )
        return user

    def list_users(
        self, skip: int = 0, limit: int = 50, tipo: str = None
    ) -> List[User]:
        user_type = None
        if tipo:
            try:
                user_type = UserType(tipo)
            except ValueError:
                pass
        return self.user_repo.get_all(skip=skip, limit=limit, tipo=user_type)

    def count_users(self, tipo: str = None) -> int:
        user_type = None
        if tipo:
            try:
                user_type = UserType(tipo)
            except ValueError:
                pass
        return self.user_repo.count(tipo=user_type)
