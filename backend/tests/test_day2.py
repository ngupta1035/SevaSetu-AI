import io
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from tests.conftest import rand_point

client = TestClient(app)


def _png() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (120, 120, 120)).save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def citizen():
    email = f"t{uuid.uuid4().hex[:8]}@test.com"
    r = client.post("/api/auth/register", json={"name": "Test User", "email": email, "password": "secret12"})
    assert r.status_code == 201
    r = client.post("/api/auth/login", data={"username": email, "password": "secret12"})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, email


def test_duplicate_email_rejected(citizen):
    _, email = citizen
    r = client.post("/api/auth/register", json={"name": "X Y", "email": email, "password": "secret12"})
    assert r.status_code == 409


def test_wrong_password():
    r = client.post("/api/auth/login", data={"username": "citizen@demo.sevasetu", "password": "nope"})
    assert r.status_code == 401


def test_requires_auth():
    assert client.get("/api/issues/my").status_code == 401


def test_create_and_fetch_issue(citizen):
    headers, _ = citizen
    r = client.post("/api/issues", headers=headers,
                    files={"image": ("p.png", _png(), "image/png")},
                    data={"latitude": (pt := rand_point())[0], "longitude": pt[1], "issue_type": "POTHOLE",
                          "description": "Large pothole near junction", "address": "Hinjewadi Phase 1"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["issue_code"].startswith("SS-")
    assert body["status"] == "REPORTED"
    assert body["department_name"] == "Roads"
    assert len(body["reports"]) == 1 and len(body["events"]) == 1

    assert client.get(f"/api/issues/{body['id']}", headers=headers).status_code == 200
    mine = client.get("/api/issues/my", headers=headers).json()
    assert any(i["id"] == body["id"] for i in mine)
    assert client.get(body["reports"][0]["image_url"]).status_code == 200  # served statically


def test_invalid_inputs(citizen):
    headers, _ = citizen
    base = {"latitude": 18.5, "longitude": 73.7, "issue_type": "GARBAGE"}
    # not an image
    r = client.post("/api/issues", headers=headers, files={"image": ("a.txt", b"hello", "text/plain")}, data=base)
    assert r.status_code == 415
    # fake image bytes
    r = client.post("/api/issues", headers=headers, files={"image": ("a.png", b"notreallyapng", "image/png")}, data=base)
    assert r.status_code == 400
    # bad coordinates
    r = client.post("/api/issues", headers=headers, files={"image": ("a.png", _png(), "image/png")},
                    data={**base, "latitude": 999})
    assert r.status_code == 422
    # missing location
    r = client.post("/api/issues", headers=headers, files={"image": ("a.png", _png(), "image/png")},
                    data={"issue_type": "GARBAGE"})
    assert r.status_code == 422


def test_citizen_cannot_view_others_issue(citizen):
    headers, _ = citizen
    other = f"o{uuid.uuid4().hex[:8]}@test.com"
    client.post("/api/auth/register", json={"name": "Other One", "email": other, "password": "secret12"})
    tok = client.post("/api/auth/login", data={"username": other, "password": "secret12"}).json()["access_token"]
    oh = {"Authorization": f"Bearer {tok}"}
    mine = client.get("/api/issues/my", headers=headers).json()
    assert client.get(f"/api/issues/{mine[0]['id']}", headers=oh).status_code == 403


def test_authority_can_view_any_issue(citizen):
    headers, _ = citizen
    mine = client.get("/api/issues/my", headers=headers).json()
    tok = client.post("/api/auth/login", data={"username": "authority@demo.sevasetu", "password": "demo1234"}).json()["access_token"]
    assert client.get(f"/api/issues/{mine[0]['id']}", headers={"Authorization": f"Bearer {tok}"}).status_code == 200
