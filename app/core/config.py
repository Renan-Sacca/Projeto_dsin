"""
Configurações centrais da aplicação.
Usa pydantic-settings para carregar variáveis de ambiente.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configurações da aplicação carregadas do .env"""

    # Segurança
    SECRET_KEY: str = "cabeleleila-leila-default-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Banco de dados
    DATABASE_URL: str = "sqlite:///./data/cabeleleila.db"

    # Admin padrão
    ADMIN_EMAIL: str = "admin@admin.com"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_NAME: str = "Administrador"

    # E-mail (Gmail)
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "Cabeleleila Leila <noreply@cabeleleilaleila.com>"

    # App
    APP_NAME: str = "Cabeleleila Leila"
    APP_VERSION: str = "1.0.0"
    FRONTEND_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()
