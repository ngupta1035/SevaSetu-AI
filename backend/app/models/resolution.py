from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import VerificationStatus


class Resolution(Base):
    __tablename__ = "resolutions"

    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey("civic_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    resolved_by = Column(Integer, ForeignKey("users.id"))
    resolution_notes = Column(Text)
    before_image_url = Column(String(500))
    after_image_url = Column(String(500))
    verification_status = Column(Enum(VerificationStatus, native_enum=False),
                                 default=VerificationStatus.PENDING)
    verified_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("CivicIssue", back_populates="resolutions")
