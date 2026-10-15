"""Hotspot detection: density-based clustering (DBSCAN) of open civic issues.

Pure Python with haversine distance, so it is easy to test and explain:
a hotspot is >= min_points issues where each is within eps_m metres of another
member -- i.e. a dense cluster of civic problems, not just one busy spot.
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@dataclass
class Point:
    id: int
    lat: float
    lon: float
    issue_type: str
    priority: float
    report_count: int
    address: str | None = None
    code: str = ""


def dbscan(points: list[Point], eps_m: float, min_points: int) -> list[list[int]]:
    """Returns clusters as lists of indices into `points` (noise is dropped)."""
    n = len(points)
    nbrs = [[j for j in range(n)
             if haversine_m(points[i].lat, points[i].lon, points[j].lat, points[j].lon) <= eps_m]
            for i in range(n)]          # includes the point itself
    label = [-1] * n
    visited = [False] * n
    clusters: list[list[int]] = []
    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True
        if len(nbrs[i]) < min_points:
            continue                     # noise (may be claimed as a border point later)
        cluster = [i]
        label[i] = len(clusters)
        queue = [j for j in nbrs[i] if j != i]
        while queue:
            j = queue.pop()
            if label[j] == -1:
                label[j] = label[i]
                cluster.append(j)
            if visited[j]:
                continue
            visited[j] = True
            if len(nbrs[j]) >= min_points:
                queue.extend(k for k in nbrs[j] if not visited[k] or label[k] == -1)
        clusters.append(cluster)
    return clusters


def find_hotspots(points: list[Point], eps_m: float = 250, min_points: int = 3) -> list[dict]:
    out = []
    for idx, members in enumerate(dbscan(points, eps_m, min_points)):
        pts = [points[i] for i in members]
        clat = sum(p.lat for p in pts) / len(pts)
        clon = sum(p.lon for p in pts) / len(pts)
        radius = max(haversine_m(clat, clon, p.lat, p.lon) for p in pts) + 40
        addresses = [p.address.strip() for p in pts if p.address and p.address.strip()]
        label = Counter(addresses).most_common(1)[0][0] if addresses else f"Near {clat:.4f}, {clon:.4f}"
        types = Counter(p.issue_type for p in pts)
        out.append({
            "label": label,
            "center_lat": round(clat, 6), "center_lon": round(clon, 6),
            "radius_m": round(max(radius, 60)),
            "issue_count": len(pts),
            "report_count": sum(p.report_count for p in pts),
            "avg_priority": round(sum(p.priority for p in pts) / len(pts), 1),
            "max_priority": round(max(p.priority for p in pts), 1),
            "dominant_type": types.most_common(1)[0][0],
            "by_type": dict(types),
            "issue_ids": [p.id for p in pts],
        })
    out.sort(key=lambda h: (h["avg_priority"] * h["issue_count"]), reverse=True)
    for rank, h in enumerate(out, 1):
        h["rank"] = rank
    return out
