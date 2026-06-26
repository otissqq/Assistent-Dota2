import requests
import sys
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from config.settings import OPENDOTA_BASE_URL
from core.database import DatabaseManager

class OpenDotaClient:
    def __init__(self):
        self.session = requests.Session()
        self.db = DatabaseManager()
        self.cache_ttl = timedelta(hours=6)

    def _get(self, endpoint, params=None):
        url = f"{OPENDOTA_BASE_URL}/{endpoint}"
        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_heroes(self, force_refresh=False):
        if not force_refresh:
            cached = self.db.get_cached_heroes()
            if cached:
                return cached
        data = self._get("heroes")
        heroes = []
        for h in data:
            heroes.append({
                'id': h.get('id'),
                'name': h.get('name'),
                'localized_name': h.get('localized_name'),
                'primary_attr': h.get('primary_attr'),
                'attack_type': h.get('attack_type'),
                'roles': h.get('roles', []),
                'winrate': 0.0
            })
        self.db.cache_heroes(heroes)
        return heroes

    def get_hero_stats(self):
        return self._get("heroStats")

    def get_hero_matchups(self, hero_id, force_refresh=False):
        if not force_refresh:
            cached = self.db.get_matchups(hero_id)
            if cached:
                return cached
        data = self._get(f"heroes/{hero_id}/matchups")
        matchups = []
        for m in data:
            games = m.get('games_played', 0)
            wins = m.get('wins', 0)
            matchups.append({
                'hero_id': m.get('hero_id'),
                'games': games,
                'wins': wins,
                'winrate': (wins / games) if games > 0 else 0
            })
        self.db.cache_matchups(hero_id, matchups)
        return matchups

    def get_meta_heroes(self, limit=10):
        stats = self.get_hero_stats()
        sorted_stats = sorted(stats, key=lambda x: x.get('win_rate', 0), reverse=True)
        return sorted_stats[:limit]
