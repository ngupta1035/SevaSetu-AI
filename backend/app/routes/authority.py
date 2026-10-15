from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models import (Assignment, CivicIssue, Department, DuplicateCandidate, IssueEvent,
                        IssueReport, Resolution, User)
from app.models.enums import IssueStatus, IssueType, ReviewStatus, UserRole, VerificationStatus
from app.schemas.authority import AssignIn, StatusIn, VerifyIn
from app.schemas.issue import IssueRow
from app.services import hotspot_service
from app.services.priority_service import compute_priority, refresh_open_issues
from app.utils.uploads import save_image

router = APIRouter(prefix="/api/admin", tags=["authority"])
authority_only = require_roles(UserRole.AUTHORITY, UserRole.ADMIN)

OPEN = (IssueStatus.REPORTED, IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS)
HIGH_PRIORITY_AT = 70

# Transitions handled by PATCH /status. ASSIGNED -> assign endpoint;
# RESOLVED -> POST /resolve (with after-photo); VERIFIED -> POST /verify.
TRANSITIONS = {
    IssueStatus.ASSIGNED: {IssueStatus.IN_PROGRESS},
    IssueStatus.RESOLVED: {IssueStatus.IN_PROGRESS},      # reopen if the fix did not hold
}


def _event(db, issue, old, new, user, comment):
    db.add(IssueEvent(issue_id=issue.id, old_status=old.value if old else None,
                      new_status=new.value, changed_by=user.id, comment=comment))


def _get(db, issue_id) -> CivicIssue:
    issue = db.get(CivicIssue, issue_id)
    if not issue:
        raise HTTPException(404, "Issue not found")
    return issue


@router.get("/departments")
def departments(db: Session = Depends(get_db), _: User = Depends(authority_only)):
    return [{"id": d.id, "name": d.name} for d in db.query(Department).order_by(Department.id).all()]


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), _: User = Depends(authority_only)):
    refresh_open_issues(db)
    total = db.query(func.count(CivicIssue.id)).scalar()
    by_status = dict(db.query(CivicIssue.status, func.count()).group_by(CivicIssue.status).all())
    by_type = dict(db.query(CivicIssue.issue_type, func.count()).group_by(CivicIssue.issue_type).all())
    by_dept = dict(db.query(Department.name, func.count(CivicIssue.id))
                   .outerjoin(CivicIssue, CivicIssue.department_id == Department.id)
                   .group_by(Department.name).all())
    open_q = db.query(func.count(CivicIssue.id)).filter(CivicIssue.status.in_(OPEN))
    avg_secs = (db.query(func.avg(func.extract("epoch", CivicIssue.resolved_at - CivicIssue.created_at)))
                .filter(CivicIssue.resolved_at.isnot(None)).scalar())
    resolved = by_status.get(IssueStatus.RESOLVED, 0) + by_status.get(IssueStatus.VERIFIED, 0)
    return {
        "total": total,
        "open": open_q.scalar(),
        "pending": by_status.get(IssueStatus.REPORTED, 0),
        "high_priority": open_q.filter(CivicIssue.priority_score >= HIGH_PRIORITY_AT).scalar(),
        "resolved": resolved,
        "avg_resolution_hours": round(float(avg_secs) / 3600, 1) if avg_secs else None,
        "pending_duplicates": db.query(func.count(DuplicateCandidate.id))
                                .filter(DuplicateCandidate.review_status == ReviewStatus.PENDING).scalar(),
        "by_status": {s.value: by_status.get(s, 0) for s in IssueStatus},
        "by_category": {t.value: by_type.get(t, 0) for t in IssueType},
        "by_department": by_dept,
    }


@router.get("/issues", response_model=list[IssueRow])
def list_issues(
    status: IssueStatus | None = None,
    issue_type: IssueType | None = None,
    department_id: int | None = None,
    min_priority: float | None = Query(None, ge=0, le=100),
    open_only: bool = False,
    search: str | None = Query(None, max_length=100),
    sort: str = Query("priority", pattern="^(priority|newest|oldest)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _: User = Depends(authority_only),
):
    refresh_open_issues(db)
    q = db.query(CivicIssue)
    if status: q = q.filter(CivicIssue.status == status)
    if issue_type: q = q.filter(CivicIssue.issue_type == issue_type)
    if department_id: q = q.filter(CivicIssue.department_id == department_id)
    if min_priority is not None: q = q.filter(CivicIssue.priority_score >= min_priority)
    if open_only: q = q.filter(CivicIssue.status.in_(OPEN))
    if search:
        like = f"%{search}%"
        q = q.filter(CivicIssue.issue_code.ilike(like) | CivicIssue.address.ilike(like)
                     | CivicIssue.description.ilike(like))
    order = {"priority": CivicIssue.priority_score.desc(), "newest": CivicIssue.created_at.desc(),
             "oldest": CivicIssue.created_at.asc()}[sort]
    issues = q.order_by(order, CivicIssue.id).offset(offset).limit(limit).all()

    dept_names = dict(db.query(Department.id, Department.name).all())
    ids = [i.id for i in issues]
    pend = dict(db.query(DuplicateCandidate.issue_id, func.count())
                .filter(DuplicateCandidate.issue_id.in_(ids),
                        DuplicateCandidate.review_status == ReviewStatus.PENDING)
                .group_by(DuplicateCandidate.issue_id).all()) if ids else {}
    rows = []
    for i in issues:
        r = IssueRow.model_validate(i)
        r.department_name = dept_names.get(i.department_id)
        r.pending_duplicates = pend.get(i.id, 0)
        rows.append(r)
    return rows


@router.patch("/issues/{issue_id}/assign")
def assign(issue_id: int, body: AssignIn, db: Session = Depends(get_db),
           user: User = Depends(authority_only)):
    issue = _get(db, issue_id)
    if issue.status not in (IssueStatus.REPORTED, IssueStatus.ASSIGNED):
        raise HTTPException(409, f"Cannot assign an issue that is {issue.status.value}")
    dept_id = body.department_id or issue.department_id
    dept = db.get(Department, dept_id) if dept_id else None
    if not dept:
        raise HTTPException(422, "A valid department is required")
    old = issue.status
    issue.department_id = dept.id
    issue.status = IssueStatus.ASSIGNED
    db.add(Assignment(issue_id=issue.id, department_id=dept.id, notes=body.notes))
    _event(db, issue, old, IssueStatus.ASSIGNED, user,
           f"Assigned to {dept.name}" + (f" — {body.notes}" if body.notes else ""))
    db.commit()
    return {"id": issue.id, "status": issue.status.value, "department": dept.name}


@router.patch("/issues/{issue_id}/status")
def change_status(issue_id: int, body: StatusIn, db: Session = Depends(get_db),
                  user: User = Depends(authority_only)):
    issue = _get(db, issue_id)
    new, old = body.status, issue.status
    if new == IssueStatus.ASSIGNED:
        raise HTTPException(422, "Use the assign action to assign an issue")
    if new in (IssueStatus.RESOLVED, IssueStatus.VERIFIED):
        raise HTTPException(422, "Use the resolve / verify actions (they record the resolution evidence)")
    if new not in TRANSITIONS.get(old, set()):
        raise HTTPException(409, f"Invalid transition {old.value} → {new.value}")
    now = datetime.now(timezone.utc)
    latest = (db.query(Assignment).filter(Assignment.issue_id == issue.id)
              .order_by(Assignment.id.desc()).first())
    issue.status = new
    if new == IssueStatus.IN_PROGRESS and latest and not latest.accepted_at:
        latest.accepted_at = now
    if old == IssueStatus.RESOLVED and new == IssueStatus.IN_PROGRESS:
        issue.resolved_at = None            # reopened
        _reject_latest_resolution(db, issue.id)
    _event(db, issue, old, new, user, body.comment)
    db.commit()
    return {"id": issue.id, "status": issue.status.value}


def _latest_resolution(db, issue_id):
    return (db.query(Resolution).filter(Resolution.issue_id == issue_id)
            .order_by(Resolution.id.desc()).first())


def _reject_latest_resolution(db, issue_id):
    res = _latest_resolution(db, issue_id)
    if res and res.verification_status == VerificationStatus.PENDING:
        res.verification_status = VerificationStatus.REJECTED


@router.post("/issues/{issue_id}/resolve")
async def resolve(issue_id: int,
                  notes: str | None = Form(None, max_length=1000),
                  after_image: UploadFile | None = File(None),
                  db: Session = Depends(get_db), user: User = Depends(authority_only)):
    """Mark an in-progress issue resolved, recording notes and an optional after-photo."""
    issue = _get(db, issue_id)
    if issue.status != IssueStatus.IN_PROGRESS:
        raise HTTPException(409, f"Only in-progress issues can be resolved (this one is {issue.status.value})")
    after_url = None
    if after_image is not None and after_image.filename:
        after_url, _ = await save_image(after_image)
    first = (db.query(IssueReport).filter(IssueReport.issue_id == issue.id)
             .order_by(IssueReport.id.asc()).first())
    now = datetime.now(timezone.utc)
    db.add(Resolution(issue_id=issue.id, resolved_by=user.id, resolution_notes=notes,
                      before_image_url=first.image_url if first else None,
                      after_image_url=after_url, verification_status=VerificationStatus.PENDING))
    latest = (db.query(Assignment).filter(Assignment.issue_id == issue.id)
              .order_by(Assignment.id.desc()).first())
    if latest:
        latest.completed_at = now
    old = issue.status
    issue.status = IssueStatus.RESOLVED
    issue.resolved_at = now
    _event(db, issue, old, IssueStatus.RESOLVED, user,
           notes or ("Marked resolved with after-photo" if after_url else "Marked resolved"))
    db.commit()
    return {"id": issue.id, "status": issue.status.value, "after_image_url": after_url}


@router.post("/issues/{issue_id}/verify")
def verify(issue_id: int, body: VerifyIn, db: Session = Depends(get_db),
           user: User = Depends(authority_only)):
    """Authority confirms (or rejects) the resolution. Verification here is human-confirmed."""
    issue = _get(db, issue_id)
    if issue.status != IssueStatus.RESOLVED:
        raise HTTPException(409, f"Only resolved issues can be verified (this one is {issue.status.value})")
    res = _latest_resolution(db, issue.id)
    now = datetime.now(timezone.utc)
    old = issue.status
    if body.approved:
        issue.status = IssueStatus.VERIFIED
        if res:
            res.verification_status, res.verified_at = VerificationStatus.VERIFIED, now
        _event(db, issue, old, IssueStatus.VERIFIED, user, body.comment or "Resolution verified")
    else:
        issue.status, issue.resolved_at = IssueStatus.IN_PROGRESS, None
        if res:
            res.verification_status, res.verified_at = VerificationStatus.REJECTED, now
        _event(db, issue, old, IssueStatus.IN_PROGRESS, user,
               "Resolution rejected: " + (body.comment or "work not satisfactory"))
    db.commit()
    return {"id": issue.id, "status": issue.status.value}


@router.get("/map")
def map_data(issue_type: IssueType | None = None, open_only: bool = True,
             eps_m: float = Query(250, ge=50, le=2000), min_points: int = Query(3, ge=2, le=20),
             db: Session = Depends(get_db), _: User = Depends(authority_only)):
    """Markers + hotspot clusters for the map. Hotspots are always built from OPEN issues."""
    refresh_open_issues(db)
    q = db.query(CivicIssue)
    if issue_type:
        q = q.filter(CivicIssue.issue_type == issue_type)
    if open_only:
        q = q.filter(CivicIssue.status.in_(OPEN))
    issues = q.all()
    open_issues = [i for i in issues if i.status in OPEN]
    pts = [hotspot_service.Point(i.id, i.latitude, i.longitude, i.issue_type.value,
                                 i.priority_score or 0, i.report_count or 1, i.address, i.issue_code)
           for i in open_issues]
    return {
        "issues": [{"id": i.id, "code": i.issue_code, "type": i.issue_type.value,
                    "lat": i.latitude, "lon": i.longitude, "status": i.status.value,
                    "priority": i.priority_score or 0,
                    "severity": i.severity.value if i.severity else None,
                    "reports": i.report_count, "address": i.address} for i in issues],
        "hotspots": hotspot_service.find_hotspots(pts, eps_m, min_points),
        "params": {"eps_m": eps_m, "min_points": min_points},
    }


@router.get("/analytics")
def analytics(days: int = Query(14, ge=3, le=90), db: Session = Depends(get_db),
              _: User = Depends(authority_only)):
    start = (datetime.now(timezone.utc) - timedelta(days=days - 1)).date()
    created = dict(db.query(func.date(CivicIssue.created_at), func.count())
                   .filter(func.date(CivicIssue.created_at) >= start).group_by(func.date(CivicIssue.created_at)).all())
    resolved = dict(db.query(func.date(CivicIssue.resolved_at), func.count())
                    .filter(CivicIssue.resolved_at.isnot(None), func.date(CivicIssue.resolved_at) >= start)
                    .group_by(func.date(CivicIssue.resolved_at)).all())
    trend = []
    for k in range(days):
        d = start + timedelta(days=k)
        trend.append({"date": d.isoformat(), "reported": created.get(d, 0), "resolved": resolved.get(d, 0)})
    avg = (db.query(CivicIssue.issue_type, func.avg(func.extract("epoch", CivicIssue.resolved_at - CivicIssue.created_at)))
           .filter(CivicIssue.resolved_at.isnot(None)).group_by(CivicIssue.issue_type).all())
    return {"trend": trend,
            "avg_resolution_hours_by_category": {t.value: round(float(v) / 3600, 1) for t, v in avg}}


@router.post("/duplicates/{dup_id}/{action}")
def review_duplicate(dup_id: int, action: str, db: Session = Depends(get_db),
                     user: User = Depends(authority_only)):
    """confirm: merge this issue's reports into the candidate issue. dismiss: keep both."""
    if action not in ("confirm", "dismiss"):
        raise HTTPException(404, "Unknown action")
    dup = db.get(DuplicateCandidate, dup_id)
    if not dup or dup.review_status != ReviewStatus.PENDING:
        raise HTTPException(404, "No pending duplicate with that id")
    if action == "dismiss":
        dup.review_status = ReviewStatus.DISMISSED
        db.commit()
        return {"result": "dismissed"}

    source, target = _get(db, dup.issue_id), _get(db, dup.candidate_issue_id)
    moved = db.query(IssueReport).filter(IssueReport.issue_id == source.id).update(
        {IssueReport.issue_id: target.id})
    target.report_count = (target.report_count or 1) + moved
    db.add(IssueEvent(issue_id=target.id, old_status=target.status.value,
                      new_status=target.status.value, changed_by=user.id,
                      comment=f"Merged duplicate {source.issue_code} ({moved} report(s)) after review"))
    src_code, target_id = source.issue_code, target.id
    db.flush()
    db.expire(source)
    db.delete(source)          # cascades its events / predictions / candidates
    db.flush()
    target = _get(db, target_id)
    src = (target.priority_breakdown or {}).get("severity_source", "ai")
    target.priority_score, target.priority_breakdown = compute_priority(target, src)
    db.commit()
    return {"result": "merged", "into": target.issue_code, "removed": src_code}
