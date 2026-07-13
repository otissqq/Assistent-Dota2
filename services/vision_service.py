"""
Computer vision for Dota 2 top HUD / draft screenshots.

Important behavior:
- the program does NOT add fake heroes when the draft is incomplete;
- it searches only the top hero HUD slots instead of the whole screen;
- uncertain slots are skipped, so it is better to show fewer heroes than wrong heroes;
- debug images are saved to debug_cv/last_detection.png and debug_cv/last_search_area.png.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np
from PIL import Image

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_DIR = Path(__file__).resolve().parent.parent
HERO_DIR = PROJECT_DIR / "assets" / "heroes"
DEBUG_DIR = PROJECT_DIR / "debug_cv"

# Slot matching thresholds. If a match is too weak or too close to the second
# result, it is treated as unknown and is not returned.
MIN_SLOT_SCORE = 0.43
MIN_SCORE_GAP = 0.045

_TEMPLATE_CACHE: Dict[str, np.ndarray] | None = None


@dataclass
class SlotResult:
    name: str
    score: float
    second_score: float
    x: int
    y: int
    w: int
    h: int
    side: str  # "left" or "right"
    slot_index: int


def _read_bgr_8bit(path: Path | str) -> np.ndarray | None:
    """Read image as 8-bit BGR even if PNG is 16-bit."""
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


def _score_slot(slot: np.ndarray, tmpl: np.ndarray) -> float:
    """Combined score: grayscale structure + color histogram + color distance."""
    h, w = slot.shape[:2]
    resized = cv2.resize(tmpl, (w, h), interpolation=cv2.INTER_AREA)

    gray_slot = cv2.cvtColor(slot, cv2.COLOR_BGR2GRAY)
    gray_tmpl = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    corr = float(cv2.matchTemplate(gray_slot, gray_tmpl, cv2.TM_CCOEFF_NORMED)[0, 0])

    hsv_slot = cv2.cvtColor(slot, cv2.COLOR_BGR2HSV)
    hsv_tmpl = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
    hist_slot = cv2.calcHist([hsv_slot], [0, 1], None, [18, 10], [0, 180, 0, 256])
    hist_tmpl = cv2.calcHist([hsv_tmpl], [0, 1], None, [18, 10], [0, 180, 0, 256])
    cv2.normalize(hist_slot, hist_slot)
    cv2.normalize(hist_tmpl, hist_tmpl)
    hist = float(cv2.compareHist(hist_slot, hist_tmpl, cv2.HISTCMP_CORREL))

    mse = float(np.mean((slot.astype(np.float32) - resized.astype(np.float32)) ** 2) / 65025.0)
    mse_score = max(-1.0, min(1.0, 1.0 - mse * 3.0))

    return 0.35 * corr + 0.35 * hist + 0.30 * mse_score


def _slot_layout(img_w: int, img_h: int) -> Tuple[int, List[Tuple[str, int, int, int, int, int]]]:
    """
    Returns search height and expected top-HUD slots.

    Dota 2 top HUD keeps hero portraits near the center. Ratios are used so it
    works on 1920x1080, 3840x2160 and screenshots scaled by Windows/OBS.
    """
    if img_h <= 180:
        search_h = max(28, int(img_h * 0.65))
        slot_h = max(22, int(search_h * 0.62))
        slot_w = max(38, int(slot_h * 1.70))
        y = 0
        left_start = int(img_w * 0.27)
        right_start = int(img_w * 0.55)
    else:
        search_h = max(50, min(int(img_h * 0.075), 165))
        slot_h = max(30, min(int(img_h * 0.036), search_h - 2))
        slot_w = max(48, min(int(img_w * 0.034), 140))
        y = 0
        left_start = int(img_w * 0.276)
        right_start = int(img_w * 0.547)

    slots: List[Tuple[str, int, int, int, int, int]] = []
    for i in range(5):
        slots.append(("left", i, left_start + i * slot_w, y, slot_w, slot_h))
    for i in range(5):
        slots.append(("right", i, right_start + i * slot_w, y, slot_w, slot_h))
    return search_h, slots


def _match_one_slot(img: np.ndarray, slot, templates: Dict[str, np.ndarray]) -> SlotResult | None:
    side, slot_index, x, y, w, h = slot
    img_h, img_w = img.shape[:2]
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(1, min(w, img_w - x))
    h = max(1, min(h, img_h - y))

    crop = img[y:y + h, x:x + w]
    if crop.size == 0:
        return None

    # Remove a tiny border from the slot: top HUD borders / HP strips can confuse matching.
    pad_x = max(1, int(w * 0.04))
    pad_y = max(1, int(h * 0.05))
    inner = crop[pad_y:h - pad_y if h - pad_y > pad_y else h, pad_x:w - pad_x if w - pad_x > pad_x else w]
    if inner.size == 0:
        inner = crop

    scores = []
    for name, tmpl in templates.items():
        try:
            scores.append((_score_slot(inner, tmpl), name))
        except Exception:
            continue
    if not scores:
        return None

    scores.sort(reverse=True)
    best_score, best_name = scores[0]
    second_score = scores[1][0] if len(scores) > 1 else -1.0

    # Skip uncertain detections instead of showing wrong heroes.
    if best_score < MIN_SLOT_SCORE:
        return None
    if best_score - second_score < MIN_SCORE_GAP:
        return None

    return SlotResult(best_name, float(best_score), float(second_score), x, y, w, h, side, slot_index)


def _dedupe_results(results: List[SlotResult]) -> List[SlotResult]:
    """Do not return the same hero twice; keep the stronger slot."""
    by_name: Dict[str, SlotResult] = {}
    for r in results:
        old = by_name.get(r.name)
        if old is None or r.score > old.score:
            by_name[r.name] = r
    return sorted(by_name.values(), key=lambda r: (0 if r.side == "left" else 1, r.slot_index))


def _debug_image(full_img: np.ndarray, search_h: int, slots, results: List[SlotResult]) -> None:
    try:
        DEBUG_DIR.mkdir(exist_ok=True)
        vis = full_img.copy()
        cv2.rectangle(vis, (0, 0), (vis.shape[1] - 1, min(search_h, vis.shape[0]) - 1), (80, 80, 255), 2)

        result_by_slot = {(r.side, r.slot_index): r for r in results}
        for side, idx, x, y, w, h in slots:
            r = result_by_slot.get((side, idx))
            color = (70, 255, 120) if r else (0, 215, 255)
            cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
            label = f"{r.name} {r.score:.2f}" if r else "?"
            cv2.putText(vis, label, (x, max(14, y + h + 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imwrite(str(DEBUG_DIR / "last_detection.png"), vis)
        cv2.imwrite(str(DEBUG_DIR / "last_search_area.png"), full_img[:min(search_h, full_img.shape[0]), :])
    except Exception:
        pass


def _empty_result(source: str = "none") -> dict:
    return {"ally_heroes": [], "enemy_heroes": [], "confidences": [], "source": source}


def recognize_draft(image_path: str, side: str = "Radiant") -> dict:
    """
    Recognize heroes from a screenshot.

    Left side of top HUD is Radiant, right side is Dire. If user selected Dire,
    the returned ally/enemy lists are swapped. Missing/uncertain slots are not
    filled automatically.
    """
    img = _read_bgr_8bit(image_path)
    if img is None:
        return _empty_result("no_image")

    templates = _load_templates()
    if not templates:
        return _empty_result("no_templates")

    img_h, img_w = img.shape[:2]
    search_h, slots = _slot_layout(img_w, img_h)

    results: List[SlotResult] = []
    for slot in slots:
        r = _match_one_slot(img, slot, templates)
        if r is not None:
            results.append(r)

    results = _dedupe_results(results)
    _debug_image(img, search_h, slots, results)

    left = [r for r in results if r.side == "left"]
    right = [r for r in results if r.side == "right"]
    left.sort(key=lambda r: r.slot_index)
    right.sort(key=lambda r: r.slot_index)

    left_names = [r.name for r in left[:5]]
    right_names = [r.name for r in right[:5]]

    if side == "Dire":
        ally, enemy = right_names, left_names
    else:
        ally, enemy = left_names, right_names

    return {
        "ally_heroes": ally,
        "enemy_heroes": enemy,
        "confidences": [round(r.score, 3) for r in results],
        "source": "cv_partial" if len(results) < 10 else "cv",
    }
