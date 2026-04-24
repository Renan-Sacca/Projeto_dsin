from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.models.appointment import AppointmentStatus
from app.schemas.service import ServiceResponse


class AppointmentCreate(BaseModel):
    data_hora: datetime
    service_ids: List[int]
    add_to_google_calendar: bool = False
    client_id: Optional[int] = None


class AppointmentUpdate(BaseModel):
    data_hora: Optional[datetime] = None
    service_ids: Optional[List[int]] = None


class AppointmentServiceResponse(BaseModel):
    id: int
    service_id: int
    service: Optional[ServiceResponse] = None

    model_config = {"from_attributes": True}


class AppointmentResponse(BaseModel):
    id: int
    client_id: int
    data_hora: datetime
    status: AppointmentStatus
    criado_por: int
    aprovado_por: Optional[int] = None
    data_aprovacao: Optional[datetime] = None
    criado_em: datetime
    atualizado_em: datetime
    services: List[AppointmentServiceResponse] = []
    client_nome: Optional[str] = None
    approver_nome: Optional[str] = None

    model_config = {"from_attributes": True}


class AvailableSlotResponse(BaseModel):
    data_hora: datetime
    disponivel: bool = True


class AppointmentListResponse(BaseModel):
    items: List[AppointmentResponse]
    total: int
    skip: int
    limit: int


class DashboardMetrics(BaseModel):
    total_agendamentos: int
    pendentes: int
    aprovados: int
    rejeitados: int
    cancelados: int
    completados: int
    total_clientes: int
    total_servicos: int
    receita_estimada: float
    agendamentos_hoje: int


class RevenueChartItem(BaseModel):
    label: str
    estimated_revenue: float
    paid_revenue: float


class RevenueChartResponse(BaseModel):
    items: List[RevenueChartItem]
    total_estimated: float
    total_paid: float
