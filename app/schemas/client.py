from typing import Optional
from pydantic import BaseModel
from pydantic import BaseModel, field_validator
import html
from app.schemas.user import UserResponse


class ClientResponse(BaseModel):
    id: int
    user_id: int
    telefone: Optional[str] = None
    user: Optional[UserResponse] = None

    model_config = {"from_attributes": True}




class ClientUpdate(BaseModel):
    telefone: Optional[str] = None
    nome: Optional[str] = None
    email: Optional[str] = None
    ativo: Optional[bool] = None

    @field_validator('nome', 'email', 'telefone')
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            # Remove tags HTML e espaços extras
            return html.escape(v).strip()
        return v


from typing import List

class ClientListResponse(BaseModel):
    items: List[ClientResponse]
    total: int
    skip: int
    limit: int
