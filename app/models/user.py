import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, Enum, DateTime
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class UserType(str, enum.Enum):
    CLIENT = "CLIENT"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    tipo = Column(Enum(UserType), default=UserType.CLIENT, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    atualizado_em = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    google_access_token = Column(String(2048), nullable=True)
    google_refresh_token = Column(String(2048), nullable=True)
    google_token_expiry = Column(DateTime, nullable=True)

    client = relationship("Client", back_populates="user", uselist=False)
    approved_appointments = relationship(
        "Appointment",
        back_populates="approver",
        foreign_keys="Appointment.aprovado_por",
    )

    @property
    def has_google_calendar(self) -> bool:
        return bool(self.google_refresh_token)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', tipo='{self.tipo}')>"
