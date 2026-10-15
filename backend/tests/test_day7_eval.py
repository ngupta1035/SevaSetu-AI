"""Evaluation-harness arithmetic and synthetic demo-data properties (pure, no DB)."""
import itertools
from pathlib import Path
from types import SimpleNamespace

from PIL import Image

from app.evaluation.run_eval import collect, summarize, to_markdown
from app.models.enums import IssueType, Severity
from app.seed_demo import _dist, build_plan
from app.services.hotspot_service import Point, find_hotspots


def rec(truth, pred, conf=0.8, model_ms=20.0, wall_ms=50.0):
    return {"file": "x.jpg", "truth": truth, "pred": pred, "confidence": conf if pred else None,
            "severity": "HIGH" if pred else None, "model_ms": model_ms if pred else None, "wall_ms": wall_ms}


def test_summary_math():
    records = ([rec("POTHOLE", "POTHOLE")] * 3 + [rec("POTHOLE", None)]
               + [rec("GARBAGE", None)] * 2
               + [rec("STREETLIGHT", "POTHOLE")]
               + [rec("NONE", None)] * 3 + [rec("NONE", "POTHOLE")])
    s = summarize(records)
    assert s["images"] == 11
    assert s["per_class"]["POTHOLE"]["recall"] == 0.75 and s["per_class"]["POTHOLE"]["not_detected"] == 1
    assert s["per_class"]["GARBAGE"]["recall"] == 0.0
    assert s["per_class"]["STREETLIGHT"]["confused_with_other_class"] == 1
    assert s["per_class"]["NONE"]["false_positive_rate"] == 0.25
    assert s["precision_by_predicted_class"]["POTHOLE"] == {"predicted": 5, "precision": 0.6}
    assert s["overall_category_accuracy"] == round(3 / 7, 3)
    assert s["confusion_matrix_truth_to_prediction"]["POTHOLE"] == {"POTHOLE": 3, "none": 1}


def test_latency_stats_and_markdown():
    s = summarize([rec("POTHOLE", "POTHOLE", model_ms=m, wall_ms=m * 2) for m in (10, 20, 30, 40)])
    assert s["latency_ms"]["model_mean"] == 25.0 and s["latency_ms"]["end_to_end_mean"] == 50.0
    md = to_markdown(s, {"model": "m", "threshold": 0.25, "data": "d", "note": "n"})
    assert "model confidence" in md and "| POTHOLE |" in md


def test_collect_reads_folder_labels(tmp_path):
    for folder, n in (("pothole", 2), ("garbage", 1), ("negative", 1), ("ignored_folder", 1)):
        (tmp_path / folder).mkdir()
        for k in range(n):
            Image.new("RGB", (8, 8)).save(tmp_path / folder / f"{k}.png")

    def fake(path):
        if "pothole" in path:
            return SimpleNamespace(issue_type=IssueType.POTHOLE, confidence=0.9, severity=Severity.HIGH, inference_time_ms=12.0)
        return None

    recs = collect(tmp_path, fake)
    assert len(recs) == 4 and {r["truth"] for r in recs} == {"POTHOLE", "GARBAGE", "NONE"}
    assert [r["pred"] for r in recs if r["truth"] == "POTHOLE"] == ["POTHOLE", "POTHOLE"]


# ---------- synthetic demo data ----------
def test_demo_plan_is_deterministic_and_sized():
    a, b = build_plan(7), build_plan(7)
    assert [(s.lat, s.lon, s.status) for s in a] == [(s.lat, s.lon, s.status) for s in b]
    assert 45 <= len(a) <= 55
    assert all("[synthetic demo]" in s.description for s in a)


def test_demo_hero_scenario():
    hero = build_plan(7)[0]
    assert hero.issue_type == "POTHOLE" and hero.reports == 7 and hero.status == "REPORTED" and hero.severity == "HIGH"
    assert "Hinjewadi" in hero.address


def test_demo_data_yields_exactly_three_named_hotspots():
    plan = build_plan(7)
    open_pts = [Point(i, s.lat, s.lon, s.issue_type, 50, s.reports, s.address)
                for i, s in enumerate(plan) if s.status in ("REPORTED", "ASSIGNED", "IN_PROGRESS")]
    hs = find_hotspots(open_pts, 250, 3)
    assert [h["label"] for h in hs] == ["Hinjewadi Phase 1", "Hinjewadi Phase 2", "Wakad"]


def test_demo_spacing_and_status_mix():
    plan = build_plan(7)
    pair = [s for s in plan if s.extra.get("pair_key")]
    assert len(pair) == 2 and 40 < _dist((pair[0].lat, pair[0].lon), (pair[1].lat, pair[1].lon)) < 50
    for a, b in itertools.combinations(plan, 2):
        if a.extra.get("pair_key") and b.extra.get("pair_key"):
            continue
        assert _dist((a.lat, a.lon), (b.lat, b.lon)) >= 60            # separate issues, none would auto-merge
    statuses = {s.status for s in plan}
    assert statuses == {"REPORTED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "VERIFIED"}
