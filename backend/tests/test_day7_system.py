"""System / robustness tests: bad tokens, bad input, abuse attempts, duplicate submissions."""
import io
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from PIL import Image

from app.core.config import settings
from app.main import app
from app.services import ai_service
from tests.conftest import rand_point

client = TestClient(app)


def _png():
    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (70, 70, 70)).save(buf, "PNG")
    return buf.getvalue()


def _user():
    email = f"s{uuid.uuid4().hex[:8]}@test.com"
    client.post("/api/auth/register", json={"name": "Sys Tester", "email": email, "password": "secret12"})
    tok = client.post("/api/auth/login", data={"username": email, "password": "secret12"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


@pytest.fixture(autouse=True)
def no_ai(monkeypatch):
    monkeypatch.setattr(ai_service, "analyze_image", lambda p: None)


def _post(h, files=None, **data):
    lat, lon = rand_point()
    base = {"latitude": lat, "longitude": lon, "issue_type": "POTHOLE"}
    base.update(data)
    return client.post("/api/issues", headers=h, files=files or {"image": ("p.png", _png(), "image/png")},
                       data={k: v for k, v in base.items() if v is not None})


# ---------- authentication ----------
def test_bad_tokens_are_rejected():
    now = datetime.now(timezone.utc)
    cases = {
        "garbage": "not.a.jwt",
        "wrong_secret": jwt.encode({"sub": "1", "exp": now + timedelta(hours=1)}, "other-secret", algorithm="HS256"),
        "expired": jwt.encode({"sub": "1", "exp": now - timedelta(hours=1)}, settings.SECRET_KEY, algorithm="HS256"),
        "unknown_user": jwt.encode({"sub": "999999999", "exp": now + timedelta(hours=1)}, settings.SECRET_KEY, algorithm="HS256"),
        "non_numeric_sub": jwt.encode({"sub": "abc", "exp": now + timedelta(hours=1)}, settings.SECRET_KEY, algorithm="HS256"),
    }
    for name, tok in cases.items():
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 401, name


@pytest.mark.parametrize("path", ["/api/auth/me", "/api/issues/my", "/api/issues/1", "/api/ai/status",
                                  "/api/admin/dashboard", "/api/admin/issues", "/api/admin/map", "/api/admin/analytics"])
def test_protected_routes_need_a_token(path):
    assert client.get(path).status_code == 401


def test_register_validation_and_no_privilege_escalation():
    assert client.post("/api/auth/register", json={"name": "A B", "email": "bad", "password": "secret12"}).status_code == 422
    assert client.post("/api/auth/register", json={"name": "A B", "email": "x@y.com", "password": "123"}).status_code == 422
    assert client.post("/api/auth/register", json={"name": "A B", "email": "x@y.com", "password": "p" * 100}).status_code == 422
    email = f"e{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/api/auth/register", json={"name": "Evil User", "email": email, "password": "secret12", "role": "ADMIN"})
    assert r.status_code == 201 and r.json()["role"] == "CITIZEN"


# ---------- input validation ----------
def test_report_input_validation():
    h = _user()
    assert _post(h, latitude="north").status_code == 422
    assert _post(h, longitude=181).status_code == 422
    assert _post(h, issue_type="DRAGON").status_code == 422
    assert _post(h, description="x" * 1001).status_code == 422
    assert client.post("/api/issues", headers=h, data={"latitude": 18, "longitude": 73, "issue_type": "POTHOLE"}).status_code == 422  # no image


def test_oversized_image_rejected():
    h = _user()
    big = b"\x89PNG" + b"0" * (9 * 1024 * 1024)
    assert _post(h, files={"image": ("big.png", big, "image/png")}).status_code == 413


def test_non_image_and_empty_uploads_rejected():
    h = _user()
    assert _post(h, files={"image": ("a.exe", b"MZ....", "application/octet-stream")}).status_code == 415
    assert _post(h, files={"image": ("e.png", b"", "image/png")}).status_code == 400


def test_pagination_bounds_enforced():
    tok = client.post("/api/auth/login", data={"username": "authority@demo.sevasetu", "password": "demo1234"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    assert client.get("/api/admin/issues", headers=h, params={"limit": 0}).status_code == 422
    assert client.get("/api/admin/issues", headers=h, params={"limit": 501}).status_code == 422
    assert client.get("/api/admin/issues", headers=h, params={"sort": "random"}).status_code == 422


# ---------- abuse attempts ----------
def test_sql_injection_in_search_is_inert():
    tok = client.post("/api/auth/login", data={"username": "authority@demo.sevasetu", "password": "demo1234"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    for payload in ("'; DROP TABLE civic_issues; --", "' OR '1'='1", "%' OR 1=1 --"):
        r = client.get("/api/admin/issues", headers=h, params={"search": payload})
        assert r.status_code == 200 and r.json() == []
    assert client.get("/api/admin/dashboard", headers=h).status_code == 200      # tables still there


def test_uploads_path_traversal_blocked():
    for path in ("/uploads/../.env", "/uploads/%2e%2e/.env", "/uploads/..%2f..%2fapp/main.py"):
        r = client.get(path)
        assert r.status_code in (400, 404) and "SECRET_KEY" not in r.text


def test_markup_in_description_is_returned_as_plain_data():
    h = _user()
    payload = "<script>alert(1)</script>"
    r = _post(h, description=payload)
    assert r.status_code == 201 and r.json()["description"] == payload          # stored verbatim; React escapes on render
    assert r.headers["content-type"].startswith("application/json")


# ---------- duplicate submissions ----------
def test_same_citizen_double_submit_merges_instead_of_duplicating():
    h = _user(); lat, lon = rand_point()
    first = _post(h, latitude=lat, longitude=lon).json()
    again = _post(h, latitude=lat, longitude=lon).json()
    assert again["id"] == first["id"] and again["merged"] is True and again["report_count"] == 2
    assert len(client.get("/api/issues/my", headers=h).json()) == 1


def test_missing_location_message_is_clear():
    h = _user()
    r = client.post("/api/issues", headers=h, files={"image": ("p.png", _png(), "image/png")}, data={"issue_type": "POTHOLE"})
    assert r.status_code == 422
    fields = {e["loc"][-1] for e in r.json()["detail"]}
    assert {"latitude", "longitude"} <= fields
