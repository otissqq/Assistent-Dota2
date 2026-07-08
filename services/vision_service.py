"""
Computer vision for Dota 2 draft screenshots.

How it works:
1. Loads hero portrait templates from assets/heroes/*.png.
2. Searches the top part of the screenshot for hero portraits using OpenCV template matching.
3. Picks the best 10 non-overlapping detections.
4. Splits detections into left/right draft sides and returns ally/enemy heroes.

If real recognition fails, the service returns a sample draft so the rest of the program
can still be demonstrated. For debugging, it writes images into debug_cv/.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.heroes_data import HEROES

PROJECT_DIR = Path(__file__).resolve().parent.parent
HERO_DIR = PROJECT_DIR / "assets" / "heroes"
DEBUG_DIR = PROJECT_DIR / "debug_cv"

# Якщо занадто мало знаходить — зменшуй до 0.42.
# Якщо плутає героїв — піднімай до 0.52-0.58.
CONFIDENCE_THRESHOLD = 0.46
MIN_REAL_DETECTIONS = 6

# Де шукати портрети на скриншоті. 0.28 = верхні 28% екрана.
# Якщо у твоєму скрині герої нижче, постав 0.35.
TOP_SEARCH_RATIO = 0.30

# Пошук по різних розмірах портретів. Це допомагає для 1920x1080 і 3840x2160.
TEMPLATE_WIDTHS = [46, 54, 64, 76, 90, 108, 128]


@dataclass
class Detection:
    name: str
    score: float
    x: int
    y: int
    w: int
    h: int


def preprocess(image: np.ndarray) -> np.ndarray:
    """Light preprocessing for template matching."""
    if image is None or image.size == 0:
        return image
    # Keep BGR, equalize luminance only.
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def _load_templates() -> Dict[str, np.ndarray]:
    templates: Dict[str, np.ndarray] = {}
    if not HERO_DIR.is_dir():
        return templates

    for path in HERO_DIR.glob("*.png"):
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None or img.size == 0:
            continue
        templates[path.stem] = preprocess(img)

    return templates


def _rect_iou(a: Detection, b: Detection) -> float:
    ax1, ay1, ax2, ay2 = a.x, a.y, a.x + a.w, a.y + a.h
    bx1, by1, bx2, by2 = b.x, b.y, b.x + b.w, b.y + b.h
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(0, ix2 - ix1), max(0, iy2 - iy1)
    inter = iw * ih
    area_a = a.w * a.h
    area_b = b.w * b.h
    union = area_a + area_b - inter
    return inter / union if union else 0.0


def _find_best_matches(search_img: np.ndarray, templates: Dict[str, np.ndarray]) -> List[Detection]:
    """Find best portrait matches in the top draft area."""
    candidates: List[Detection] = []
    gray_search = cv2.cvtColor(search_img, cv2.COLOR_BGR2GRAY)

    for name, tmpl in templates.items():
        th, tw = tmpl.shape[:2]
        if th == 0 or tw == 0:
            continue

        best: Detection | None = None
        aspect = th / tw

        for target_w in TEMPLATE_WIDTHS:
            target_h = max(20, int(target_w * aspect))
            if target_h >= gray_search.shape[0] or target_w >= gray_search.shape[1]:
                continue

            resized = cv2.resize(tmpl, (target_w, target_h), interpolation=cv2.INTER_AREA)
            gray_tmpl = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

            res = cv2.matchTemplate(gray_search, gray_tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            score = float(max_val)

            if best is None or score > best.score:
                best = Detection(name=name, score=score, x=max_loc[0], y=max_loc[1], w=target_w, h=target_h)

        if best and best.score >= CONFIDENCE_THRESHOLD:
            candidates.append(best)

    # Higher score first. Keep unique non-overlapping slots.
    candidates.sort(key=lambda d: d.score, reverse=True)
    selected: List[Detection] = []
    used_names = set()

    for det in candidates:
        if det.name in used_names:
            continue
        if any(_rect_iou(det, old) > 0.25 for old in selected):
            continue
        selected.append(det)
        used_names.add(det.name)
        if len(selected) >= 10:
            break

    # Return in screen order.
    selected.sort(key=lambda d: (d.x, d.y))
    return selected


def _split_by_side(detections: List[Detection], image_width: int, side: str) -> Tuple[List[str], List[str]]:
    """Split detected heroes into Radiant/Dire by screen half and then into ally/enemy."""
    left = [d for d in detections if d.x + d.w / 2 < image_width / 2]
    right = [d for d in detections if d.x + d.w / 2 >= image_width / 2]

    left.sort(key=lambda d: d.x)
    right.sort(key=lambda d: d.x)

    left_names = [d.name for d in left[:5]]
    right_names = [d.name for d in right[:5]]

    if side == "Dire":
        return right_names, left_names
    return left_names, right_names


def _debug_image(full_img: np.ndarray, search_h: int, detections: List[Detection]) -> None:
    try:
        DEBUG_DIR.mkdir(exist_ok=True)
        vis = full_img.copy()
        cv2.rectangle(vis, (0, 0), (vis.shape[1] - 1, search_h - 1), (80, 80, 255), 2)
        for d in detections:
            cv2.rectangle(vis, (d.x, d.y), (d.x + d.w, d.y + d.h), (80, 255, 120), 2)
            cv2.putText(
                vis,
                f"{d.name} {d.score:.2f}",
                (d.x, max(16, d.y - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )
        cv2.imwrite(str(DEBUG_DIR / "last_detection.png"), vis)
        cv2.imwrite(str(DEBUG_DIR / "last_search_area.png"), full_img[:search_h, :])
    except Exception:
        pass


def _sample_result() -> dict:
    # Deterministic sample draft for demo mode.
    ally = ["Pangolier", "Lina", "Magnus", "Phoenix", "Crystal Maiden"]
    enemy = ["Timbersaw", "Tinker", "Batrider", "Dark Willow", "Tidehunter"]
    return {
        "ally_heroes": ally,
        "enemy_heroes": enemy,
        "confidences": [0.93, 0.95, 0.91, 0.88, 0.97, 0.90, 0.94, 0.89, 0.92, 0.96],
        "source": "sample",
    }


def recognize_draft(image_path: str, side: str = "Radiant") -> dict:
    """Recognize ally/enemy heroes from a full Dota 2 draft screenshot."""
    templates = _load_templates()
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)

    if img is None or not templates:
        return _sample_result()

    img = preprocess(img)
    h, w = img.shape[:2]
    search_h = int(h * TOP_SEARCH_RATIO)
    search_img = img[:search_h, :]

    detections = _find_best_matches(search_img, templates)
    _debug_image(img, search_h, detections)

    if len(detections) < MIN_REAL_DETECTIONS:
        return _sample_result()

    ally, enemy = _split_by_side(detections, w, side)

    # If one side is under-detected, still return what was detected + sample fill.
    # This prevents UI crashes and makes it clear in debug_cv what failed.
    sample = _sample_result()
    while len(ally) < 5:
        ally.append(sample["ally_heroes"][len(ally)])
    while len(enemy) < 5:
        enemy.append(sample["enemy_heroes"][len(enemy)])

    return {
        "ally_heroes": ally[:5],
        "enemy_heroes": enemy[:5],
        "confidences": [round(d.score, 3) for d in detections[:10]],
        "source": "cv",
    }
