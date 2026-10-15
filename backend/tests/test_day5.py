"""Day 5: duplicate detection (PostGIS) + authority dashboard/workflow."""
import io
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services import ai_service
from tests.conftest import offset, rand_point

client = TestClient(app)


def _png():
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (80, 80, 80)).save(buf, "PNG")
    return buf.getvalue()


def _register():
    email = f"d{uuid.uuid4().hex[:8]}@test.com"
    client.post("/api/auth/register", json={"name": "Dup Tester", "email": email, "password": "secret12"})
    tok = client.post("/api/auth/login", data={"username": email, "password": "secret12"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(autouse=True)
def no_ai(monkeypatch):
    monkeypatch.setattr(ai_service, "analyze_image", lambda p: None)


@pytest.fixture(scope="module")
def authority():
    tok = client.post("/api/auth/login", data={"username": "authority@demo.sevasetu", "password": "demo1234"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _report(h, lat, lon, itype="POTHOLE", **extra):
    return client.post("/api/issues", headers=h, files={"image": ("p.png", _png(), "image/png")},
                       data={"latitude": lat, "longitude": lon, "issue_type": itype, **extra})


# ---------- duplicate detection ----------
def test_reports_within_25m_merge_into_one_issue():
    a, b, c = _register(), _register(), _register()
    lat, lon = rand_point()
    r1 = _report(a, lat, lon).json()
    r2 = _report(b, *offset(lat, lon, 12)).json()      # ~12 m away
    r3 = _report(c, *offset(lat, lon, 0, 18)).json()   # ~18 m away
    assert r2["id"] == r1["id"] == r3["id"] and r2["merged"] is True
    assert r3["report_count"] == 3 and len(r3["reports"]) == 3
    # more reports -> higher frequency component -> higher priority
    assert r3["priority_breakdown"]["components"]["frequency"] == 50
    assert r3["priority_score"] > r1["priority_score"]
    # the second citizen can see/track the shared issue
    assert any(i["id"] == r1["id"] for i in client.get("/api/issues/my", headers=b).json())
    assert client.get(f"/api/issues/{r1['id']}", headers=b).status_code == 200


def test_different_category_does_not_merge():
    h = _register(); lat, lon = rand_point()
    p = _report(h, lat, lon, "POTHOLE").json()
    g = _report(h, *offset(lat, lon, 5), itype="GARBAGE").json()
    assert p["id"] != g["id"] and g["merged"] is False


def test_far_report_is_a_separate_issue():
    h = _register(); lat, lon = rand_point()
    a = _report(h, lat, lon).json()
    b = _report(h, *offset(lat, lon, 500)).json()
    assert a["id"] != b["id"] and b["possible_duplicates"] == []


def test_citizen_cannot_see_duplicate_review_data(authority):
    h = _register(); lat, lon = rand_point()
    _report(h, lat, lon)
    near = _report(h, *offset(lat, lon, 40)).json()          # 40 m: review band
    assert near["merged"] is False and near["possible_duplicates"] == []     # hidden from citizens
    detail = client.get(f"/api/issues/{near['id']}", headers=authority).json()
    assert len(detail["possible_duplicates"]) == 1
    d = detail["possible_duplicates"][0]
    assert 30 < d["distance_meters"] < 50 and d["review_status"] == "PENDING"


def test_authority_confirms_duplicate_merge(authority):
    h = _register(); lat, lon = rand_point()
    first = _report(h, lat, lon).json()
    second = _report(h, *offset(lat, lon, 45)).json()
    dup = client.get(f"/api/issues/{second['id']}", headers=authority).json()["possible_duplicates"][0]
    r = client.post(f"/api/admin/duplicates/{dup['id']}/confirm", headers=authority)
    assert r.status_code == 200 and r.json()["result"] == "merged"
    merged = client.get(f"/api/issues/{first['id']}", headers=authority).json()
    assert merged["report_count"] == 2 and len(merged["reports"]) == 2
    assert client.get(f"/api/issues/{second['id']}", headers=authority).status_code == 404
    assert any(i["id"] == first["id"] for i in client.get("/api/issues/my", headers=h).json())


def test_authority_dismisses_duplicate(authority):
    h = _register(); lat, lon = rand_point()
    _report(h, lat, lon)
    second = _report(h, *offset(lat, lon, 50)).json()
    dup = client.get(f"/api/issues/{second['id']}", headers=authority).json()["possible_duplicates"][0]
    assert client.post(f"/api/admin/duplicates/{dup['id']}/dismiss", headers=authority).json()["result"] == "dismissed"
    assert client.post(f"/api/admin/duplicates/{dup['id']}/confirm", headers=authority).status_code == 404


# ---------- authority access ----------
def test_citizen_blocked_from_admin_endpoints():
    h = _register()
    assert client.get("/api/admin/dashboard", headers=h).status_code == 403
    assert client.get("/api/admin/issues", headers=h).status_code == 403
    assert client.patch("/api/admin/issues/1/assign", headers=h, json={}).status_code == 403
    assert client.get("/api/admin/issues").status_code == 401


# ---------- dashboard + list ----------
def test_dashboard_kpis_are_consistent(authority):
    d = client.get("/api/admin/dashboard", headers=authority).json()
    assert d["total"] == sum(d["by_status"].values()) == sum(d["by_category"].values())
    assert d["open"] + d["resolved"] == d["total"]
    assert set(d["by_category"]) == {"POTHOLE", "GARBAGE", "WATER_LEAKAGE", "STREETLIGHT"}
    assert {"Roads", "Sanitation", "Water", "Electrical"} <= set(d["by_department"])


def test_issue_list_filters_and_sorting(authority):
    h = _register(); lat, lon = rand_point()
    _report(h, lat, lon, "STREETLIGHT", address="Unique-Lane-" + uuid.uuid4().hex[:6])
    allrows = client.get("/api/admin/issues", headers=authority).json()
    scores = [r["priority_score"] for r in allrows]
    assert scores == sorted(scores, reverse=True)
    only = client.get("/api/admin/issues", headers=authority, params={"issue_type": "STREETLIGHT"}).json()
    assert only and all(r["issue_type"] == "STREETLIGHT" for r in only)
    assert all(r["department_name"] == "Electrical" for r in only)
    nothing = client.get("/api/admin/issues", headers=authority, params={"search": "zzz-no-such-text"}).json()
    assert nothing == []


# ---------- workflow ----------
def test_full_status_workflow(authority):
    h = _register(); lat, lon = rand_point()
    iid = _report(h, lat, lon, "WATER_LEAKAGE").json()["id"]
    url = f"/api/admin/issues/{iid}"
    # cannot skip steps, and resolve/verify have dedicated endpoints
    assert client.patch(f"{url}/status", headers=authority, json={"status": "RESOLVED"}).status_code == 422
    assert client.patch(f"{url}/status", headers=authority, json={"status": "ASSIGNED"}).status_code == 422
    assert client.post(f"{url}/resolve", headers=authority).status_code == 409          # not in progress yet
    r = client.patch(f"{url}/assign", headers=authority, json={"notes": "Ward officer Patil"})
    assert r.status_code == 200 and r.json()["department"] == "Water"
    assert client.patch(f"{url}/status", headers=authority, json={"status": "IN_PROGRESS"}).status_code == 200
    assert client.post(f"{url}/resolve", headers=authority, data={"notes": "Pipe repaired"}).status_code == 200
    assert client.post(f"{url}/verify", headers=authority, json={"approved": True}).status_code == 200
    d = client.get(f"/api/issues/{iid}", headers=authority).json()
    assert d["status"] == "VERIFIED" and d["resolved_at"] is not None
    assert [e["new_status"] for e in d["events"]] == ["REPORTED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "VERIFIED"]
    assert client.get(f"/api/issues/{iid}", headers=h).json()["status"] == "VERIFIED"
    assert client.patch(f"{url}/assign", headers=authority, json={}).status_code == 409


def test_reopen_clears_resolved_at(authority):
    h = _register(); lat, lon = rand_point()
    iid = _report(h, lat, lon, "GARBAGE").json()["id"]
    url = f"/api/admin/issues/{iid}"
    client.patch(f"{url}/assign", headers=authority, json={})
    client.patch(f"{url}/status", headers=authority, json={"status": "IN_PROGRESS"})
    client.post(f"{url}/resolve", headers=authority)
    assert client.patch(f"{url}/status", headers=authority, json={"status": "IN_PROGRESS", "comment": "Not fixed"}).status_code == 200
    d = client.get(f"/api/issues/{iid}", headers=authority).json()
    assert d["resolved_at"] is None and d["resolution"]["verification_status"] == "REJECTED"


def test_departments_list(authority):
    names = [d["name"] for d in client.get("/api/admin/departments", headers=authority).json()]
    assert {"Roads", "Sanitation", "Water", "Electrical"} <= set(names)


def test_unknown_issue_404(authority):
    assert client.patch("/api/admin/issues/99999999/assign", headers=authority, json={}).status_code == 404
