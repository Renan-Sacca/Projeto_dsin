from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator
import html

from app.models.user import UserType



class UserCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    telefone: Optional[str] = None

    @field_validator('nome', 'email', 'telefone')
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return html.escape(v).strip()
        return v


class UserLogin(BaseModel):
    email: EmailStr
    senha: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    nova_senha: str


class UserUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    ativo: Optional[bool] = None

    @field_validator('nome', 'email', 'telefone')
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return html.escape(v).strip()
        return v


class UserResponse(BaseModel):
    id: int
    nome: str
    email: str
    tipo: UserType
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime
    has_google_calendar: Optional[bool] = False

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
