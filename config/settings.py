import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "dota2_assistant.db")
CACHE_DIR = os.path.join(BASE_DIR, "data", "cache")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
HERO_PORTRAITS_DIR = os.path.join(ASSETS_DIR, "hero_portraits")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
LOCALES_DIR = os.path.join(BASE_DIR, "locales")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENDOTA_BASE_URL = "https://api.opendota.com/api"

DEFAULT_SETTINGS = {
    "language": "uk",
    "theme": "dark",
    "auto_capture": False,
    "capture_region": "full",
    "confidence_threshold": 0.65,
    "gemini_model": "gemini-1.5-flash",
    "show_animations": True,
    "sound_effects": True,
    "auto_save": True,
    "draft_mode": "both",
}

SETTINGS_FILE = os.path.join(BASE_DIR, "data", "settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(HERO_PORTRAITS_DIR, exist_ok=True)
os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(LOCALES_DIR, exist_ok=True)
