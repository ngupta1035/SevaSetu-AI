"""Run the test-suite and write docs/TEST_REPORT.md from the REAL results.

    python scripts/generate_test_report.py            (from backend/, venv active, DB running)
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

AREAS = OrderedDict([
    ("test_day2", "Authentication & issue reporting"),
    ("test_day4", "Priority engine & AI integration"),
    ("test_day5", "Duplicate detection & authority workflow"),
    ("test_day6", "Hotspots, analytics & resolution workflow"),
    ("test_day7_system", "System robustness & error handling"),
    ("test_day7_eval", "Evaluation harness & demo data"),
    ("test_day10_ai", "AI with/without weights (fake detectors)"),
])
OUT = Path(__file__).resolve().parents[2] / "docs" / "TEST_REPORT.md"


def environment():
    """Record what the run actually used (DB name, PostgreSQL/PostGIS versions)."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url
        from app.core.config import settings
        eng = create_engine(settings.DATABASE_URL)
        with eng.connect() as c:
            pg = c.execute(text("show server_version")).scalar()
            gis = c.execute(text("select postgis_lib_version()")).scalar()
        return make_url(settings.DATABASE_URL).database, pg, gis
    except Exception as e:  # report, don't crash
        return "unknown", "unknown", f"unknown ({type(e).__name__})"


def main():
    db, pg, gis = environment()
    xml = Path("test-results.xml")
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", f"--junitxml={xml}", "-p", "no:cacheprovider"],
                          capture_output=True, text=True)
    root = ET.parse(xml).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    cases = []
    for tc in suite.iter("testcase"):
        status = "FAIL" if (tc.find("failure") is not None or tc.find("error") is not None) else \
                 "SKIP" if tc.find("skipped") is not None else "PASS"
        mod = tc.get("classname", "").split(".")[-1]
        cases.append((mod, tc.get("name"), status, float(tc.get("time", 0))))
    total, passed = len(cases), sum(1 for c in cases if c[2] == "PASS")
    lines = ["# SevaSetu AI — Automated Test Report", "",
             f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ",
             f"Database used: `{db}` (PostgreSQL {pg}, PostGIS {gis})  ",
             "AI detector in these tests: **fake stand-in objects** (no model weights loaded)  ",
             f"Result: **{passed}/{total} passed** ({total - passed} failed/skipped), total time {sum(c[3] for c in cases):.1f} s", "",
             "Tests run against a real PostgreSQL + PostGIS database through the FastAPI test client. "
             "Route tests of the AI pipeline use a stand-in detector; real model performance is reported separately "
             "(see AI evaluation).", "",
             "## Summary by area", "", "| Area | Tests | Passed |", "|---|---|---|"]
    for mod, area in AREAS.items():
        rows = [c for c in cases if c[0] == mod]
        if rows:
            lines.append(f"| {area} | {len(rows)} | {sum(1 for r in rows if r[2] == 'PASS')} |")
    lines += ["", "## All tests", "", "| Area | Test | Result | Time (s) |", "|---|---|---|---|"]
    for mod, name, status, t in cases:
        lines.append(f"| {AREAS.get(mod, mod)} | `{name}` | {status} | {t:.2f} |")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    xml.unlink(missing_ok=True)
    print(proc.stdout.strip().splitlines()[-1])
    print(f"Wrote {OUT}")
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
