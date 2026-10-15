from sqlalchemy import Column, Integer, Float, DateTime, Enum, ForeignKey, func

from app.core.database import Base
from app.models.enums import ReviewStatus


class DuplicateCandidate(Base):
    __tablename__ = "duplicate_candidates"

    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey("civic_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_issue_id = Column(Integer, ForeignKey("civic_issues.id", ondelete="CASCADE"), nullable=False)
    distance_meters = Column(Float)
    image_similarity = Column(Float)      # optional / stretch
    combined_score = Column(Float)
    review_status = Column(Enum(ReviewStatus, native_enum=False), default=ReviewStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
