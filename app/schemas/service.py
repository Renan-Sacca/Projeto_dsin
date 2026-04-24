from typing import Optional
from pydantic import BaseModel, Field


class ServiceCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None
    duracao_minutos: int = Field(gt=0, description="Duração em minutos")
    preco: float = Field(gt=0, description="Preço do serviço")


class ServiceUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    duracao_minutos: Optional[int] = Field(None, gt=0)
    preco: Optional[float] = Field(None, gt=0)
    ativo: Optional[bool] = None


class ServiceResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None
    duracao_minutos: int
    preco: float
    ativo: bool

    model_config = {"from_attributes": True}


class ServiceListResponse(BaseModel):
    items: list[ServiceResponse]
    total: int
    skip: int
    limit: int
