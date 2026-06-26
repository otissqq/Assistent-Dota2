import cv2
import numpy as np
from PIL import Image
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from config.settings import HERO_PORTRAITS_DIR

class HeroRecognizer:
    def __init__(self, threshold=0.65):
        self.templates = {}
        self.threshold = threshold
        self._load_templates()

    def _load_templates(self):
        if not os.path.exists(HERO_PORTRAITS_DIR):
            return
        for filename in os.listdir(HERO_PORTRAITS_DIR):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                hero_name = os.path.splitext(filename)[0]
                path = os.path.join(HERO_PORTRAITS_DIR, filename)
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    self.templates[hero_name] = img

    def recognize_heroes(self, screenshot_path):
        if not self.templates:
            return []

        img = cv2.imread(screenshot_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return []

        found = []
        h_img, w_img = img.shape

        for hero_name, template in self.templates.items():
            h_t, w_t = template.shape
            if h_t > h_img or w_t > w_img:
                continue

            result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            loc = np.where(result >= self.threshold)

            for pt in zip(*loc[::-1]):
                is_new = True
                for f in found:
                    if abs(f['x'] - pt[0]) < w_t and abs(f['y'] - pt[1]) < h_t:
                        is_new = False
                        break
                if is_new:
                    found.append({
                        'name': hero_name,
                        'x': int(pt[0]),
                        'y': int(pt[1]),
                        'confidence': float(result[pt[1], pt[0]])
                    })

        found.sort(key=lambda x: x['x'])
        return [f['name'] for f in found]

    def set_threshold(self, threshold):
        self.threshold = threshold

    def add_template(self, hero_name, image_path):
        dst = os.path.join(HERO_PORTRAITS_DIR, f"{hero_name}.png")
        img = Image.open(image_path).convert('L')
        img.save(dst)
        self.templates[hero_name] = cv2.imread(dst, cv2.IMREAD_GRAYSCALE)

    def has_templates(self):
        return len(self.templates) > 0
