"""
Computer vision for Dota 2 draft screenshots.

This version is tuned for the top Dota 2 HUD / draft row:
- searches only the top bar, not the whole top 30% of the screen;
- ignores the middle scoreboard/timer area so it does not mark random UI as heroes;
- does not auto-fill missing heroes with sample heroes;
- returns only the heroes that were really detected.
"""

from __future__ import annotations

import os
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

# Lower = finds more, but may confuse heroes. Higher = stricter.
# For small top HUD icons 0.40-0.45 is usually better than 0.50+.
CONFIDENCE_THRESHOLD = 0.42

# No sample auto-fill. Even 1-2 detections are returned as a partial draft.
MIN_REAL_DETECTIONS = 1

# Widths for Dota top HUD icons and larger draft portraits.
# Small widths are important because the top bar icons are much smaller
# than normal hero portraits.
TEMPLATE_WIDTHS = [20, 24, 28, 32, 38, 46, 54, 64, 76, 90, 108, 128]

# Center area contains score/timer, not hero icons.
# Candidates inside this area are ignored.
CENTER_IGNORE_LEFT = 0.42
CENTER_IGNORE_RIGHT = 0.58


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
    union = a.w * a.h + b.w * b.h - inter
    return inter / union if union else 0.0


def _top_search_height(img_h: int) -> int:
    """
    Full screenshots and cropped top-bar screenshots need different heights.

    If the user passes a small cropped HUD image, search about the upper half.
    If the user passes a full screenshot, search only the real top HUD area.
    """
    if img_h <= 180:
        return max(24, int(img_h * 0.55))

    # 1080p -> ~86 px, 2160p -> ~150 px, but do not go too deep.
    return max(70, min(int(img_h * 0.08), 160))


def _is_in_scoreboard_area(det: Detection, image_width: int) -> bool:
    cx = (det.x + det.w / 2) / max(1, image_width)
    return CENTER_IGNORE_LEFT <= cx <= CENTER_IGNORE_RIGHT


def _find_best_matches(search_img: np.ndarray, templates: Dict[str, np.ndarray]) -> List[Detection]:
    """
    Find portrait matches in the top HUD area.

    The old version selected the best 10 matches globally, so it could mark
    the timer/scoreboard or map background as heroes. This version:
    - ignores the center scoreboard area;
    - selects up to 5 detections on the left and up to 5 on the right;
    - keeps only non-overlapping detections;
    - returns a partial result if fewer than 10 heroes are found.
    """
    candidates: List[Detection] = []
    img_h, img_w = search_img.shape[:2]
    gray_search = cv2.cvtColor(search_img, cv2.COLOR_BGR2GRAY)

    for name, tmpl in templates.items():
        th, tw = tmpl.shape[:2]
        if th == 0 or tw == 0:
            continue

        aspect = th / tw

        for target_w in TEMPLATE_WIDTHS:
            target_h = max(12, int(target_w * aspect))

            if target_h >= img_h or target_w >= img_w:
                continue

            resized = cv2.resize(tmpl, (target_w, target_h), interpolation=cv2.INTER_AREA)
            gray_tmpl = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

            res = cv2.matchTemplate(gray_search, gray_tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)

            det = Detection(
                name=name,
                score=float(max_val),
                x=max_loc[0],
                y=max_loc[1],
                w=target_w,
                h=target_h,
            )

            if det.score >= CONFIDENCE_THRESHOLD and not _is_in_scoreboard_area(det, img_w):
                candidates.append(det)

    candidates.sort(key=lambda d: d.score, reverse=True)

    left: List[Detection] = []
    right: List[Detection] = []
    used_names = set()

    for det in candidates:
        if det.name in used_names:
            continue

        cx = det.x + det.w / 2
        target = left if cx < img_w / 2 else right

        if len(target) >= 5:
            continue

        # Same slot / same hero portrait area.
        if any(_rect_iou(det, old) > 0.22 for old in target):
            continue

        # Prevent detections that are almost on the same x-position in one side.
        # It is usually the same HUD slot with another wrong hero name.
        if any(abs((det.x + det.w / 2) - (old.x + old.w / 2)) < max(det.w, old.w) * 0.55 for old in target):
            continue

        target.append(det)
        used_names.add(det.name)

        if len(left) >= 5 and len(right) >= 5:
            break

    selected = left + right
    selected.sort(key=lambda d: (d.x, d.y))
    return selected


def _split_by_side(detections: List[Detection], image_width: int, side: str) -> Tuple[List[str], List[str]]:
    """Split detected heroes into Radiant/Dire by top bar side."""
    left = [d for d in detections if d.x + d.w / 2 < image_width / 2]
    right = [d for d in detections if d.x + d.w / 2 >= image_width / 2]

    left.sort(key=lambda d: d.x)
    right.sort(key=lambda d: d.x)

    left_names = [d.name for d in left[:5]]
    right_names = [d.name for d in right[:5]]

    # In Dota HUD: left side = Radiant, right side = Dire.
    # If the user plays Dire, their team is on the right.
    if side == "Dire":
        return right_names, left_names
    return left_names, right_names


def _debug_image(full_img: np.ndarray, search_h: int, detections: List[Detection]) -> None:
    try:
        DEBUG_DIR.mkdir(exist_ok=True)

        vis = full_img.copy()
        cv2.rectangle(vis, (0, 0), (vis.shape[1] - 1, search_h - 1), (80, 80, 255), 2)

        # Mark ignored scoreboard zone.
        x1 = int(vis.shape[1] * CENTER_IGNORE_LEFT)
        x2 = int(vis.shape[1] * CENTER_IGNORE_RIGHT)
        cv2.rectangle(vis, (x1, 0), (x2, search_h - 1), (80, 120, 255), 1)

        for d in detections:
            cv2.rectangle(vis, (d.x, d.y), (d.x + d.w, d.y + d.h), (80, 255, 120), 2)
            cv2.putText(
                vis,
                f"{d.name} {d.score:.2f}",
                (d.x, max(14, d.y - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        cv2.imwrite(str(DEBUG_DIR / "last_detection.png"), vis)
        cv2.imwrite(str(DEBUG_DIR / "last_search_area.png"), full_img[:search_h, :])
    except Exception:
        pass


def _empty_result(source: str = "none") -> dict:
    return {
        "ally_heroes": [],
        "enemy_heroes": [],
        "confidences": [],
        "source": source,
    }


def recognize_draft(image_path: str, side: str = "Radiant") -> dict:
    """
    Recognize ally/enemy heroes from a Dota 2 screenshot.

    Important:
    - does not add fake/sample heroes;
    - if the screenshot is incomplete, returns only detected heroes;
    - manual input and recommendation logic should handle missing heroes.
    """
    templates = _load_templates()
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)

    if img is None:
        return _empty_result("no_image")

    if not templates:
        return _empty_result("no_templates")

    img = preprocess(img)
    h, w = img.shape[:2]

    search_h = _top_search_height(h)
    search_img = img[:search_h, :]

    detections = _find_best_matches(search_img, templates)
    _debug_image(img, search_h, detections)

    if len(detections) < MIN_REAL_DETECTIONS:
        return _empty_result("cv_none")

    ally, enemy = _split_by_side(detections, w, side)

    return {
        "ally_heroes": ally[:5],
        "enemy_heroes": enemy[:5],
        "confidences": [round(d.score, 3) for d in detections],
        "source": "cv_partial" if len(detections) < 10 else "cv",
    }