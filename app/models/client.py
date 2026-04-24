
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    telefone = Column(String(20), nullable=True)

    user = relationship("User", back_populates="client")
    appointments = relationship("Appointment", back_populates="client")

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, user_id={self.user_id})>"
