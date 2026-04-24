import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.connection import get_db
from app.models.user import User, UserType
from app.repositories.user_repository import UserRepository
from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

security = HTTPBearer(auto_error=False)


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = None

    if credentials:
        token = credentials.credentials

    if not token:
        token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: sem identificação do usuário.",
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(int(user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )

    if not user.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada.",
        )

    return user


def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    try:
        return get_current_user(request, credentials, db)
    except HTTPException:
        return None


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.tipo != UserType.ADMIN:
        logger.warning(
            f"Acesso admin negado para usuário #{current_user.id} ({current_user.tipo})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return current_user


def require_client(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.tipo != UserType.CLIENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a clientes.",
        )
    return current_user


def require_super_admin(
    current_user: User = Depends(require_admin),
) -> User:
    if current_user.email != settings.ADMIN_EMAIL:
        logger.warning(
            f"Acesso Super Admin negado para usuário #{current_user.id} ({current_user.email})"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita ao Administrador Principal.",
        )
    return current_user
