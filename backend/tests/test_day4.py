"""Day 4: priority engine, severity heuristic, AI integration.
The route tests use a TEST DOUBLE in place of the YOLO model (no weights needed);
real-model behaviour is measured separately in the evaluation step."""
import io
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from tests.conftest import rand_point
from app.models.enums import IssueType, Severity
from app.services import ai_service
from app.services import priority_service as ps

client = TestClient(app)


# ---------- priority engine ----------
def test_blueprint_example_scores_81_25():
    assert ps.weighted_score(90, 80, 90, 75, 60) == 81.25


def test_weights_sum_to_one():
    assert round(sum(ps.WEIGHTS.values()), 6) == 1.0


def test_frequency_and_time_scores():
    assert ps.frequency_score(1) == 20 and ps.frequency_score(3) == 50 and ps.frequency_score(20) == 100
    now = datetime.now(timezone.utc)
    assert ps.time_score(now, now) == 0
    assert ps.time_score(now - timedelta(hours=36), now) == 50
    assert ps.time_score(now - timedelta(days=10), now) == 100


def test_location_keywords():
    assert ps.location_score("Near City Hospital", None) == 90
    assert ps.location_score(None, "on main road") == 65
    assert ps.location_score("quiet lane", "") == 40


# ---------- severity heuristic ----------
def test_severity_levels():
    big = [ai_service.Detection("D40", 0.9, 0.06)]
    small = [ai_service.Detection("D40", 0.9, 0.01)]
    crack = [ai_service.Detection("D00", 0.9, 0.03)]
    assert ai_service.severity_from_detections(big)[0] == Severity.HIGH
    assert ai_service.severity_from_detections(small)[0] == Severity.MEDIUM
    assert ai_service.severity_from_detections(crack)[0] == Severity.LOW


# ---------- routes ----------
def _png():
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (90, 90, 90)).save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def headers():
    email = f"a{uuid.uuid4().hex[:8]}@test.com"
    client.post("/api/auth/register", json={"name": "Ai Tester", "email": email, "password": "secret12"})
    tok = client.post("/api/auth/login", data={"username": email, "password": "secret12"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def _fake_result(label="D40", conf=0.91, area=0.06, itype=IssueType.POTHOLE):
    dets = [ai_service.Detection(label, conf, area)]
    sev, score = ai_service.severity_from_detections(dets)
    return ai_service.AIResult("test-double", "v0", dets, label, itype, conf, sev, score, 12.0)


def _submit(headers, data):
    lat, lon = rand_point()
    return client.post("/api/issues", headers=headers,
                       files={"image": ("p.png", _png(), "image/png")},
                       data={"latitude": lat, "longitude": lon, **data})


def test_ai_status_without_weights(headers):
    r = client.get("/api/ai/status", headers=headers)
    assert r.status_code == 200 and r.json()["model_loaded"] is False


def test_no_type_and_no_ai_is_rejected(headers, monkeypatch):
    monkeypatch.setattr(ai_service, "analyze_image", lambda p: None)
    r = _submit(headers, {})
    assert r.status_code == 422 and "select the issue type" in r.json()["detail"]


def test_manual_type_without_ai_gets_default_severity(headers, monkeypatch):
    monkeypatch.setattr(ai_service, "analyze_image", lambda p: None)
    r = _submit(headers, {"issue_type": "GARBAGE"})
    assert r.status_code == 201
    b = r.json()
    assert b["severity"] == "MEDIUM" and b["model_confidence"] is None
    assert b["priority_breakdown"]["severity_source"].startswith("default")
    assert b["predictions"] == [] and b["department_name"] == "Sanitation"


def test_ai_detects_type_and_scores_priority(headers, monkeypatch):
    monkeypatch.setattr(ai_service, "analyze_image", lambda p: _fake_result())
    r = _submit(headers, {"description": "Large pothole near the junction"})   # no type given
    assert r.status_code == 201, r.text
    b = r.json()
    assert b["issue_type"] == "POTHOLE" and b["department_name"] == "Roads"
    assert b["severity"] == "HIGH" and abs(b["model_confidence"] - 0.91) < 1e-6
    assert b["predictions"][0]["predicted_class"] == "D40"
    comp = b["priority_breakdown"]["components"]
    assert comp["severity"] == 90 and comp["location"] == 90 and comp["frequency"] == 20
    expected = ps.weighted_score(90, 20, 90, 70, comp["time"])
    assert abs(b["priority_score"] - expected) < 0.01


def test_user_type_wins_but_prediction_is_kept(headers, monkeypatch):
    monkeypatch.setattr(ai_service, "analyze_image", lambda p: _fake_result())
    r = _submit(headers, {"issue_type": "GARBAGE"})
    b = r.json()
    assert b["issue_type"] == "GARBAGE" and b["predictions"][0]["predicted_class"] == "D40"
    assert b["priority_breakdown"]["severity_source"].startswith("default")   # AI severity not applied to a different category


def test_analyze_preview_endpoint(headers, monkeypatch):
    monkeypatch.setattr(ai_service, "analyze_image", lambda p: _fake_result())
    r = client.post("/api/ai/analyze", headers=headers, files={"image": ("p.png", _png(), "image/png")})
    assert r.status_code == 200
    j = r.json()
    assert j["detected"] and j["result"]["issue_type"] == "POTHOLE" and j["result"]["severity"] == "HIGH"
