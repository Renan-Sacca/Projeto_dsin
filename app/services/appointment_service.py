import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserType
from app.models.service import Service
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.service_repository import ServiceRepository
from app.repositories.system_config_repository import SystemConfigRepository
from app.repositories.client_repository import ClientRepository
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AvailableSlotResponse,
    DashboardMetrics,
    RevenueChartResponse,
    RevenueChartItem,
)

logger = logging.getLogger(__name__)

OPENING_HOUR = 8
CLOSING_HOUR = 18
SLOT_INTERVAL_MINUTES = 15


class AppointmentService:
    def __init__(self, db: Session):
        self.db = db
        self.appt_repo = AppointmentRepository(db)
        self.service_repo = ServiceRepository(db)
        self.config_repo = SystemConfigRepository(db)
        self.client_repo = ClientRepository(db)


    def create_appointment(
        self, data: AppointmentCreate, user: User
    ) -> Appointment:

        if user.tipo == UserType.ADMIN and data.client_id:
            client = self.client_repo.get_by_id(data.client_id)
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cliente não encontrado.",
                )
        else:
            client = self.client_repo.get_by_user_id(user.id)
            if not client:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Usuário não possui perfil de cliente.",
                )

        services = self._validate_services(data.service_ids)
        total_duration = sum(s.duracao_minutos for s in services)

        appointment_dt = data.data_hora
        if appointment_dt.tzinfo is None:
            appointment_dt = appointment_dt.replace(tzinfo=timezone.utc)

        if appointment_dt <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A data do agendamento deve ser no futuro.",
            )

        config = self.config_repo.get()
        auto_approve = config.auto_approve_appointments if config else False

        if auto_approve:
            has_conflict = self.appt_repo.check_conflict(
                data_hora=data.data_hora,
                duration_minutes=total_duration,
            )
            if has_conflict:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Conflito de horário com outro agendamento aprovado.",
                )

        initial_status = (
            AppointmentStatus.APPROVED if auto_approve else AppointmentStatus.PENDING
        )

        appointment = Appointment(
            client_id=client.id,
            data_hora=data.data_hora,
            status=initial_status,
            criado_por=user.id,
            aprovado_por=user.id if auto_approve else None,
            data_aprovacao=datetime.now(timezone.utc) if auto_approve else None,
        )
        appointment = self.appt_repo.create(appointment)

        self.appt_repo.add_services(appointment.id, data.service_ids)

        if status == AppointmentStatus.APPROVED:
            self._sync_calendar(
                appointment=appointment,
                total_duration=total_duration,
                sync_client=data.add_to_google_calendar
            )
        else:
            if data.add_to_google_calendar:
                appointment.google_event_id_client = "WANTS_SYNC"
                self.appt_repo.db.commit()

        status_text = "aprovado automaticamente" if auto_approve else "pendente"
        logger.info(
            f"Agendamento #{appointment.id} criado ({status_text}) "
            f"para cliente #{client.id} em {data.data_hora}"
        )

        return self.appt_repo.get_by_id(appointment.id)


    def list_appointments(
        self,
        user: User,
        skip: int = 0,
        limit: int = 50,
        status_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        admin_client_id: Optional[int] = None,
    ) -> Tuple[List[Appointment], int]:
        appt_status = None
        if status_filter:
            try:
                appt_status = AppointmentStatus(status_filter)
            except ValueError:
                pass

        client_id = None
        if user.tipo == UserType.CLIENT:
            client = self.client_repo.get_by_user_id(user.id)
            if client:
                client_id = client.id
        elif admin_client_id:
            client_id = admin_client_id

        appointments = self.appt_repo.get_all(
            skip=skip, limit=limit, status=appt_status, client_id=client_id,
            date_from=date_from, date_to=date_to,
        )
        total = self.appt_repo.count(
            status=appt_status, client_id=client_id,
            date_from=date_from, date_to=date_to,
        )

        return appointments, total

    def get_appointment(self, appointment_id: int, user: User) -> Appointment:
        appointment = self.appt_repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado.",
            )

        if user.tipo == UserType.CLIENT:
            client = self.client_repo.get_by_user_id(user.id)
            if not client or appointment.client_id != client.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Você não tem permissão para acessar este agendamento.",
                )

        return appointment


    def update_appointment(
        self, appointment_id: int, data: AppointmentUpdate, user: User
    ) -> Appointment:

        appointment = self.get_appointment(appointment_id, user)

        if user.tipo == UserType.CLIENT:
            self._enforce_two_day_rule(appointment)

        if data.data_hora:
            update_dt = data.data_hora
            if update_dt.tzinfo is None:
                update_dt = update_dt.replace(tzinfo=timezone.utc)

            if update_dt <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A nova data deve ser no futuro.",
                )

            service_ids = data.service_ids or [
                s.service_id for s in appointment.services
            ]
            services = self._validate_services(service_ids)
            total_duration = sum(s.duracao_minutos for s in services)

            if appointment.status == AppointmentStatus.APPROVED:
                has_conflict = self.appt_repo.check_conflict(
                    data_hora=data.data_hora,
                    duration_minutes=total_duration,
                    exclude_id=appointment.id,
                )
                if has_conflict:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Conflito de horário com outro agendamento aprovado.",
                    )

            appointment.data_hora = data.data_hora

        if data.service_ids:
            self._validate_services(data.service_ids)
            self.appt_repo.clear_services(appointment.id)
            self.appt_repo.add_services(appointment.id, data.service_ids)

        if (data.data_hora or data.service_ids) and user.tipo == UserType.CLIENT:
            appointment.status = AppointmentStatus.PENDING
            appointment.aprovado_por = None
            appointment.data_aprovacao = None

        appointment = self.appt_repo.update(appointment)
        logger.info(
            f"Agendamento #{appointment_id} atualizado por usuário #{user.id}"
        )

        return self.appt_repo.get_by_id(appointment.id)


    def approve_appointment(
        self, appointment_id: int, admin: User
    ) -> Appointment:
        appointment = self.appt_repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado.",
            )

        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Só é possível aprovar agendamentos pendentes. Status atual: {appointment.status.value}",
            )

        total_duration = sum(
            s.service.duracao_minutos for s in appointment.services if s.service
        ) or 30

        has_conflict = self.appt_repo.check_conflict(
            data_hora=appointment.data_hora,
            duration_minutes=total_duration,
            exclude_id=appointment.id,
        )
        if has_conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflito de horário. Já existe um agendamento aprovado neste horário.",
            )

        appointment.status = AppointmentStatus.APPROVED
        appointment.aprovado_por = admin.id
        appointment.data_aprovacao = datetime.now(timezone.utc)

        appointment = self.appt_repo.update(appointment)
        
        wants_sync = (appointment.google_event_id_client == "WANTS_SYNC")
        self._sync_calendar(
            appointment=appointment,
            total_duration=total_duration,
            sync_client=wants_sync
        )

        logger.info(
            f"Agendamento #{appointment_id} APROVADO pelo admin #{admin.id} ({admin.nome})"
        )

        return self.appt_repo.get_by_id(appointment.id)

    def _sync_calendar(self, appointment: Appointment, total_duration: int, sync_client: bool = False):
        try:
            from app.services.google_calendar import GoogleCalendarService
            from app.routers.google_auth import get_client_secrets_file
            import json

            with open(get_client_secrets_file(), 'r') as f:
                creds_data = json.load(f)
                client_id = creds_data['web']['client_id']
                client_secret = creds_data['web']['client_secret']

            services_names = [s.service.nome for s in appointment.services if s.service]
            title = f"Agendamento Confirmado: {', '.join(services_names)}"
            description = f"Agendamento com {appointment.client.user.nome} ({appointment.client.telefone})"
            end_time = appointment.data_hora + timedelta(minutes=total_duration)

            admin_user = self.db.query(User).filter(User.tipo == UserType.ADMIN, User.google_refresh_token.isnot(None)).first()
            if admin_user and admin_user.google_access_token and not (appointment.google_event_id_admin and appointment.google_event_id_admin != "WANTS_SYNC"):
                try:
                    gc_admin = GoogleCalendarService(
                        access_token=admin_user.google_access_token,
                        refresh_token=admin_user.google_refresh_token,
                        token_expiry=admin_user.google_token_expiry,
                        client_id=client_id,
                        client_secret=client_secret
                    )
                    event_id = gc_admin.create_event(title, description, appointment.data_hora, end_time, add_alarm=False)
                    if event_id:
                        appointment.google_event_id_admin = event_id
                except Exception as e:
                    logger.error(f"Erro ao criar evento no calendário do Admin: {e}")

            client_user = appointment.client.user
            if sync_client and client_user.google_access_token and client_user.google_refresh_token:
                try:
                    gc_client = GoogleCalendarService(
                        access_token=client_user.google_access_token,
                        refresh_token=client_user.google_refresh_token,
                        token_expiry=client_user.google_token_expiry,
                        client_id=client_id,
                        client_secret=client_secret
                    )
                    event_id = gc_client.create_event(title, description, appointment.data_hora, end_time, add_alarm=True)
                    if event_id:
                        appointment.google_event_id_client = event_id
                except Exception as e:
                    logger.error(f"Erro ao criar evento no calendário do Cliente: {e}")
            elif sync_client and appointment.google_event_id_client == "WANTS_SYNC":
                appointment.google_event_id_client = None

            self.appt_repo.db.commit()
        except Exception as e:
            logger.error(f"Erro geral na integração com Google Calendar: {e}")

    def reject_appointment(
        self, appointment_id: int, admin: User
    ) -> Appointment:
        appointment = self.appt_repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado.",
            )

        if appointment.status != AppointmentStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Só é possível rejeitar agendamentos pendentes. Status atual: {appointment.status.value}",
            )

        appointment.status = AppointmentStatus.REJECTED
        appointment.aprovado_por = admin.id
        appointment.data_aprovacao = datetime.now(timezone.utc)

        appointment = self.appt_repo.update(appointment)

        logger.info(
            f"Agendamento #{appointment_id} REJEITADO pelo admin #{admin.id} ({admin.nome})"
        )

        return self.appt_repo.get_by_id(appointment.id)

    def cancel_appointment(
        self, appointment_id: int, user: User
    ) -> Appointment:
        appointment = self.get_appointment(appointment_id, user)

        if appointment.status in [
            AppointmentStatus.CANCELLED,
            AppointmentStatus.COMPLETED,
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Não é possível cancelar um agendamento {appointment.status.value}.",
            )

        if user.tipo == UserType.CLIENT:
            self._enforce_two_day_rule(appointment)

        appointment.status = AppointmentStatus.CANCELLED

        appointment = self.appt_repo.update(appointment)

        logger.info(
            f"Agendamento #{appointment_id} CANCELADO por usuário #{user.id}"
        )

        return self.appt_repo.get_by_id(appointment.id)

    def complete_appointment(
        self, appointment_id: int, admin: User
    ) -> Appointment:
        appointment = self.appt_repo.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado.",
            )

        if appointment.status != AppointmentStatus.APPROVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Só é possível concluir agendamentos aprovados.",
            )

        appointment.status = AppointmentStatus.COMPLETED
        appointment = self.appt_repo.update(appointment)

        logger.info(f"Agendamento #{appointment_id} CONCLUÍDO pelo admin #{admin.id}")

        return self.appt_repo.get_by_id(appointment.id)


    def check_existing_appointments_in_week(self, user: User, date: datetime) -> Optional[Appointment]:

        client = self.client_repo.get_by_user_id(user.id)
        if not client:
            return None

        start_of_week = date - timedelta(days=date.weekday())
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0)
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

        appointments = self.appt_repo.get_all(
            client_id=client.id,
            date_from=start_of_week,
            date_to=end_of_week,
        )
        
        active_appts = [a for a in appointments if a.status not in [AppointmentStatus.CANCELLED, AppointmentStatus.REJECTED]]
        
        return active_appts[0] if active_appts else None


    def get_available_slots(self, date: datetime, service_duration: int = 15) -> List[AvailableSlotResponse]:
        slots = []
        current = date.replace(hour=OPENING_HOUR, minute=0, second=0, microsecond=0)
        end = date.replace(hour=CLOSING_HOUR, minute=0, second=0, microsecond=0)
        now = datetime.now(timezone.utc)

        approved = self.appt_repo.get_approved_for_date(date)

        busy_intervals = []
        for appt in approved:
            duration = sum(
                s.service.duracao_minutos for s in appt.services if s.service
            ) or 15
            appt_end = appt.data_hora + timedelta(minutes=duration)
            busy_intervals.append((appt.data_hora, appt_end))

        while current < end:
            service_end = current + timedelta(minutes=service_duration)
            current_aware = current.replace(tzinfo=timezone.utc) if not current.tzinfo else current
            is_available = current_aware > now

            if is_available and service_end > end:
                is_available = False

            if is_available:
                for busy_start, busy_end in busy_intervals:
                    bs = busy_start.replace(tzinfo=None) if busy_start.tzinfo else busy_start
                    be = busy_end.replace(tzinfo=None) if busy_end.tzinfo else busy_end
                    cs = current.replace(tzinfo=None) if current.tzinfo else current
                    se = service_end.replace(tzinfo=None) if service_end.tzinfo else service_end

                    if cs < be and se > bs:
                        is_available = False
                        break

            slots.append(
                AvailableSlotResponse(
                    data_hora=current,
                    disponivel=is_available,
                )
            )
            current += timedelta(minutes=SLOT_INTERVAL_MINUTES)

        return slots


    def get_dashboard_metrics(self) -> DashboardMetrics:
        status_counts = self.appt_repo.count_by_status()
        total = sum(status_counts.values())

        return DashboardMetrics(
            total_agendamentos=total,
            pendentes=status_counts.get("PENDING", 0),
            aprovados=status_counts.get("APPROVED", 0),
            rejeitados=status_counts.get("REJECTED", 0),
            cancelados=status_counts.get("CANCELLED", 0),
            completados=status_counts.get("COMPLETED", 0),
            total_clientes=self.client_repo.count(),
            total_servicos=self.service_repo.count(only_active=True),
            receita_estimada=self.appt_repo.get_estimated_revenue(),
            agendamentos_hoje=self.appt_repo.count_today(),
        )

    def get_revenue_chart_data(
        self,
        period: str = "monthly",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        service_id: Optional[int] = None,
        status_filter: Optional[str] = None
    ) -> RevenueChartResponse:
        raw_data = self.appt_repo.get_revenue_data(
            date_from=date_from,
            date_to=date_to,
            service_id=service_id,
            status_filter=status_filter
        )

        from collections import defaultdict
        grouped = defaultdict(lambda: {"estimated": 0.0, "paid": 0.0})

        total_estimated = 0.0
        total_paid = 0.0

        for dt, status, preco in raw_data:
            if period == "daily":
                label = dt.strftime("%Y-%m-%d")
            else:
                label = dt.strftime("%Y-%m")


            if status == AppointmentStatus.COMPLETED.value:
                grouped[label]["paid"] += preco
                total_paid += preco
            else:
                grouped[label]["estimated"] += preco
                total_estimated += preco

        sorted_labels = sorted(grouped.keys())

        items = []
        for label in sorted_labels:
            items.append(RevenueChartItem(
                label=label,
                estimated_revenue=grouped[label]["estimated"],
                paid_revenue=grouped[label]["paid"]
            ))

        return RevenueChartResponse(
            items=items,
            total_estimated=total_estimated,
            total_paid=total_paid
        )


    def _validate_services(self, service_ids: List[int]) -> List[Service]:
        if not service_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="É necessário selecionar pelo menos um serviço.",
            )

        services = []
        for sid in service_ids:
            service = self.service_repo.get_by_id(sid)
            if not service:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Serviço com ID {sid} não encontrado.",
                )
            if not service.ativo:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Serviço '{service.nome}' está desativado.",
                )
            services.append(service)

        return services

    def _enforce_two_day_rule(self, appointment: Appointment) -> None:
        now = datetime.now(timezone.utc)
        appt_time = appointment.data_hora
        if appt_time.tzinfo is None:
            appt_time = appt_time.replace(tzinfo=timezone.utc)

        diff = appt_time - now
        if diff < timedelta(days=2):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível editar/cancelar agendamentos com menos de 2 dias de antecedência.",
            )
