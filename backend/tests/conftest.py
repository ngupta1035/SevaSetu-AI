"""Shared test helpers and safety rails.

SAFETY: the suite creates many rows (users, issues, uploads). It therefore REFUSES to run unless
DATABASE_URL points at a database whose name contains "test" (e.g. sevasetu_test_db), so it can
never pollute the demo/application database. Override only if you really mean it:
    set SEVASETU_ALLOW_TESTS_ON_ANY_DB=1
"""
import math
import os
import random

import pytest
from sqlalchemy.engine import make_url


def _database_name() -> str:
    from app.core.config import settings
    return make_url(settings.DATABASE_URL).database or ""


def pytest_configure(config):
    if os.environ.get("SEVASETU_ALLOW_TESTS_ON_ANY_DB") == "1":
        return
    name = _database_name()
    if "test" not in name.lower():
        pytest.exit(
            f"\n\nRefusing to run tests against database '{name}'.\n"
            "Create a separate test database and point DATABASE_URL at it, for example:\n"
            "  psql -U postgres -c \"CREATE DATABASE sevasetu_test_db;\"\n"
            "  $env:DATABASE_URL = \"postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/sevasetu_test_db\"\n"
            "  python -m alembic upgrade head\n"
            "  python -m pytest -q tests\n",
            returncode=2,
        )


@pytest.fixture(scope="session", autouse=True)
def seeded_base_data():
    """Departments + demo authority/citizen accounts must exist (idempotent)."""
    from app.seed import run as seed
    seed()


def rand_point():
    """Random location in India so repeated test runs never merge with older rows."""
    return round(random.uniform(8, 33), 6), round(random.uniform(68, 96), 6)


def offset(lat, lon, metres_north=0.0, metres_east=0.0):
    return (round(lat + metres_north / 111320, 6),
            round(lon + metres_east / (111320 * math.cos(math.radians(lat))), 6))
