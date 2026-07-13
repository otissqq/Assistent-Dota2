"""
Computer vision for Dota 2 top HUD / draft screenshots.

This version uses global template matching in the top HUD strip instead of
rigid fixed slots. It is better for real screenshots where Dota shifts the top
panel because of demo mode, UI scale, scoreboard, or resolution.

Behavior:
- only heroes that are actually found are returned;
- missing heroes are NOT auto-filled;
- predicted picks are handled by the recommendation logic, not by CV;
- debug images are saved to debug_cv/last_detection.png and debug_cv/last_search_area.png.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
from PIL import Image

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_DIR = Path(__file__).resolve().parent.parent
HERO_DIR = PROJECT_DIR / "assets" / "heroes"
DEBUG_DIR = PROJECT_DIR / "debug_cv"

# High enough to avoid random UI/background matches, but low enough for small HUD portraits.
MIN_GLOBAL_SCORE = 0.60
_TEMPLATE_CACHE: Dict[str, np.ndarray] | None = None
_TEMPLATE_GRAY_CACHE: Dict[str, np.ndarray] | None = None


@dataclass
class Detection:
    name: str
    score: float
    x: int
    y: int
    w: int
    h: int
    side: str  # "left" or "right"


def _read_bgr_8bit(path: Path | str) -> np.ndarray | None:
    try:
        im = Image.open(path).convert("RGB")
        return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def _load_templates() -> Dict[str, np.ndarray]:
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is not None:
        return _TEMPLATE_CACHE

    templates: Dict[str, np.ndarray] = {}
    if not HERO_DIR.is_dir():
        _TEMPLATE_CACHE = templates
        return templates

    for path in HERO_DIR.glob("*.png"):
        img = _read_bgr_8bit(path)
        if img is None or img.size == 0:
            continue
        templates[path.stem] = img

    _TEMPLATE_CACHE = templates
    return templates


def _hud_params(img_w: int, img_h: int) -> tuple[int, int, int]:
    """Return search height and top-HUD portrait size."""
    if img_h <= 180:
        search_h = max(35, int(img_h * 0.70))
        slot_h = max(24, int(search_h * 0.55))
        slot_w = max(42, int(slot_h * 1.72))
    else:
        search_h = max(62, min(int(img_h * 0.075), 180))
        slot_h = max(30, min(int(img_h * 0.036), 44))
        slot_w = max(48, min(int(img_w * 0.034), 82))
    return search_h, slot_w, slot_h


def _score_crop(crop: np.ndarray, tmpl: np.ndarray) -> float:
    h, w = crop.shape[:2]
    resized = cv2.resize(tmpl, (w, h), interpolation=cv2.INTER_AREA)

    gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    gray_tmpl = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    corr = float(cv2.matchTemplate(gray_crop, gray_tmpl, cv2.TM_CCOEFF_NORMED)[0, 0])

    hsv_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    hsv_tmpl = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    hist_crop = cv2.calcHist([hsv_crop], [0, 1], None, [20, 12], [0, 180, 0, 256])
    hist_tmpl = cv2.calcHist([hsv_tmpl], [0, 1], None, [20, 12], [0, 180, 0, 256])
    cv2.normalize(hist_crop, hist_crop)
    cv2.normalize(hist_tmpl, hist_tmpl)
    hist = float(cv2.compareHist(hist_crop, hist_tmpl, cv2.HISTCMP_CORREL))

    return 0.55 * corr + 0.45 * hist


def _allowed_hud_x(img_w: int, x: int, slot_w: int) -> bool:
    """Filter out minimap/scoreboard/left tool panel/background false matches."""
    cx = x + slot_w / 2
    # top HUD hero area: around the center, not the side panels.
    left_ok = img_w * 0.20 <= cx <= img_w * 0.49
    right_ok = img_w * 0.51 <= cx <= img_w * 0.80
    return left_ok or right_ok


def _side_from_x(img_w: int, x: int, slot_w: int) -> str:
    return "left" if (x + slot_w / 2) < img_w * 0.50 else "right"


def _global_match_top_hud(img: np.ndarray, templates: Dict[str, np.ndarray]) -> List[Detection]:
    img_h, img_w = img.shape[:2]
    search_h, slot_w, slot_h = _hud_params(img_w, img_h)

    top = img[:min(search_h, img_h), :]
    # In normal full screenshots, real top HUD portraits are at the very top.
    # Lower matches often come from hero health bars, minimap, or the side tool panel.
    max_y = min(max(12, int(slot_h * 0.40)), max(0, top.shape[0] - slot_h))

    gray_top = cv2.cvtColor(top, cv2.COLOR_BGR2GRAY)

    candidates: List[Detection] = []

    for name, tmpl in templates.items():
        try:
            resized = cv2.resize(tmpl, (slot_w, slot_h), interpolation=cv2.INTER_AREA)
            gray_tmpl = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            resp = cv2.matchTemplate(gray_top, gray_tmpl, cv2.TM_CCOEFF_NORMED)

            # Take several local maxima per hero. Then NMS will remove overlaps.
            for _ in range(3):
                _, corr, _, loc = cv2.minMaxLoc(resp)
                if corr < 0.48:
                    break

                x, y = loc
                if y <= max_y and _allowed_hud_x(img_w, x, slot_w):
                    crop = top[y:y + slot_h, x:x + slot_w]
                    if crop.shape[0] == slot_h and crop.shape[1] == slot_w:
                        combined = 0.50 * float(corr) + 0.50 * _score_crop(crop, tmpl)
                        if combined >= MIN_GLOBAL_SCORE:
                            candidates.append(
                                Detection(
                                    name=name,
                                    score=float(combined),
                                    x=int(x),
                                    y=int(y),
                                    w=int(slot_w),
                                    h=int(slot_h),
                                    side=_side_from_x(img_w, x, slot_w),
                                )
                            )

                # Suppress this location for the same hero.
                x0 = max(0, x - slot_w // 2)
                y0 = max(0, y - slot_h // 2)
                x1 = min(resp.shape[1], x + slot_w // 2)
                y1 = min(resp.shape[0], y + slot_h // 2)
                resp[y0:y1, x0:x1] = 0
        except Exception:
            continue

    candidates.sort(key=lambda d: d.score, reverse=True)

    selected: List[Detection] = []
    used_names = set()

    for d in candidates:
        if d.name in used_names:
            continue
        # NMS: do not return two heroes from the same small portrait area.
        overlaps = False
        for s in selected:
            if abs(d.x - s.x) < int(slot_w * 0.65) and abs(d.y - s.y) < int(slot_h * 0.70):
                overlaps = True
                break
        if overlaps:
            continue

        selected.append(d)
        used_names.add(d.name)

        if len([x for x in selected if x.side == "left"]) >= 5 and len([x for x in selected if x.side == "right"]) >= 5:
            break

    selected.sort(key=lambda d: (0 if d.side == "left" else 1, d.x))
    return selected


def _debug_image(full_img: np.ndarray, detections: List[Detection]) -> None:
    try:
        DEBUG_DIR.mkdir(exist_ok=True)
        vis = full_img.copy()
        search_h, _, _ = _hud_params(vis.shape[1], vis.shape[0])
        cv2.rectangle(vis, (0, 0), (vis.shape[1] - 1, min(search_h, vis.shape[0]) - 1), (80, 80, 255), 2)

        for d in detections:
            color = (70, 255, 120) if d.side == "left" else (255, 160, 80)
            cv2.rectangle(vis, (d.x, d.y), (d.x + d.w, d.y + d.h), color, 2)
            label = f"{d.name} {d.score:.2f}"
            cv2.putText(
                vis,
                label,
                (d.x, max(14, d.y + d.h + 14)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.42,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        cv2.imwrite(str(DEBUG_DIR / "last_detection.png"), vis)
        cv2.imwrite(str(DEBUG_DIR / "last_search_area.png"), full_img[:min(search_h, full_img.shape[0]), :])
    except Exception:
        pass


def _empty_result(source: str = "none") -> dict:
    return {"ally_heroes": [], "enemy_heroes": [], "confidences": [], "source": source}


def recognize_draft(image_path: str, side: str = "Radiant") -> dict:
    img = _read_bgr_8bit(image_path)
    if img is None:
        return _empty_result("no_image")

    templates = _load_templates()
    if not templates:
        return _empty_result("no_templates")

    detections = _global_match_top_hud(img, templates)
    _debug_image(img, detections)

    left = [d for d in detections if d.side == "left"]
    right = [d for d in detections if d.side == "right"]
    left.sort(key=lambda d: d.x)
    right.sort(key=lambda d: d.x)

    left_names = [d.name for d in left[:5]]
    right_names = [d.name for d in right[:5]]

    if side == "Dire":
        ally, enemy = right_names, left_names
    else:
        ally, enemy = left_names, right_names

    return {
        "ally_heroes": ally,
        "enemy_heroes": enemy,
        "confidences": [round(d.score, 3) for d in detections],
        "source": "cv_partial" if len(detections) < 10 else "cv",
    }