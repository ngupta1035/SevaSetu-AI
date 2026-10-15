from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.enums import IssueType, Severity, IssueStatus


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    image_url: str | None
    description: str | None
    latitude: float
    longitude: float
    submitted_at: datetime | None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    old_status: str | None
    new_status: str
    comment: str | None
    created_at: datetime | None


class PredictionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    model_name: str | None
    model_version: str | None
    predicted_class: str | None
    confidence: float | None
    severity_prediction: str | None
    inference_time_ms: float | None


class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    issue_code: str
    issue_type: IssueType
    description: str | None
    latitude: float
    longitude: float
    address: str | None
    severity: Severity | None
    model_confidence: float | None
    priority_score: float | None
    report_count: int
    department_id: int | None
    status: IssueStatus
    created_at: datetime | None
    resolved_at: datetime | None


class ResolutionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    resolution_notes: str | None
    before_image_url: str | None
    after_image_url: str | None
    verification_status: str | None
    verified_at: datetime | None
    created_at: datetime | None


class DuplicateOut(BaseModel):
    id: int
    candidate_issue_id: int
    candidate_code: str
    distance_meters: float | None
    combined_score: float | None
    review_status: str


class IssueRow(IssueOut):
    department_name: str | None = None
    pending_duplicates: int = 0


class IssueDetail(IssueOut):
    department_name: str | None = None
    priority_breakdown: dict | None = None
    reports: list[ReportOut] = []
    events: list[EventOut] = []
    predictions: list[PredictionOut] = []
    possible_duplicates: list[DuplicateOut] = []
    resolution: ResolutionOut | None = None
    merged: bool = False        # True when this report was attached to an existing issue
