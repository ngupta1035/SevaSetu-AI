from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey("civic_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name = Column(String(80))
    model_version = Column(String(40))
    predicted_class = Column(String(40))
    confidence = Column(Float)
    severity_prediction = Column(String(20))
    inference_time_ms = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("CivicIssue", back_populates="predictions")
