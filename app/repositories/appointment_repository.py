import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from app.models.appointment import Appointment, AppointmentService, AppointmentStatus
from app.models.service import Service

logger = logging.getLogger(__name__)


class AppointmentRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, appointment_id: int) -> Optional[Appointment]:
        return (
            self.db.query(Appointment)
            .options(
                joinedload(Appointment.services).joinedload(AppointmentService.service),
                joinedload(Appointment.client),
                joinedload(Appointment.approver),
                joinedload(Appointment.creator),
            )
            .filter(Appointment.id == appointment_id)
            .first()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[AppointmentStatus] = None,
        client_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> List[Appointment]:
        query = (
            self.db.query(Appointment)
            .options(
                joinedload(Appointment.services).joinedload(AppointmentService.service),
                joinedload(Appointment.client),
                joinedload(Appointment.approver),
                joinedload(Appointment.creator),
            )
        )
        if status:
            query = query.filter(Appointment.status == status)
        if client_id:
            query = query.filter(Appointment.client_id == client_id)
        if date_from:
            query = query.filter(Appointment.data_hora >= date_from)
        if date_to:
            end_of_day = date_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Appointment.data_hora <= end_of_day)
        return query.order_by(Appointment.data_hora.desc()).offset(skip).limit(limit).all()

    def count(
        self,
        status: Optional[AppointmentStatus] = None,
        client_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ) -> int:
        query = self.db.query(Appointment)
        if status:
            query = query.filter(Appointment.status == status)
        if client_id:
            query = query.filter(Appointment.client_id == client_id)
        if date_from:
            query = query.filter(Appointment.data_hora >= date_from)
        if date_to:
            end_of_day = date_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Appointment.data_hora <= end_of_day)
        return query.count()

    def check_conflict(
        self,
        data_hora: datetime,
        duration_minutes: int,
        exclude_id: Optional[int] = None,
    ) -> bool:
        start_time = data_hora
        end_time = data_hora + timedelta(minutes=duration_minutes)

        query = self.db.query(Appointment).filter(
            Appointment.status == AppointmentStatus.APPROVED,
        )

        if exclude_id:
            query = query.filter(Appointment.id != exclude_id)

        approved = query.all()
        for appt in approved:
            appt_duration = self._get_appointment_duration(appt.id)
            appt_start = appt.data_hora
            appt_end = appt.data_hora + timedelta(minutes=appt_duration)

            if start_time < appt_end and end_time > appt_start:
                return True

        return False

    def _get_appointment_duration(self, appointment_id: int) -> int:
        result = (
            self.db.query(func.sum(Service.duracao_minutos))
            .join(AppointmentService, AppointmentService.service_id == Service.id)
            .filter(AppointmentService.appointment_id == appointment_id)
            .scalar()
        )
        return result or 30

    def get_approved_for_date(self, date: datetime) -> List[Appointment]:
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        return (
            self.db.query(Appointment)
            .options(
                joinedload(Appointment.services).joinedload(AppointmentService.service),
            )
            .filter(
                Appointment.status == AppointmentStatus.APPROVED,
                Appointment.data_hora >= start,
                Appointment.data_hora <= end,
            )
            .order_by(Appointment.data_hora)
            .all()
        )

    def count_by_status(self) -> dict:
        results = (
            self.db.query(Appointment.status, func.count(Appointment.id))
            .group_by(Appointment.status)
            .all()
        )
        counts = {status.value: 0 for status in AppointmentStatus}
        for status, count in results:
            counts[status.value] = count
        return counts

    def count_today(self) -> int:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return (
            self.db.query(Appointment)
            .filter(
                Appointment.data_hora >= today,
                Appointment.data_hora < tomorrow,
            )
            .count()
        )

    def get_estimated_revenue(self) -> float:
        result = (
            self.db.query(func.sum(Service.preco))
            .join(AppointmentService, AppointmentService.service_id == Service.id)
            .join(Appointment, Appointment.id == AppointmentService.appointment_id)
            .filter(
                Appointment.status.in_([
                    AppointmentStatus.PENDING,
                    AppointmentStatus.APPROVED,
                    AppointmentStatus.COMPLETED,
                ])
            )
            .scalar()
        )
        return result or 0.0

    def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        logger.info(
            f"Agendamento criado: id={appointment.id}, "
            f"client_id={appointment.client_id}, status={appointment.status}"
        )
        return appointment

    def add_services(self, appointment_id: int, service_ids: List[int]) -> None:
        for sid in service_ids:
            appt_service = AppointmentService(
                appointment_id=appointment_id,
                service_id=sid,
            )
            self.db.add(appt_service)
        self.db.commit()

    def clear_services(self, appointment_id: int) -> None:
        self.db.query(AppointmentService).filter(
            AppointmentService.appointment_id == appointment_id
        ).delete()
        self.db.commit()

    def update(self, appointment: Appointment) -> Appointment:
        self.db.commit()
        self.db.refresh(appointment)
        logger.info(
            f"Agendamento atualizado: id={appointment.id}, status={appointment.status}"
        )
        return appointment

    def get_revenue_data(
        self,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        service_id: Optional[int] = None,
        status_filter: Optional[str] = None
    ) -> List[Tuple[datetime, str, float]]:
        query = (
            self.db.query(Appointment.data_hora, Appointment.status, Service.preco)
            .join(AppointmentService, AppointmentService.appointment_id == Appointment.id)
            .join(Service, Service.id == AppointmentService.service_id)
        )

        valid_statuses = [
            AppointmentStatus.PENDING,
            AppointmentStatus.APPROVED,
            AppointmentStatus.COMPLETED
        ]

        if status_filter:
            try:
                s = AppointmentStatus(status_filter)
                if s in valid_statuses:
                    query = query.filter(Appointment.status == s)
                else:
                    return []
            except ValueError:
                pass
        else:
            query = query.filter(Appointment.status.in_(valid_statuses))

        if date_from:
            query = query.filter(Appointment.data_hora >= date_from)
        if date_to:
            end_of_day = date_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Appointment.data_hora <= end_of_day)
        
        if service_id:
            query = query.filter(Service.id == service_id)

        results = query.all()
        return results
