"""AI inference for citizen photos.

The detector is a YOLO model trained on public road-damage imagery (RDD2022).
If the weights file is missing or `ultralytics` is not installed, the service
reports itself as unavailable and the app falls back to the citizen-selected
category -- it never fabricates a detection.
"""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from app.core.config import settings
from app.models.enums import IssueType, Severity

log = logging.getLogger(__name__)

# Model class name (lower-case) -> civic issue type. RDD2022: D00/D10 cracks,
# D20 alligator crack, D40 pothole. All road-damage classes route to Roads.
CLASS_TO_ISSUE = {
    "d00": IssueType.POTHOLE, "d10": IssueType.POTHOLE, "d20": IssueType.POTHOLE,
    "d40": IssueType.POTHOLE, "pothole": IssueType.POTHOLE, "crack": IssueType.POTHOLE,
    "garbage": IssueType.GARBAGE, "waste": IssueType.GARBAGE,
    "water_leakage": IssueType.WATER_LEAKAGE, "leakage": IssueType.WATER_LEAKAGE,
    "streetlight": IssueType.STREETLIGHT,
}
# How damaging each class is (prototype heuristic, used for severity only).
CLASS_WEIGHT = {"d40": 100, "pothole": 100, "d20": 70, "d00": 40, "d10": 40, "crack": 40}
DEFAULT_WEIGHT = 60

HIGH_AT, MEDIUM_AT = 60, 35


@dataclass
class Detection:
    label: str
    confidence: float
    area_ratio: float            # box area / image area (0..1)


@dataclass
class AIResult:
    model_name: str
    model_version: str
    detections: list[Detection]
    predicted_class: str
    issue_type: IssueType | None
    confidence: float            # MODEL CONFIDENCE, not accuracy
    severity: Severity
    severity_score: float
    inference_time_ms: float
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["issue_type"] = self.issue_type.value if self.issue_type else None
        d["severity"] = self.severity.value
        return d


def severity_from_detections(dets: list[Detection]) -> tuple[Severity, float]:
    """Transparent heuristic: 60% damaged-area share, 40% worst class weight."""
    area = min(1.0, sum(d.area_ratio for d in dets))
    area_score = min(100.0, area * 100 * 8)          # 12.5% of the frame -> 100
    weight = max(CLASS_WEIGHT.get(d.label.lower(), DEFAULT_WEIGHT) for d in dets)
    score = 0.6 * area_score + 0.4 * weight
    level = Severity.HIGH if score >= HIGH_AT else Severity.MEDIUM if score >= MEDIUM_AT else Severity.LOW
    return level, round(score, 1)


class YoloDetector:
    def __init__(self, weights: str):
        self.weights = weights
        self.name = Path(weights).stem
        self._model = None
        self._lock = threading.Lock()

    def available(self) -> bool:
        return Path(self.weights).is_file()

    def _load(self):
        if self._model is None:
            from ultralytics import YOLO  # lazy: heavy import
            self._model = YOLO(self.weights)
        return self._model

    def detect(self, image_path: str, conf: float) -> tuple[list[Detection], float]:
        with self._lock:
            model = self._load()
            t0 = time.perf_counter()
            res = model.predict(image_path, conf=conf, verbose=False)[0]
            ms = (time.perf_counter() - t0) * 1000
        h, w = res.orig_shape
        names = res.names
        dets = []
        for box in res.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            dets.append(Detection(
                label=str(names[int(box.cls[0])]),
                confidence=float(box.conf[0]),
                area_ratio=max(0.0, (x2 - x1) * (y2 - y1) / (w * h)),
            ))
        return dets, ms


_detector: YoloDetector | None = None


def get_detector() -> YoloDetector:
    global _detector
    if _detector is None:
        _detector = YoloDetector(settings.MODEL_PATH)
    return _detector


def status() -> dict:
    d = get_detector()
    ok = d.available()
    return {"model_loaded": ok, "model_name": d.name if ok else None,
            "conf_threshold": settings.AI_CONF_THRESHOLD}


def analyze_image(image_path: str) -> AIResult | None:
    """Run the detector. Returns None when no model is available, inference fails, or
    nothing mappable to a civic category is detected above the confidence threshold."""
    det = get_detector()
    if not det.available():
        return None
    try:
        dets, ms = det.detect(image_path, settings.AI_CONF_THRESHOLD)
    except Exception:  # model/library problem must never break report submission
        log.exception("AI inference failed")
        return None
    # Only classes we can map to a civic category count. A detection of anything else
    # (e.g. a stock COCO model seeing a "person") must never become a civic-issue result.
    dets = [d for d in dets if d.label.lower() in CLASS_TO_ISSUE]
    if not dets:
        return None
    best = max(dets, key=lambda d: d.confidence)
    severity, score = severity_from_detections(dets)
    return AIResult(
        model_name=det.name, model_version="v1", detections=dets,
        predicted_class=best.label, issue_type=CLASS_TO_ISSUE.get(best.label.lower()),
        confidence=round(best.confidence, 4), severity=severity, severity_score=score,
        inference_time_ms=round(ms, 1),
    )
