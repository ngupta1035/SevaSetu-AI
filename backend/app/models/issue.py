from geoalchemy2 import Geography
from sqlalchemy import (Column, Integer, String, Text, Float, DateTime, Enum, JSON,
                        ForeignKey, func)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import IssueType, Severity, IssueStatus


class CivicIssue(Base):
    """One underlying civic problem; many citizen reports can map to it."""
    __tablename__ = "civic_issues"

    id = Column(Integer, primary_key=True)
    issue_code = Column(String(20), unique=True, nullable=False, index=True)  # e.g. SS-00042
    issue_type = Column(Enum(IssueType, native_enum=False), nullable=False, index=True)
    description = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geography(geometry_type="POINT", srid=4326, spatial_index=True))
    address = Column(String(255))
    severity = Column(Enum(Severity, native_enum=False))
    model_confidence = Column(Float)          # model confidence, NOT accuracy
    priority_score = Column(Float, default=0)
    priority_breakdown = Column(JSON)         # transparent per-factor scores
    report_count = Column(Integer, default=1)
    department_id = Column(Integer, ForeignKey("departments.id"))
    status = Column(Enum(IssueStatus, native_enum=False), nullable=False,
                    default=IssueStatus.REPORTED, index=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))

    department = relationship("Department")
    creator = relationship("User")
    reports = relationship("IssueReport", back_populates="issue", cascade="all, delete-orphan")
    events = relationship("IssueEvent", back_populates="issue", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="issue", cascade="all, delete-orphan")
    resolutions = relationship("Resolution", back_populates="issue", cascade="all, delete-orphan")
    predictions = relationship("AIPrediction", back_populates="issue", cascade="all, delete-orphan")


class IssueReport(Base):
    """A single citizen submission (photo + text + GPS)."""
    __tablename__ = "issue_reports"

    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey("civic_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    image_url = Column(String(500))
    description = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location = Column(Geography(geometry_type="POINT", srid=4326, spatial_index=True))
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("CivicIssue", back_populates="reports")
    user = relationship("User")
