import pyautogui
from PIL import Image
import os
from datetime import datetime
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from config.settings import CACHE_DIR

class ScreenCapture:
    def capture_fullscreen(self):
        screenshot = pyautogui.screenshot()
        path = os.path.join(CACHE_DIR, f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        screenshot.save(path)
        return path

    def capture_region(self, x, y, width, height):
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        path = os.path.join(CACHE_DIR, f"region_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        screenshot.save(path)
        return path

    def capture_dota_draft_region(self):
        return self.capture_region(0, 100, 1920, 880)

    def capture_dota2_window(self):
        return self.capture_fullscreen()
