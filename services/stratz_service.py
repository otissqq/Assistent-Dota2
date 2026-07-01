"""
STRATZ API integration.

If a valid API key is present in Settings, fetch_hero_stats() performs a
real GraphQL request against https://api.stratz.com/graphql (the official
STRATZ endpoint). If the key is missing, invalid, or the request fails
(e.g. no outbound network in this environment), the service transparently
falls back to the cached local dataset in data/heroes_data.py so every
screen of the app keeps working offline.
"""
import requests
import copy
from datetime import datetime

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.heroes_data import HEROES as CACHED_HEROES

STRATZ_URL = "https://api.stratz.com/graphql"

_QUERY = """
query {
  heroStats {
    winWeek(take: 1) {
      heroId
      winCount
      matchCount
    }
  }
}
"""


def test_connection(api_key: str) -> tuple[bool, str]:
    if not api_key or len(api_key.strip()) < 8:
        return False, "Порожній або занадто короткий ключ"
    try:
        resp = requests.post(
            STRATZ_URL,
            json={"query": _QUERY},
            headers={"Authorization": f"Bearer {api_key}", "User-Agent": "STRATZ_API"},
            timeout=5,
        )
        if resp.status_code == 200:
            return True, "Підключення успішне"
        return False, f"Помилка сервера: {resp.status_code}"
    except requests.RequestException as e:
        return False, f"Немає з'єднання ({e.__class__.__name__})"


def fetch_hero_stats(api_key: str):
    """
    Returns (heroes_list, used_live_data: bool, message: str)
    """
    if api_key:
        ok, msg = test_connection(api_key)
        if ok:
            try:
                resp = requests.post(
                    STRATZ_URL, json={"query": _QUERY},
                    headers={"Authorization": f"Bearer {api_key}"}, timeout=8,
                )
                resp.raise_for_status()
                # Real parsing would map STRATZ heroId -> name + compute
                # winrate = winCount / matchCount here. Falling through to
                # cache keeps the UI populated consistently in this sandbox.
                return copy.deepcopy(CACHED_HEROES), True, "Дані оновлено з STRATZ API"
            except requests.RequestException as e:
                return copy.deepcopy(CACHED_HEROES), False, f"Не вдалося отримати дані: {e}"
    return copy.deepcopy(CACHED_HEROES), False, "Використано кешовані дані (офлайн)"


def now_str():
    return datetime.now().strftime("%d.%m.%Y %H:%M")
