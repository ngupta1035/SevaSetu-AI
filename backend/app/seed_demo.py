"""Synthetic demo data for SevaSetu AI.

EVERYTHING created here is SYNTHETIC: invented locations/reports, generated
placeholder images (stamped "SYNTHETIC DEMO IMAGE"), no AI predictions and no model
confidence. It exists only to make the dashboard, map and hotspot views demonstrable.

    python -m app.seed_demo            # add demo data (idempotent: refuses if already present)
    python -m app.seed_demo --reset    # remove ONLY demo data (issues created by demoNN@demo.sevasetu), then re-add
"""
from __future__ import annotations

import argparse
import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.core.config import settings

PASSWORD = "demo1234"
N_DEMO_USERS = 12

# (north_m, east_m) offsets from each hotspot centre. All >= 65 m apart.
P1_OFFSETS = [(0, 0), (100, 40), (-110, 60), (60, -120), (180, 100), (-150, -90), (40, 190)]
P2_OFFSETS = [(0, 0), (120, 30), (-90, 100), (50, -130), (-30, 210)]
P3_OFFSETS = [(0, 0), (110, 60), (-100, -40), (30, 150)]

HOTSPOTS = [
    # name, lat, lon, offsets, type weights
    ("Hinjewadi Phase 1", 18.5912, 73.7389, P1_OFFSETS, {"POTHOLE": 5, "STREETLIGHT": 1, "GARBAGE": 1}),
    ("Hinjewadi Phase 2", 18.5990, 73.7270, P2_OFFSETS, {"GARBAGE": 4, "WATER_LEAKAGE": 1}),
    ("Wakad", 18.5985, 73.7600, P3_OFFSETS, {"STREETLIGHT": 2, "WATER_LEAKAGE": 2}),
]
SCATTER_AREAS = ["Baner", "Aundh", "Kothrud", "Pashan", "Balewadi", "Sus", "Bavdhan", "Ravet", "Thergaon"]
SCATTER_BOX = (18.48, 18.66, 73.66, 73.90)      # lat_min, lat_max, lon_min, lon_max
N_SCATTER = 33

DESCRIPTIONS = {
    "POTHOLE": ["Deep pothole on the carriageway", "Large pothole, two-wheelers swerving", "Road surface broken near the edge"],
    "GARBAGE": ["Garbage piled up by the roadside", "Overflowing bin, not collected for days", "Waste dumped near the footpath"],
    "WATER_LEAKAGE": ["Water leaking from the main pipe", "Continuous leakage, road is wet", "Burst pipe near the footpath"],
    "STREETLIGHT": ["Streetlight not working at night", "Pole light flickering and dark", "Whole stretch of lights is off"],
}
LOC_HINTS = ["", "", "", " near the bus stop", " near the school", " at the main junction", " near the market"]
SEVERITY_W = {"POTHOLE": (20, 45, 35), "GARBAGE": (30, 45, 25), "WATER_LEAKAGE": (20, 40, 40), "STREETLIGHT": (35, 45, 20)}


@dataclass
class Spec:
    issue_type: str
    lat: float
    lon: float
    address: str
    description: str
    reports: int = 1
    severity: str = "MEDIUM"
    status: str = "REPORTED"
    age_hours: float = 24.0
    group: str = ""
    extra: dict = field(default_factory=dict)


def _off(lat, lon, north_m, east_m):
    return lat + north_m / 111320, lon + east_m / (111320 * math.cos(math.radians(lat)))


def _dist(a, b):
    return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * math.cos(math.radians(a[0])))


def _pick(rng, weights: dict):
    return rng.choices(list(weights), weights=list(weights.values()))[0]


def build_plan(seed: int = 7) -> list[Spec]:
    """Deterministic list of synthetic issues (pure function: no DB access)."""
    rng = random.Random(seed)
    plan: list[Spec] = []

    for name, lat, lon, offsets, tw in HOTSPOTS:
        for k, (n, e) in enumerate(offsets):
            la, lo = _off(lat, lon, n, e)
            t = "POTHOLE" if (name == "Hinjewadi Phase 1" and k == 0) else _pick(rng, tw)
            addr = name + ("" if k == 0 else rng.choice(LOC_HINTS))
            plan.append(Spec(t, la, lo, addr, rng.choice(DESCRIPTIONS[t]) + " [synthetic demo]",
                             reports=rng.choices([1, 2, 3, 4], weights=[55, 22, 15, 8])[0],
                             severity=_pick(rng, dict(zip(("LOW", "MEDIUM", "HIGH"), SEVERITY_W[t]))),
                             age_hours=rng.uniform(4, 13 * 24), group=name))
    # Hero scenario: one pothole reported by 7 different citizens, still unassigned
    hero = plan[0]
    hero.reports, hero.severity, hero.status, hero.age_hours = 7, "HIGH", "REPORTED", 60
    hero.address = "Hinjewadi Phase 1, near the main junction"
    hero.description = "Large pothole near the junction, many vehicles affected [synthetic demo]"
    hero.extra["hero"] = True
    # Possible-duplicate pair in Phase 2: two garbage issues ~45 m apart (flagged for review)
    p2 = [s for s in plan if s.group == "Hinjewadi Phase 2"]
    a, b = p2[0], p2[1]
    a.issue_type = b.issue_type = "GARBAGE"
    b.lat, b.lon = _off(a.lat, a.lon, 45, 0)
    for s in (a, b):
        s.status, s.reports = "REPORTED", 1
        s.description = rng.choice(DESCRIPTIONS["GARBAGE"]) + " [synthetic demo]"
    b.extra["duplicate_of"] = 0                       # index within p2 (a)
    a.extra["pair_key"] = "p2"
    b.extra["pair_key"] = "p2"

    # Scattered one-off issues, kept far from each other and from hotspots (no accidental clusters)
    centers = [(h[1], h[2]) for h in HOTSPOTS]
    placed: list[tuple[float, float]] = []
    tries = 0
    while len(placed) < N_SCATTER and tries < 20000:
        tries += 1
        la = rng.uniform(SCATTER_BOX[0], SCATTER_BOX[1])
        lo = rng.uniform(SCATTER_BOX[2], SCATTER_BOX[3])
        if any(_dist((la, lo), c) < 700 for c in centers) or any(_dist((la, lo), p) < 350 for p in placed):
            continue
        placed.append((la, lo))
        t = _pick(rng, {"POTHOLE": 4, "GARBAGE": 3, "WATER_LEAKAGE": 2, "STREETLIGHT": 3})
        plan.append(Spec(t, la, lo, f"{rng.choice(SCATTER_AREAS)}{rng.choice(LOC_HINTS)}",
                         rng.choice(DESCRIPTIONS[t]) + " [synthetic demo]",
                         reports=rng.choices([1, 2, 3], weights=[70, 20, 10])[0],
                         severity=_pick(rng, dict(zip(("LOW", "MEDIUM", "HIGH"), SEVERITY_W[t]))),
                         age_hours=rng.uniform(4, 13 * 24), group="scatter"))

    # Lifecycle statuses (hero and the duplicate pair stay REPORTED).
    # Hotspot members stay OPEN so the demo hotspots are stable (hotspots are built from open issues).
    for s in plan:
        if s.extra.get("hero") or s.extra.get("pair_key"):
            continue
        r = rng.random()
        if s.group != "scatter":
            s.status = "REPORTED" if r < 0.55 else "ASSIGNED" if r < 0.8 else "IN_PROGRESS"
            continue
        if s.age_hours < 30:
            s.status = "REPORTED" if r < 0.7 else "ASSIGNED"
        else:
            s.status = ("REPORTED" if r < 0.34 else "ASSIGNED" if r < 0.5 else "IN_PROGRESS" if r < 0.68
                        else "RESOLVED" if r < 0.84 else "VERIFIED")
    return plan


# ---------------------------------------------------------------- images
def _make_images(upload_dir: Path) -> dict:
    """Generate clearly-labelled placeholder images. Returns {(kind,type): url}."""
    from PIL import Image, ImageDraw, ImageFilter
    folder = upload_dir / "demo"
    folder.mkdir(parents=True, exist_ok=True)
    rng = random.Random(1)
    urls = {}
    colors = {"POTHOLE": (95, 95, 100), "GARBAGE": (110, 105, 90), "WATER_LEAKAGE": (90, 100, 110), "STREETLIGHT": (40, 45, 70)}
    for t, base in colors.items():
        for kind in ("before", "after"):
            im = Image.new("RGB", (640, 420), base if kind == "before" else tuple(min(255, c + 45) for c in base))
            d = ImageDraw.Draw(im)
            for _ in range(900):                       # asphalt-like noise
                x, y = rng.randrange(640), rng.randrange(420)
                v = rng.randint(-18, 18)
                d.point((x, y), fill=tuple(max(0, min(255, c + v)) for c in im.getpixel((x, y))))
            if kind == "before":
                shape = {"POTHOLE": (200, 170, 440, 290), "GARBAGE": (180, 190, 460, 320),
                         "WATER_LEAKAGE": (150, 250, 500, 330), "STREETLIGHT": (290, 60, 350, 300)}[t]
                d.ellipse(shape, fill=(25, 25, 28) if t != "WATER_LEAKAGE" else (60, 110, 170))
            im = im.filter(ImageFilter.GaussianBlur(0.6))
            d = ImageDraw.Draw(im)
            d.rectangle((0, 380, 640, 420), fill=(0, 0, 0))
            d.text((14, 392), f"SYNTHETIC DEMO IMAGE - {t} ({kind})", fill=(255, 255, 255))
            name = f"demo_{kind}_{t.lower()}.jpg"
            im.save(folder / name, quality=85)
            urls[(kind, t)] = f"/uploads/demo/{name}"
    return urls


# ---------------------------------------------------------------- DB seeding
def run(reset: bool = False, seed: int = 7) -> dict:
    from geoalchemy2.elements import WKTElement
    from app.core.database import SessionLocal
    from app.core.security import hash_password
    from app.models import (Assignment, CivicIssue, Department, DuplicateCandidate, IssueEvent,
                            IssueReport, Resolution, User)
    from app.models.enums import (IssueStatus, IssueType, ReviewStatus, Severity, UserRole,
                                  VerificationStatus)
    from app.seed import run as seed_base
    from app.services.priority_service import compute_priority
    from app.services.routing_service import department_for

    seed_base()                                    # departments + demo citizen/authority accounts
    db = SessionLocal()
    rng = random.Random(seed)
    try:
        users = []
        for k in range(1, N_DEMO_USERS + 1):
            email = f"demo{k:02d}@demo.sevasetu"
            u = db.query(User).filter_by(email=email).first()
            if not u:
                u = User(name=f"Demo Citizen {k:02d}", email=email, role=UserRole.CITIZEN,
                         password_hash=hash_password(PASSWORD))
                db.add(u)
            users.append(u)
        db.flush()
        demo_ids = [u.id for u in users]
        existing = db.query(CivicIssue).filter(CivicIssue.created_by.in_(demo_ids)).all()
        if existing and not reset:
            raise SystemExit(f"Demo data already present ({len(existing)} issues). Use --reset to rebuild it.")
        for i in existing:
            db.delete(i)
        db.flush()

        authority = db.query(User).filter_by(email="authority@demo.sevasetu").first()
        imgs = _make_images(Path(settings.UPLOAD_DIR))
        now = datetime.now(timezone.utc)
        plan = build_plan(seed)
        created: dict[int, CivicIssue] = {}
        pair_issues = []

        for idx, s in enumerate(plan):
            t = IssueType(s.issue_type)
            created_at = now - timedelta(hours=s.age_hours)
            dept = department_for(db, t)
            owner = users[idx % len(users)]
            issue = CivicIssue(
                issue_code="PENDING", issue_type=t, description=s.description, latitude=s.lat, longitude=s.lon,
                location=WKTElement(f"POINT({s.lon} {s.lat})", srid=4326), address=s.address,
                severity=Severity(s.severity), model_confidence=None,
                department_id=dept.id if dept else None, status=IssueStatus.REPORTED,
                created_by=owner.id, report_count=s.reports, created_at=created_at)
            db.add(issue)
            db.flush()
            issue.issue_code = f"SS-{issue.id:05d}"
            created[idx] = issue
            if s.extra.get("pair_key"):
                pair_issues.append(issue)

            # citizen reports: distinct demo users, each within ~15 m of the issue
            for r in range(s.reports):
                u = users[(idx + r) % len(users)]
                la, lo = _off(s.lat, s.lon, rng.uniform(-15, 15), rng.uniform(-15, 15))
                span = max(1.0, s.age_hours - 0.5)
                db.add(IssueReport(issue_id=issue.id, user_id=u.id, image_url=imgs[("before", s.issue_type)],
                                   description=s.description, latitude=la, longitude=lo,
                                   location=WKTElement(f"POINT({lo} {la})", srid=4326),
                                   submitted_at=created_at + timedelta(hours=rng.uniform(0, span) if r else 0)))
            db.add(IssueEvent(issue_id=issue.id, old_status=None, new_status="REPORTED", changed_by=owner.id,
                              comment="Issue reported by citizen", created_at=created_at))

            # lifecycle history
            st = s.status
            t_cur = created_at
            if st != "REPORTED":
                t_cur = created_at + timedelta(hours=min(s.age_hours * 0.3, rng.uniform(1, 12)))
                db.add(Assignment(issue_id=issue.id, department_id=dept.id, assigned_at=t_cur,
                                  notes="Synthetic demo work order"))
                db.add(IssueEvent(issue_id=issue.id, old_status="REPORTED", new_status="ASSIGNED",
                                  changed_by=authority.id, comment=f"Assigned to {dept.name}", created_at=t_cur))
            if st in ("IN_PROGRESS", "RESOLVED", "VERIFIED"):
                t_cur += timedelta(hours=rng.uniform(1, 10))
                db.add(IssueEvent(issue_id=issue.id, old_status="ASSIGNED", new_status="IN_PROGRESS",
                                  changed_by=authority.id, comment="Work started", created_at=t_cur))
            if st in ("RESOLVED", "VERIFIED"):
                t_cur += timedelta(hours=rng.uniform(4, 60))
                t_cur = min(t_cur, now - timedelta(minutes=30))
                issue.resolved_at = t_cur
                db.add(Resolution(issue_id=issue.id, resolved_by=authority.id,
                                  resolution_notes="Repaired (synthetic demo record)",
                                  before_image_url=imgs[("before", s.issue_type)],
                                  after_image_url=imgs[("after", s.issue_type)],
                                  verification_status=VerificationStatus.VERIFIED if st == "VERIFIED" else VerificationStatus.PENDING,
                                  verified_at=t_cur + timedelta(hours=3) if st == "VERIFIED" else None,
                                  created_at=t_cur))
                db.add(IssueEvent(issue_id=issue.id, old_status="IN_PROGRESS", new_status="RESOLVED",
                                  changed_by=authority.id, comment="Repaired (synthetic demo record)", created_at=t_cur))
            if st == "VERIFIED":
                db.add(IssueEvent(issue_id=issue.id, old_status="RESOLVED", new_status="VERIFIED",
                                  changed_by=authority.id, comment="Resolution verified", created_at=t_cur + timedelta(hours=3)))
            issue.status = IssueStatus(st)
            db.flush()
            db.refresh(issue)
            issue.priority_score, issue.priority_breakdown = compute_priority(issue, "synthetic demo data")

        if len(pair_issues) == 2:                  # flagged-for-review duplicate pair
            a, b = pair_issues
            db.add(DuplicateCandidate(issue_id=b.id, candidate_issue_id=a.id, distance_meters=45.0,
                                      combined_score=round(1 - 45 / 60, 2), review_status=ReviewStatus.PENDING))
        db.commit()
        summary = {"issues": len(plan), "reports": sum(s.reports for s in plan), "demo_users": N_DEMO_USERS}
        print("Synthetic demo data created:", summary)
        print(f"Hero scenario: {created[0].issue_code} (pothole, 7 reports) at Hinjewadi Phase 1.")
        print(f"Log in as authority@demo.sevasetu / {PASSWORD}  (citizens: demo01@demo.sevasetu ... / {PASSWORD})")
        return summary
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="delete existing demo data first")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    run(reset=a.reset, seed=a.seed)
