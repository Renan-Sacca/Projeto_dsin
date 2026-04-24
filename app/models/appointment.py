import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Enum
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class AppointmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    data_hora = Column(DateTime, nullable=False, index=True)
    status = Column(
        Enum(AppointmentStatus),
        default=AppointmentStatus.PENDING,
        nullable=False,
    )
    criado_por = Column(Integer, ForeignKey("users.id"), nullable=False)
    aprovado_por = Column(Integer, ForeignKey("users.id"), nullable=True)
    data_aprovacao = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    atualizado_em = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    google_event_id_client = Column(String(255), nullable=True)
    google_event_id_admin = Column(String(255), nullable=True)

    client = relationship("Client", back_populates="appointments")
    approver = relationship(
        "User",
        back_populates="approved_appointments",
        foreign_keys=[aprovado_por],
    )
    creator = relationship("User", foreign_keys=[criado_por])
    services = relationship("AppointmentService", back_populates="appointment", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Appointment(id={self.id}, status='{self.status}', data_hora='{self.data_hora}')>"


class AppointmentService(Base):
    __tablename__ = "appointment_services"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)

    appointment = relationship("Appointment", back_populates="services")
    service = relationship("Service", back_populates="appointment_services")

    def __repr__(self) -> str:
        return f"<AppointmentService(appointment_id={self.appointment_id}, service_id={self.service_id})>"
