"""RDD2022 (India) -> YOLO: prepare, train, evaluate.  Run on Colab/Kaggle GPU.

    python rdd_pipeline.py prepare  --src /content/RDD2022/India --out /content/rdd_yolo
    python rdd_pipeline.py train    --data /content/rdd_yolo/data.yaml --epochs 30
    python rdd_pipeline.py evaluate --weights runs/detect/sevasetu/weights/best.pt \
                                    --data /content/rdd_yolo/data.yaml

Get the dataset from the official RDD2022 repository (github.com/sekilab/RoadDamageDetector),
which links the per-country archives; download the India one.  Expected layout:
    India/train/images/*.jpg   India/train/annotations/xmls/*.xml   (Pascal VOC)
The public test split normally has no annotations, so we hold out our own
validation split from `train` (seeded, reproducible).
"""
import argparse
import json
import random
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

CLASSES = ["D00", "D10", "D20", "D40"]   # longitudinal, transverse, alligator crack, pothole
IMG_EXT = {".jpg", ".jpeg", ".png"}


def voc_to_yolo(xml_path: Path):
    """Return YOLO label lines for one VOC xml (only our 4 classes)."""
    root = ET.parse(xml_path).getroot()
    size = root.find("size")
    w, h = float(size.find("width").text), float(size.find("height").text)
    lines = []
    for obj in root.findall("object"):
        name = obj.find("name").text.strip()
        if name not in CLASSES:
            continue
        b = obj.find("bndbox")
        x1, y1, x2, y2 = (float(b.find(k).text) for k in ("xmin", "ymin", "xmax", "ymax"))
        x1, x2 = max(0, min(x1, x2)), min(w, max(x1, x2))
        y1, y2 = max(0, min(y1, y2)), min(h, max(y1, y2))
        if x2 - x1 < 2 or y2 - y1 < 2 or w <= 0 or h <= 0:
            continue
        lines.append(f"{CLASSES.index(name)} {(x1+x2)/2/w:.6f} {(y1+y2)/2/h:.6f} "
                     f"{(x2-x1)/w:.6f} {(y2-y1)/h:.6f}")
    return lines


def prepare(src: str, out: str, val_frac: float = 0.2, seed: int = 42):
    src, out = Path(src), Path(out)
    img_dir = src / "train" / "images"
    xml_dir = src / "train" / "annotations" / "xmls"
    images = sorted(p for p in img_dir.iterdir() if p.suffix.lower() in IMG_EXT)
    random.Random(seed).shuffle(images)
    n_val = int(len(images) * val_frac)
    splits = {"val": images[:n_val], "train": images[n_val:]}
    stats = {"classes": CLASSES, "seed": seed, "images": {}, "boxes": {c: 0 for c in CLASSES}}
    for split, files in splits.items():
        (out / "images" / split).mkdir(parents=True, exist_ok=True)
        (out / "labels" / split).mkdir(parents=True, exist_ok=True)
        kept = 0
        for img in files:
            xml = xml_dir / f"{img.stem}.xml"
            lines = voc_to_yolo(xml) if xml.exists() else []
            if split == "train" and not lines:
                continue                       # skip unlabeled images for training
            shutil.copy2(img, out / "images" / split / img.name)
            (out / "labels" / split / f"{img.stem}.txt").write_text("\n".join(lines))
            for ln in lines:
                stats["boxes"][CLASSES[int(ln.split()[0])]] += 1
            kept += 1
        stats["images"][split] = kept
    (out / "data.yaml").write_text(
        f"path: {out.resolve()}\ntrain: images/train\nval: images/val\n"
        f"names:\n" + "".join(f"  {i}: {c}\n" for i, c in enumerate(CLASSES)))
    (out / "dataset_stats.json").write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2))


def train(data: str, epochs: int = 30, imgsz: int = 640, model: str = "yolov8n.pt", batch: int = 16):
    from ultralytics import YOLO
    YOLO(model).train(data=data, epochs=epochs, imgsz=imgsz, batch=batch, name="sevasetu", exist_ok=True)


def evaluate(weights: str, data: str, imgsz: int = 640, out: str = "evaluation_results.json"):
    from ultralytics import YOLO
    m = YOLO(weights)
    r = m.val(data=data, imgsz=imgsz)
    res = {
        "weights": weights, "imgsz": imgsz,
        "precision": float(r.box.mp), "recall": float(r.box.mr),
        "mAP50": float(r.box.map50), "mAP50_95": float(r.box.map),
        "per_class_mAP50": {r.names[i]: float(v) for i, v in zip(r.box.ap_class_index, r.box.ap50)},
        "inference_ms_per_image": float(r.speed["inference"]),
        "note": "Measured on our held-out split of RDD2022 India train data (not an official test set).",
    }
    Path(out).write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare"); p.add_argument("--src", required=True); p.add_argument("--out", required=True)
    t = sub.add_parser("train"); t.add_argument("--data", required=True)
    t.add_argument("--epochs", type=int, default=30); t.add_argument("--imgsz", type=int, default=640)
    t.add_argument("--model", default="yolov8n.pt"); t.add_argument("--batch", type=int, default=16)
    e = sub.add_parser("evaluate"); e.add_argument("--weights", required=True); e.add_argument("--data", required=True)
    e.add_argument("--imgsz", type=int, default=640)
    a = ap.parse_args()
    if a.cmd == "prepare": prepare(a.src, a.out)
    elif a.cmd == "train": train(a.data, a.epochs, a.imgsz, a.model, a.batch)
    else: evaluate(a.weights, a.data, a.imgsz)
