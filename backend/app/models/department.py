from sqlalchemy import Column, Integer, String, Text, DateTime, func

from app.core.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(Text)
    contact_email = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
