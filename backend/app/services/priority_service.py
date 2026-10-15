"""Transparent priority scoring -- our prototype decision-support rule, NOT an
official government prioritisation policy.

Priority = 0.30*Severity + 0.20*Frequency + 0.20*LocationCriticality
         + 0.15*Traffic/Footfall + 0.15*TimeUnresolved        (each 0-100)
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.models.enums import IssueType, Severity

WEIGHTS = {"severity": 0.30, "frequency": 0.20, "location": 0.20, "traffic": 0.15, "time": 0.15}

SEVERITY_SCORE = {Severity.LOW: 25, Severity.MEDIUM: 55, Severity.HIGH: 90}

# Footfall/traffic PROXY by category (no live traffic data in the prototype).
TRAFFIC_PROXY = {IssueType.POTHOLE: 70, IssueType.STREETLIGHT: 60,
                 IssueType.GARBAGE: 50, IssueType.WATER_LEAKAGE: 50}

# Location-criticality from words in the address/description.
CRITICAL_KEYWORDS = ("hospital", "school", "college", "junction", "highway", "station",
                     "bus stop", "market", "crossing", "flyover")
IMPORTANT_KEYWORDS = ("main road", "chowk", "square", "bridge", "temple", "mall", "it park", "phase")
TIME_FULL_AT_HOURS = 72   # unresolved for 3 days -> 100


def weighted_score(severity: float, frequency: float, location: float,
                   traffic: float, time_: float) -> float:
    return round(WEIGHTS["severity"] * severity + WEIGHTS["frequency"] * frequency
                 + WEIGHTS["location"] * location + WEIGHTS["traffic"] * traffic
                 + WEIGHTS["time"] * time_, 2)


def frequency_score(report_count: int) -> float:
    return float(min(100, 20 + 15 * (max(report_count, 1) - 1)))   # 1->20 ... 7+->100


def location_score(address: str | None, description: str | None) -> float:
    text = f"{address or ''} {description or ''}".lower()
    if any(k in text for k in CRITICAL_KEYWORDS):
        return 90.0
    if any(k in text for k in IMPORTANT_KEYWORDS):
        return 65.0
    return 40.0


def time_score(created_at: datetime | None, now: datetime | None = None) -> float:
    if not created_at:
        return 0.0
    now = now or datetime.now(timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    hours = max(0.0, (now - created_at).total_seconds() / 3600)
    return round(min(100.0, hours / TIME_FULL_AT_HOURS * 100), 1)


def level(score: float) -> str:
    return "HIGH" if score >= 70 else "MEDIUM" if score >= 40 else "LOW"


def compute_priority(issue, severity_source: str = "ai") -> tuple[float, dict]:
    """Returns (score, breakdown) for a CivicIssue. Safe to call again later to refresh."""
    sev = SEVERITY_SCORE.get(issue.severity or Severity.MEDIUM, 55)
    parts = {
        "severity": float(sev),
        "frequency": frequency_score(issue.report_count or 1),
        "location": location_score(issue.address, issue.description),
        "traffic": float(TRAFFIC_PROXY.get(issue.issue_type, 50)),
        "time": time_score(issue.created_at),
    }
    score = weighted_score(parts["severity"], parts["frequency"], parts["location"],
                           parts["traffic"], parts["time"])
    breakdown = {"components": parts, "weights": WEIGHTS, "score": score, "level": level(score),
                 "severity_source": severity_source,
                 "note": "Prototype decision-support rule; traffic is a per-category proxy."}
    return score, breakdown


def refresh_open_issues(db) -> int:
    """Recompute priority for open issues (the time-unresolved factor changes daily)."""
    from app.models import CivicIssue
    from app.models.enums import IssueStatus
    rows = db.query(CivicIssue).filter(CivicIssue.status.in_(
        (IssueStatus.REPORTED, IssueStatus.ASSIGNED, IssueStatus.IN_PROGRESS))).all()
    for issue in rows:
        src = (issue.priority_breakdown or {}).get("severity_source", "ai")
        issue.priority_score, issue.priority_breakdown = compute_priority(issue, src)
    db.commit()
    return len(rows)
