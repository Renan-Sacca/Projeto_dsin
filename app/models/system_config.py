
from sqlalchemy import Column, Integer, Boolean

from app.database.base import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, index=True)
    auto_approve_appointments = Column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<SystemConfig(auto_approve={self.auto_approve_appointments})>"
