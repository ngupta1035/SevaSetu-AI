"""Controlled evaluation of the deployed AI pipeline on a labelled image folder.

    data/validation/
        pothole/*.jpg   garbage/*.jpg   leakage/*.jpg   streetlight/*.jpg
        negative/*.jpg  (optional: road/street photos with NO civic issue)

    python -m app.evaluation.run_eval --data ../data/validation --out ../docs/ai_eval_app

It runs the SAME code path the app uses (ai_service.analyze_image) and reports what it
actually measured. Categories the loaded model was not trained for will simply show as
"not detected" -- the report says so rather than hiding it.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

FOLDER_TO_LABEL = {"pothole": "POTHOLE", "garbage": "GARBAGE", "leakage": "WATER_LEAKAGE",
                   "water_leakage": "WATER_LEAKAGE", "streetlight": "STREETLIGHT", "negative": "NONE"}
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}
LABELS = ["POTHOLE", "GARBAGE", "WATER_LEAKAGE", "STREETLIGHT"]


def _pct(values, q):
    if not values:
        return None
    v = sorted(values)
    return round(v[min(len(v) - 1, int(round(q * (len(v) - 1))))], 1)


def summarize(records: list[dict]) -> dict:
    """records: {file, truth, pred (label or None), confidence, severity, model_ms, wall_ms}.
    Pure function -- all the arithmetic is unit-tested."""
    per_class, confusion = {}, {}
    for lab in LABELS + ["NONE"]:
        rows = [r for r in records if r["truth"] == lab]
        if not rows:
            continue
        n = len(rows)
        correct = sum(1 for r in rows if r["pred"] == lab)
        wrong = sum(1 for r in rows if r["pred"] not in (None, lab))
        missed = sum(1 for r in rows if r["pred"] is None)
        if lab == "NONE":
            per_class[lab] = {"images": n, "false_positives": n - missed,
                              "false_positive_rate": round((n - missed) / n, 3)}
        else:
            per_class[lab] = {"images": n, "detected_correctly": correct, "confused_with_other_class": wrong,
                              "not_detected": missed, "recall": round(correct / n, 3)}
        confusion[lab] = {}
        for r in rows:
            k = r["pred"] or "none"
            confusion[lab][k] = confusion[lab].get(k, 0) + 1

    precision = {}
    for lab in LABELS:
        predicted = [r for r in records if r["pred"] == lab]
        if predicted:
            precision[lab] = {"predicted": len(predicted),
                              "precision": round(sum(1 for r in predicted if r["truth"] == lab) / len(predicted), 3)}

    issue_rows = [r for r in records if r["truth"] != "NONE"]
    wall = [r["wall_ms"] for r in records if r.get("wall_ms") is not None]
    model = [r["model_ms"] for r in records if r.get("model_ms") is not None]
    conf = [r["confidence"] for r in records if r.get("confidence") is not None]
    return {
        "images": len(records),
        "per_class": per_class,
        "precision_by_predicted_class": precision,
        "confusion_matrix_truth_to_prediction": confusion,
        "overall_category_accuracy": round(sum(1 for r in issue_rows if r["pred"] == r["truth"]) / len(issue_rows), 3) if issue_rows else None,
        "latency_ms": {"model_mean": round(statistics.mean(model), 1) if model else None,
                       "model_p95": _pct(model, 0.95),
                       "end_to_end_mean": round(statistics.mean(wall), 1) if wall else None,
                       "end_to_end_p95": _pct(wall, 0.95)},
        "mean_model_confidence_when_detected": round(statistics.mean(conf), 3) if conf else None,
    }


def to_markdown(summary: dict, meta: dict) -> str:
    L = ["# AI evaluation (application pipeline)", "",
         f"- Model: `{meta.get('model')}`  |  confidence threshold: {meta.get('threshold')}",
         f"- Images evaluated: {summary['images']}  |  data folder: `{meta.get('data')}`",
         "- Confidence values are **model confidence**, not accuracy.",
         f"- Note: {meta.get('note')}", "",
         "## Per-class results", "", "| Class (truth) | Images | Detected correctly | Confused | Not detected | Recall / FP-rate |",
         "|---|---|---|---|---|---|"]
    for lab, v in summary["per_class"].items():
        if lab == "NONE":
            L.append(f"| NONE (negatives) | {v['images']} | – | {v['false_positives']} (false positives) | – | FP rate {v['false_positive_rate']} |")
        else:
            L.append(f"| {lab} | {v['images']} | {v['detected_correctly']} | {v['confused_with_other_class']} | {v['not_detected']} | {v['recall']} |")
    L += ["", "## Precision by predicted class", "", "| Predicted class | Predictions | Precision |", "|---|---|---|"]
    for lab, v in summary["precision_by_predicted_class"].items():
        L.append(f"| {lab} | {v['predicted']} | {v['precision']} |")
    lat = summary["latency_ms"]
    L += ["", "## Latency", "", f"- Model inference: mean {lat['model_mean']} ms, p95 {lat['model_p95']} ms",
          f"- End to end (incl. image load): mean {lat['end_to_end_mean']} ms, p95 {lat['end_to_end_p95']} ms",
          f"- Overall category accuracy (issue images only): {summary['overall_category_accuracy']}", ""]
    return "\n".join(L)


def collect(data_dir: Path, analyze) -> list[dict]:
    records = []
    for folder in sorted(p for p in data_dir.iterdir() if p.is_dir()):
        truth = FOLDER_TO_LABEL.get(folder.name.lower())
        if truth is None:
            continue
        for img in sorted(p for p in folder.iterdir() if p.suffix.lower() in IMG_EXT):
            t0 = time.perf_counter()
            res = analyze(str(img))
            wall = (time.perf_counter() - t0) * 1000
            records.append({
                "file": f"{folder.name}/{img.name}", "truth": truth,
                "pred": res.issue_type.value if res and res.issue_type else None,
                "confidence": res.confidence if res else None,
                "severity": res.severity.value if res else None,
                "model_ms": res.inference_time_ms if res else None, "wall_ms": round(wall, 1)})
    return records


def main():
    from app.core.config import settings
    from app.services import ai_service
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    default_out = Path(__file__).resolve().parents[3] / "docs" / "ai_eval_app"   # <repo>/docs/ai_eval_app
    ap.add_argument("--out", default=str(default_out), help="output path without extension (.json and .md are written)")
    a = ap.parse_args()
    st = ai_service.status()
    if not st["model_loaded"]:
        raise SystemExit("No model loaded (check MODEL_PATH / ultralytics install). Nothing to evaluate.")
    records = collect(Path(a.data), ai_service.analyze_image)
    if not records:
        raise SystemExit("No labelled images found. Expected sub-folders: pothole, garbage, leakage, streetlight, negative.")
    summary = summarize(records)
    meta = {"model": st["model_name"], "threshold": settings.AI_CONF_THRESHOLD, "data": str(a.data),
            "note": "Classes the model was not trained on are expected to show as not detected."}
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".json").write_text(json.dumps({"meta": meta, "summary": summary, "records": records}, indent=2))
    out.with_suffix(".md").write_text(to_markdown(summary, meta))
    print(to_markdown(summary, meta))


if __name__ == "__main__":
    main()
