import logging
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, UserType
from app.models.client import Client
from app.repositories.user_repository import UserRepository
from app.repositories.client_repository import ClientRepository
from app.schemas.user import UserCreate, UserLogin, TokenResponse, UserResponse

logger = logging.getLogger(__name__)


class AuthService:

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.client_repo = ClientRepository(db)

    def register(self, data: UserCreate) -> TokenResponse:
        existing = self.user_repo.get_by_email(data.email)
        if existing:
            logger.warning(f"Tentativa de registro com email duplicado: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado.",
            )

        user = User(
            nome=data.nome,
            email=data.email,
            senha_hash=hash_password(data.senha),
            tipo=UserType.CLIENT,
            ativo=True,
        )
        user = self.user_repo.create(user)

        client = Client(
            user_id=user.id,
            telefone=data.telefone,
        )
        self.client_repo.create(client)

        token = create_access_token(
            data={"sub": str(user.id), "tipo": user.tipo.value}
        )

        logger.info(f"Novo cliente registrado: id={user.id}, email={user.email}")

        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    def login(self, data: UserLogin) -> TokenResponse:
        user = self.user_repo.get_by_email(data.email)

        if not user or not verify_password(data.senha, user.senha_hash):
            logger.warning(f"Tentativa de login com credenciais inválidas: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos.",
            )
            
        if user.tipo == UserType.ADMIN:
            logger.warning(f"Tentativa de login por senha de Admin: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administradores devem fazer login exclusivamente com o Google.",
            )

        if not user.ativo:
            logger.warning(f"Tentativa de login de usuário inativo: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conta desativada. Entre em contato com o administrador.",
            )

        token = create_access_token(
            data={"sub": str(user.id), "tipo": user.tipo.value}
        )

        logger.info(f"Login bem-sucedido: id={user.id}, email={user.email}")

        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )

    def forgot_password(self, email: str):
        user = self.user_repo.get_by_email(email)
        if not user:
            return True
        
        from datetime import timedelta
        reset_token = create_access_token(
            data={"sub": str(user.id), "scope": "reset_password"},
            expires_delta=timedelta(minutes=15)
        )
        
        from app.services.email_service import EmailService
        return EmailService.send_reset_password_email(user.email, reset_token)

    def reset_password(self, token: str, new_password: str):
        from app.core.security import decode_token
        payload = decode_token(token)
        
        if not payload or payload.get("scope") != "reset_password":
            raise HTTPException(status_code=400, detail="Token inválido ou expirado.")
        
        user_id = payload.get("sub")
        user = self.user_repo.get_by_id(int(user_id))
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
        user.senha_hash = hash_password(new_password)
        self.user_repo.update(user)
        logger.info(f"Senha do usuário #{user.id} redefinida com sucesso.")
        return True
