from pydantic import BaseModel

class SystemConfigResponse(BaseModel):
    id: int
    auto_approve_appointments: bool

    class Config:
        from_attributes = True

class SystemConfigUpdate(BaseModel):
    auto_approve_appointments: bool
