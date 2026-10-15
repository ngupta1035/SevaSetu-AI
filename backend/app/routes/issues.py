from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from geoalchemy2.elements import WKTElement
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import (AIPrediction, CivicIssue, DuplicateCandidate, IssueEvent,
                        IssueReport, User)
from app.models.enums import IssueType, IssueStatus, Severity, UserRole
from app.schemas.issue import DuplicateOut, IssueDetail, IssueOut, ResolutionOut
from app.services import ai_service, duplicate_service
from app.services.priority_service import compute_priority
from app.services.routing_service import department_for
from app.utils.uploads import save_image

router = APIRouter(prefix="/api/issues", tags=["issues"])

SEVERITY_RANK = {Severity.LOW: 0, Severity.MEDIUM: 1, Severity.HIGH: 2}


def _point(lat: float, lon: float) -> WKTElement:
    return WKTElement(f"POINT({lon} {lat})", srid=4326)  # PostGIS order is lon, lat


def _add_prediction(db, issue_id, ai):
    db.add(AIPrediction(issue_id=issue_id, model_name=ai.model_name, model_version=ai.model_version,
                        predicted_class=ai.predicted_class, confidence=ai.confidence,
                        severity_prediction=ai.severity.value, inference_time_ms=ai.inference_time_ms))


@router.post("", response_model=IssueDetail, status_code=201)
async def create_issue(
    image: UploadFile = File(...),
    latitude: float = Form(..., ge=-90, le=90),
    longitude: float = Form(..., ge=-180, le=180),
    issue_type: IssueType | None = Form(None),   # omit -> AI decides
    description: str | None = Form(None, max_length=1000),
    address: str | None = Form(None, max_length=255),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    image_url, image_path = await save_image(image)
    ai = await run_in_threadpool(ai_service.analyze_image, image_path)

    final_type = issue_type or (ai.issue_type if ai else None)
    if final_type is None:
        Path(image_path).unlink(missing_ok=True)
        raise HTTPException(422, "The AI could not identify an issue in this photo. "
                                 "Please select the issue type manually.")
    use_ai = ai is not None and ai.issue_type == final_type
    source = "ai" if use_ai else "default (no AI severity)"

    matches = duplicate_service.find_nearby(db, final_type, latitude, longitude)

    # ---- Same issue already reported nearby: attach this report to it ----
    if matches and matches[0][1] <= duplicate_service.AUTO_MERGE_M:
        target, dist = matches[0]
        db.add(IssueReport(issue_id=target.id, user_id=user.id, image_url=image_url,
                           description=description, latitude=latitude, longitude=longitude,
                           location=_point(latitude, longitude)))
        target.report_count = (target.report_count or 1) + 1
        if use_ai:
            if SEVERITY_RANK[ai.severity] > SEVERITY_RANK.get(target.severity, 1):
                target.severity = ai.severity
            target.model_confidence = max(target.model_confidence or 0, ai.confidence)
            _add_prediction(db, target.id, ai)
        db.add(IssueEvent(issue_id=target.id, old_status=target.status.value,
                          new_status=target.status.value, changed_by=user.id,
                          comment=f"Duplicate report merged ({dist:.0f} m from the original)"))
        db.flush()
        old_src = (target.priority_breakdown or {}).get("severity_source", source)
        target.priority_score, target.priority_breakdown = compute_priority(target, old_src)
        db.commit()
        out = _detail(db, target.id, user)
        out.merged = True
        return out

    # ---- New issue ----
    dept = department_for(db, final_type)
    issue = CivicIssue(
        issue_code="PENDING", issue_type=final_type, description=description,
        latitude=latitude, longitude=longitude, location=_point(latitude, longitude),
        address=address, department_id=dept.id if dept else None,
        status=IssueStatus.REPORTED, created_by=user.id, report_count=1,
        severity=ai.severity if use_ai else Severity.MEDIUM,
        model_confidence=ai.confidence if ai else None,
    )
    db.add(issue)
    db.flush()
    issue.issue_code = f"SS-{issue.id:05d}"
    db.add(IssueReport(issue_id=issue.id, user_id=user.id, image_url=image_url,
                       description=description, latitude=latitude, longitude=longitude,
                       location=_point(latitude, longitude)))
    db.add(IssueEvent(issue_id=issue.id, old_status=None, new_status=IssueStatus.REPORTED.value,
                      changed_by=user.id, comment="Issue reported by citizen"))
    if ai:
        _add_prediction(db, issue.id, ai)
    duplicate_service.record_candidates(db, issue, matches)   # 25-60 m: flag for review
    db.flush()
    db.refresh(issue)          # load server-side created_at
    issue.priority_score, issue.priority_breakdown = compute_priority(issue, source)
    db.commit()
    return _detail(db, issue.id, user)


@router.get("/my", response_model=list[IssueOut])
def my_issues(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Issues the citizen created OR contributed a (merged) report to."""
    reported = db.query(IssueReport.issue_id).filter(IssueReport.user_id == user.id)
    return (db.query(CivicIssue)
            .filter((CivicIssue.created_by == user.id) | (CivicIssue.id.in_(reported)))
            .order_by(CivicIssue.created_at.desc()).all())


@router.get("/{issue_id}", response_model=IssueDetail)
def get_issue(issue_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _detail(db, issue_id, user)


def _detail(db: Session, issue_id: int, user: User) -> IssueDetail:
    issue = (db.query(CivicIssue)
             .options(joinedload(CivicIssue.reports), joinedload(CivicIssue.events),
                      joinedload(CivicIssue.department), joinedload(CivicIssue.predictions),
                      joinedload(CivicIssue.resolutions))
             .filter(CivicIssue.id == issue_id).first())
    if not issue:
        raise HTTPException(404, "Issue not found")
    if user.role == UserRole.CITIZEN:
        mine = (issue.created_by == user.id) or any(r.user_id == user.id for r in issue.reports)
        if not mine:
            raise HTTPException(403, "You can only view your own reports")
    out = IssueDetail.model_validate(issue)
    out.department_name = issue.department.name if issue.department else None
    out.events = sorted(out.events, key=lambda e: e.created_at or 0)
    latest = max(issue.resolutions, key=lambda r: r.id, default=None)
    out.resolution = ResolutionOut.model_validate(latest) if latest else None
    if user.role != UserRole.CITIZEN:      # duplicate review is an authority-side view
        rows = (db.query(DuplicateCandidate, CivicIssue.issue_code)
                .join(CivicIssue, CivicIssue.id == DuplicateCandidate.candidate_issue_id)
                .filter(DuplicateCandidate.issue_id == issue_id).all())
        out.possible_duplicates = [DuplicateOut(
            id=d.id, candidate_issue_id=d.candidate_issue_id, candidate_code=code,
            distance_meters=d.distance_meters, combined_score=d.combined_score,
            review_status=d.review_status.value) for d, code in rows]
    return out
