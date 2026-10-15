from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class IssueEvent(Base):
    """Status-change history for the issue timeline."""
    __tablename__ = "issue_events"

    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey("civic_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(String(20))
    new_status = Column(String(20), nullable=False)
    changed_by = Column(Integer, ForeignKey("users.id"))
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("CivicIssue", back_populates="events")
