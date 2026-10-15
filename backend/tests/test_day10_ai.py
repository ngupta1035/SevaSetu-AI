"""AI behaviour with and without model weights.

These use fake detector objects (no weights, no GPU). They prove the *application logic*:
  - no weights  -> the app says so, never fabricates a detection, falls back to manual category
  - detections of classes we cannot map to a civic category are ignored
  - mapped detections are chosen by confidence and drive category/severity
They say nothing about real-world model accuracy -- that needs the evaluation harness + trained weights.
"""
import io
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services import ai_service
from app.services.ai_service import Detection, YoloDetector, analyze_image
from tests.conftest import rand_point

client = TestClient(app)


class FakeDetector:
    """Stands in for YoloDetector: same public surface (name, available, detect)."""

    def __init__(self, detections, available=True, boom=False):
        self.name, self._dets, self._available, self._boom = "fake-detector", detections, available, boom

    def available(self):
        return self._available

    def detect(self, image_path, conf):
        if self._boom:
            raise RuntimeError("model exploded")
        return list(self._dets), 12.5


def _png():
    buf = io.BytesIO()
    Image.new("RGB", (48, 48), (90, 90, 90)).save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture
def headers():
    email = f"ai{uuid.uuid4().hex[:8]}@test.com"
    client.post("/api/auth/register", json={"name": "AI Tester", "email": email, "password": "secret12"})
    tok = client.post("/api/auth/login", data={"username": email, "password": "secret12"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def use(monkeypatch, detector):
    monkeypatch.setattr(ai_service, "_detector", detector)


def submit(headers, **data):
    lat, lon = rand_point()
    return client.post("/api/issues", headers=headers, files={"image": ("p.png", _png(), "image/png")},
                       data={"latitude": lat, "longitude": lon, **data})


# ---------------- weights absent ----------------
def test_real_detector_reports_unavailable_when_weights_missing(monkeypatch, tmp_path):
    use(monkeypatch, YoloDetector(str(tmp_path / "does_not_exist.pt")))
    assert ai_service.status()["model_loaded"] is False
    assert analyze_image("any.jpg") is None          # never touches the image or imports ultralytics


def test_no_weights_means_no_detection_and_manual_category_works(monkeypatch, headers, tmp_path):
    use(monkeypatch, YoloDetector(str(tmp_path / "missing.pt")))
    st = client.get("/api/ai/status", headers=headers).json()
    assert st["model_loaded"] is False and st["model_name"] is None
    prev = client.post("/api/ai/analyze", headers=headers, files={"image": ("p.png", _png(), "image/png")}).json()
    assert prev["detected"] is False and prev["result"] is None
    # AI-only submission (no category) is refused with a clear message...
    r = submit(headers)
    assert r.status_code == 422 and "select the issue type" in r.json()["detail"]
    # ...and a manual category still works, with NO fabricated AI fields
    ok = submit(headers, issue_type="GARBAGE").json()
    assert ok["model_confidence"] is None and ok["predictions"] == []
    assert ok["priority_breakdown"]["severity_source"].startswith("default")


def test_inference_crash_is_swallowed_not_fatal(monkeypatch, headers):
    use(monkeypatch, FakeDetector([], boom=True))
    assert analyze_image("x.jpg") is None
    assert submit(headers, issue_type="POTHOLE").status_code == 201


# ---------------- unmapped classes ----------------
def test_unmapped_class_is_ignored_even_at_high_confidence(monkeypatch, headers):
    use(monkeypatch, FakeDetector([Detection("person", 0.99, 0.30), Detection("bus", 0.97, 0.40)]))
    assert analyze_image("x.jpg") is None
    prev = client.post("/api/ai/analyze", headers=headers, files={"image": ("p.png", _png(), "image/png")}).json()
    assert prev["detected"] is False
    assert submit(headers).status_code == 422        # cannot invent a civic category from a "bus"


def test_mapped_class_wins_over_higher_confidence_unmapped_class(monkeypatch):
    use(monkeypatch, FakeDetector([Detection("person", 0.99, 0.30), Detection("D40", 0.55, 0.06)]))
    res = analyze_image("x.jpg")
    assert res.predicted_class == "D40" and res.issue_type.value == "POTHOLE" and abs(res.confidence - 0.55) < 1e-9
    assert len(res.detections) == 1                  # the unmapped detection was dropped


# ---------------- weights present (fake) ----------------
def test_mapped_detection_drives_category_severity_and_prediction_row(monkeypatch, headers):
    use(monkeypatch, FakeDetector([Detection("D40", 0.91, 0.07), Detection("D00", 0.60, 0.02)]))
    st = client.get("/api/ai/status", headers=headers).json()
    assert st["model_loaded"] is True and st["model_name"] == "fake-detector"
    b = submit(headers).json()                       # no category given -> AI decides
    assert b["issue_type"] == "POTHOLE" and b["department_name"] == "Roads"
    assert b["severity"] == "HIGH" and abs(b["model_confidence"] - 0.91) < 1e-6
    p = b["predictions"][0]
    assert p["predicted_class"] == "D40" and p["model_name"] == "fake-detector" and p["inference_time_ms"] == 12.5
    assert b["priority_breakdown"]["severity_source"] == "ai"


def test_user_category_overrides_ai_but_prediction_is_kept(monkeypatch, headers):
    use(monkeypatch, FakeDetector([Detection("D40", 0.91, 0.07)]))
    b = submit(headers, issue_type="STREETLIGHT").json()
    assert b["issue_type"] == "STREETLIGHT" and b["department_name"] == "Electrical"
    assert b["predictions"][0]["predicted_class"] == "D40"
    assert b["priority_breakdown"]["severity_source"].startswith("default")   # AI severity not applied across categories
