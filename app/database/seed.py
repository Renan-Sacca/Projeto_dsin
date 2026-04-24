"""
Seed do banco de dados.
Cria o admin padrão e a configuração inicial do sistema.
"""

import logging
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.models.user import User, UserType
from app.models.system_config import SystemConfig

logger = logging.getLogger(__name__)
settings = get_settings()


def seed_database(db: Session) -> None:
    """Popula o banco de dados com dados iniciais."""
    _seed_admin(db)
    _seed_system_config(db)
    db.commit()
    logger.info("Seed do banco de dados concluído com sucesso.")


def _seed_admin(db: Session) -> None:
    """Cria o usuário administrador padrão se não existir."""
    admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
    if admin is None:
        admin = User(
            nome=settings.ADMIN_NAME,
            email=settings.ADMIN_EMAIL,
            senha_hash=hash_password(settings.ADMIN_PASSWORD),
            tipo=UserType.ADMIN,
            ativo=True,
        )
        db.add(admin)
        db.flush()
        logger.info(f"Admin padrão criado: {settings.ADMIN_EMAIL}")
    else:
        logger.info("Admin padrão já existe, pulando seed.")


def _seed_system_config(db: Session) -> None:
    """Cria a configuração padrão do sistema se não existir."""
    config = db.query(SystemConfig).first()
    if config is None:
        config = SystemConfig(auto_approve_appointments=False)
        db.add(config)
        logger.info("Configuração do sistema criada com aprovação manual.")
    else:
        logger.info("Configuração do sistema já existe, pulando seed.")
