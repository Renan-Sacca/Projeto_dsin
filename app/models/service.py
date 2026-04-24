
from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class Service(Base):

    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    descricao = Column(Text, nullable=True)
    duracao_minutos = Column(Integer, nullable=False)
    preco = Column(Float, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

    appointment_services = relationship("AppointmentService", back_populates="service")

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, nome='{self.nome}', preco={self.preco})>"
