"""Duplicate detection: same category + GPS proximity + time window (PostGIS).

  <= AUTO_MERGE_M   : treated as the SAME issue -> the new report is attached to it
  <= REVIEW_M       : kept as a separate issue but flagged "possible duplicate"
                      (DuplicateCandidate, PENDING) for the authority to confirm/dismiss
Image similarity is a possible later extension; it is NOT used in this version.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import CivicIssue, DuplicateCandidate
from app.models.enums import IssueStatus, IssueType, ReviewStatus

AUTO_MERGE_M = 25.0
REVIEW_M = 60.0
WINDOW_DAYS = 14
OPEN_STATUSES = (IssueStatus.REPORTED, IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS)


def find_nearby(db: Session, issue_type: IssueType, lat: float, lon: float,
                exclude_id: int | None = None) -> list[tuple[CivicIssue, float]]:
    """Open issues of the same type within REVIEW_M metres, nearest first."""
    point = func.ST_GeogFromText(f"SRID=4326;POINT({lon} {lat})")
    dist = func.ST_Distance(CivicIssue.location, point)
    cutoff = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    q = (db.query(CivicIssue, dist.label("dist"))
         .filter(CivicIssue.issue_type == issue_type,
                 CivicIssue.status.in_(OPEN_STATUSES),
                 CivicIssue.created_at >= cutoff,
                 func.ST_DWithin(CivicIssue.location, point, REVIEW_M)))
    if exclude_id:
        q = q.filter(CivicIssue.id != exclude_id)
    return [(i, float(d)) for i, d in q.order_by(dist).all()]


def proximity_score(distance_m: float) -> float:
    """1.0 at the same spot, 0.0 at REVIEW_M. (Proximity only; no image similarity yet.)"""
    return round(max(0.0, 1 - distance_m / REVIEW_M), 2)


def record_candidates(db: Session, new_issue: CivicIssue,
                      matches: list[tuple[CivicIssue, float]], limit: int = 3) -> None:
    for other, d in matches[:limit]:
        db.add(DuplicateCandidate(issue_id=new_issue.id, candidate_issue_id=other.id,
                                  distance_meters=round(d, 1), combined_score=proximity_score(d),
                                  review_status=ReviewStatus.PENDING))
