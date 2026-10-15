"""Day 6: hotspot clustering, map/analytics endpoints, resolution workflow with photos."""
import io
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services import ai_service
from app.services.hotspot_service import Point, dbscan, find_hotspots, haversine_m
from tests.conftest import offset, rand_point

client = TestClient(app)


def _png(color=(80, 80, 80)):
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(buf, "PNG")
    return buf.getvalue()


# ---------- hotspot algorithm (pure) ----------
def test_haversine_known_distance():
    # 0.001 deg latitude is ~111 m
    assert 108 < haversine_m(18.0, 73.0, 18.001, 73.0) < 114


def _pt(i, lat, lon, prio=50, addr=None, t="POTHOLE"):
    return Point(i, lat, lon, t, prio, 1, addr, f"SS-{i}")


def test_dbscan_finds_cluster_and_ignores_noise():
    lat, lon = 18.59, 73.74
    cluster = [_pt(i, *offset(lat, lon, i * 80)) for i in range(4)]      # 0..240 m chain
    far = [_pt(10, *offset(lat, lon, 5000)), _pt(11, *offset(lat, lon, 9000, 9000))]
    groups = dbscan(cluster + far, eps_m=120, min_points=3)
    assert len(groups) == 1 and sorted(groups[0]) == [0, 1, 2, 3]


def test_chain_connects_through_density():
    lat, lon = 18.0, 73.0
    pts = [_pt(i, *offset(lat, lon, i * 100)) for i in range(6)]         # 500 m chain, eps 150
    assert len(dbscan(pts, eps_m=150, min_points=3)) == 1


def test_two_separate_clusters():
    a = [_pt(i, *offset(18.0, 73.0, i * 40)) for i in range(3)]
    b = [_pt(10 + i, *offset(18.1, 73.1, i * 40)) for i in range(3)]
    assert len(dbscan(a + b, eps_m=100, min_points=3)) == 2


def test_hotspot_summary_fields():
    pts = [_pt(i, *offset(18.59, 73.74, i * 60), prio=60 + i * 10, addr="Hinjewadi Phase 1") for i in range(3)]
    h = find_hotspots(pts, eps_m=150, min_points=3)[0]
    assert h["label"] == "Hinjewadi Phase 1" and h["issue_count"] == 3 and h["rank"] == 1
    assert h["max_priority"] == 80 and h["avg_priority"] == 70 and h["radius_m"] >= 60


def test_too_few_points_no_hotspot():
    assert find_hotspots([_pt(1, 18, 73), _pt(2, 18.0001, 73)], 250, 3) == []


# ---------- API ----------
def _register():
    email = f"m{uuid.uuid4().hex[:8]}@test.com"
    client.post("/api/auth/register", json={"name": "Map Tester", "email": email, "password": "secret12"})
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


def test_map_endpoint_detects_hotspot(authority):
    h = _register(); lat, lon = rand_point()
    ids = [_report(h, *offset(lat, lon, i * 90), address="Test Hotspot Rd").json()["id"] for i in range(3)]
    assert len(set(ids)) == 3                      # 90 m apart: separate issues
    m = client.get("/api/admin/map", headers=authority, params={"eps_m": 150, "min_points": 3}).json()
    mine = [x for x in m["hotspots"] if set(ids) <= set(x["issue_ids"])]
    assert len(mine) == 1 and mine[0]["label"] == "Test Hotspot Rd" and mine[0]["issue_count"] == 3
    assert {x["id"] for x in m["issues"]} >= set(ids)
    only_garbage = client.get("/api/admin/map", headers=authority, params={"issue_type": "GARBAGE"}).json()
    assert all(x["type"] == "GARBAGE" for x in only_garbage["issues"])


def test_map_requires_authority():
    assert client.get("/api/admin/map", headers=_register()).status_code == 403


def test_analytics_trend(authority):
    h = _register(); lat, lon = rand_point()
    _report(h, lat, lon, "STREETLIGHT")
    a = client.get("/api/admin/analytics", headers=authority, params={"days": 7}).json()
    assert len(a["trend"]) == 7
    assert a["trend"][-1]["reported"] >= 1            # today's report is counted
    assert all(set(t) == {"date", "reported", "resolved"} for t in a["trend"])


# ---------- resolution workflow ----------
def _to_in_progress(authority, h, itype="POTHOLE"):
    lat, lon = rand_point()
    iid = _report(h, lat, lon, itype).json()["id"]
    client.patch(f"/api/admin/issues/{iid}/assign", headers=authority, json={})
    client.patch(f"/api/admin/issues/{iid}/status", headers=authority, json={"status": "IN_PROGRESS"})
    return iid


def test_resolve_with_after_photo_and_verify(authority):
    h = _register()
    iid = _to_in_progress(authority, h)
    r = client.post(f"/api/admin/issues/{iid}/resolve", headers=authority,
                    data={"notes": "Filled and levelled"},
                    files={"after_image": ("after.png", _png((200, 200, 200)), "image/png")})
    assert r.status_code == 200 and r.json()["after_image_url"].startswith("/uploads/")
    d = client.get(f"/api/issues/{iid}", headers=h).json()          # visible to the citizen
    res = d["resolution"]
    assert d["status"] == "RESOLVED" and res["verification_status"] == "PENDING"
    assert res["before_image_url"] == d["reports"][0]["image_url"] and res["after_image_url"]
    assert client.get(res["after_image_url"]).status_code == 200
    assert client.post(f"/api/admin/issues/{iid}/verify", headers=authority, json={"approved": True, "comment": "Checked on site"}).status_code == 200
    d = client.get(f"/api/issues/{iid}", headers=h).json()
    assert d["status"] == "VERIFIED" and d["resolution"]["verification_status"] == "VERIFIED"
    assert d["resolution"]["verified_at"] is not None


def test_rejected_resolution_reopens_issue(authority):
    h = _register()
    iid = _to_in_progress(authority, h, "GARBAGE")
    client.post(f"/api/admin/issues/{iid}/resolve", headers=authority)          # no photo is allowed
    r = client.post(f"/api/admin/issues/{iid}/verify", headers=authority, json={"approved": False, "comment": "Still littered"})
    assert r.status_code == 200 and r.json()["status"] == "IN_PROGRESS"
    d = client.get(f"/api/issues/{iid}", headers=authority).json()
    assert d["resolved_at"] is None and d["resolution"]["verification_status"] == "REJECTED"
    assert "Still littered" in d["events"][-1]["comment"]


def test_resolve_rejects_bad_photo_and_wrong_state(authority):
    h = _register()
    iid = _to_in_progress(authority, h)
    bad = client.post(f"/api/admin/issues/{iid}/resolve", headers=authority,
                      files={"after_image": ("a.png", b"not-an-image", "image/png")})
    assert bad.status_code == 400
    assert client.get(f"/api/issues/{iid}", headers=authority).json()["status"] == "IN_PROGRESS"   # unchanged
    assert client.post(f"/api/admin/issues/{iid}/verify", headers=authority, json={"approved": True}).status_code == 409
    client.post(f"/api/admin/issues/{iid}/resolve", headers=authority)
    assert client.post(f"/api/admin/issues/{iid}/resolve", headers=authority).status_code == 409   # already resolved


def test_citizen_cannot_resolve_or_verify():
    h = _register()
    assert client.post("/api/admin/issues/1/resolve", headers=h).status_code == 403
    assert client.post("/api/admin/issues/1/verify", headers=h, json={"approved": True}).status_code == 403
