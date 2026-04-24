from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.dependencies.auth import get_current_user, require_admin
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentListResponse,
    AvailableSlotResponse,
    DashboardMetrics,
    RevenueChartResponse,
)
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/api/appointments", tags=["Agendamentos"])


def _format_appointment(appt) -> dict:
    data = {
        "id": appt.id,
        "client_id": appt.client_id,
        "data_hora": appt.data_hora,
        "status": appt.status,
        "criado_por": appt.criado_por,
        "aprovado_por": appt.aprovado_por,
        "data_aprovacao": appt.data_aprovacao,
        "criado_em": appt.criado_em,
        "atualizado_em": appt.atualizado_em,
        "services": appt.services,
        "client_nome": appt.client.user.nome if appt.client and appt.client.user else None,
        "approver_nome": appt.approver.nome if appt.approver else None,
    }
    return data


@router.post("", response_model=AppointmentResponse, status_code=201)
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AppointmentService(db)
    appt = service.create_appointment(data, user)
    return _format_appointment(appt)


@router.get("", response_model=AppointmentListResponse)
def list_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    status: str = Query(None),
    date_from: str = Query(None, description="Data início (YYYY-MM-DD)"),
    date_to: str = Query(None, description="Data fim (YYYY-MM-DD)"),
    client_id: int = Query(None, description="ID do cliente (admin apenas)"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    parsed_from = None
    parsed_to = None
    if date_from:
        try:
            parsed_from = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            pass
    if date_to:
        try:
            parsed_to = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            pass

    service = AppointmentService(db)
    appointments, total = service.list_appointments(
        user=user, skip=skip, limit=limit, status_filter=status,
        date_from=parsed_from, date_to=parsed_to,
        admin_client_id=client_id,
    )
    items = [_format_appointment(a) for a in appointments]
    return AppointmentListResponse(
        items=items, total=total, skip=skip, limit=limit
    )


from typing import List, Optional

@router.get("/check-week", response_model=Optional[AppointmentResponse])
def check_week_appointments(
    date: str = Query(..., description="Data no formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Formato de data inválido. Use YYYY-MM-DD.",
        )
    service = AppointmentService(db)
    appt = service.check_existing_appointments_in_week(user, target_date)
    return _format_appointment(appt) if appt else None


@router.get("/available-slots", response_model=list[AvailableSlotResponse])
def get_available_slots(
    date: str = Query(..., description="Data no formato YYYY-MM-DD"),
    duration: int = Query(15, ge=1, description="Duração total dos serviços em minutos"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Formato de data inválido. Use YYYY-MM-DD.",
        )
    service = AppointmentService(db)
    return service.get_available_slots(target_date, duration)


@router.get("/metrics", response_model=DashboardMetrics)
def get_metrics(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = AppointmentService(db)
    return service.get_dashboard_metrics()


@router.get("/revenue-chart", response_model=RevenueChartResponse)
def get_revenue_chart(
    period: str = Query("monthly", description="monthly ou daily"),
    date_from: str = Query(None, description="Data início (YYYY-MM-DD)"),
    date_to: str = Query(None, description="Data fim (YYYY-MM-DD)"),
    service_id: int = Query(None, description="ID do serviço para filtro"),
    status: str = Query(None, description="Status do agendamento para filtro"),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    parsed_from = None
    parsed_to = None
    if date_from:
        try:
            parsed_from = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            pass
    if date_to:
        try:
            parsed_to = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            pass

    service = AppointmentService(db)
    return service.get_revenue_chart_data(
        period=period,
        date_from=parsed_from,
        date_to=parsed_to,
        service_id=service_id,
        status_filter=status
    )



@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AppointmentService(db)
    appt = service.get_appointment(appointment_id, user)
    return _format_appointment(appt)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AppointmentService(db)
    appt = service.update_appointment(appointment_id, data, user)
    return _format_appointment(appt)


@router.post("/{appointment_id}/approve", response_model=AppointmentResponse)
def approve_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = AppointmentService(db)
    appt = service.approve_appointment(appointment_id, admin)
    return _format_appointment(appt)


@router.post("/{appointment_id}/reject", response_model=AppointmentResponse)
def reject_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = AppointmentService(db)
    appt = service.reject_appointment(appointment_id, admin)
    return _format_appointment(appt)


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    service = AppointmentService(db)
    appt = service.cancel_appointment(appointment_id, user)
    return _format_appointment(appt)


@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
def complete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    service = AppointmentService(db)
    appt = service.complete_appointment(appointment_id, admin)
    return _format_appointment(appt)
