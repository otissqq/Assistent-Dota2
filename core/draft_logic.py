import sys
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from core.database import DatabaseManager
from core.opendota_api import OpenDotaClient

class DraftEngine:
    def __init__(self):
        self.db = DatabaseManager()
        self.api = OpenDotaClient()
        self.heroes = {}
        self._load_heroes()

    def _load_heroes(self):
        heroes = self.db.get_cached_heroes()
        for h in heroes:
            name = h.get('localized_name') or h.get('name', '')
            if name:
                self.heroes[name] = h

    def refresh_heroes(self):
        self._load_heroes()

    def calculate_team_strength(self, hero_names):
        if not hero_names:
            return 50.0

        total_score = 0.0
        for name in hero_names:
            h = self.heroes.get(name)
            if h:
                winrate = h.get('winrate', 50)
                total_score += winrate
            else:
                total_score += 50

        avg = total_score / len(hero_names)
        return min(100, max(0, avg))

    def get_counter_score(self, hero_name, enemy_team):
        h = self.heroes.get(hero_name)
        if not h:
            return 50.0

        hero_id = h.get('hero_id')
        if not hero_id:
            return 50.0

        matchups = self.db.get_matchups(hero_id)
        if not matchups:
            try:
                matchups = self.api.get_hero_matchups(hero_id)
            except:
                return 50.0

        matchup_map = {m['opponent_id']: m for m in matchups}
        score = 50.0

        for enemy in enemy_team:
            eh = self.heroes.get(enemy)
            if eh:
                eid = eh.get('hero_id')
                if eid in matchup_map:
                    score += matchup_map[eid].get('winrate', 0) * 50

        return score / max(1, len(enemy_team))

    def get_synergy_score(self, hero_name, ally_team):
        h = self.heroes.get(hero_name)
        if not h:
            return 50.0

        roles = set(h.get('roles', []))
        synergy = 50.0

        for ally in ally_team:
            ah = self.heroes.get(ally)
            if ah:
                a_roles = set(ah.get('roles', []))
                if roles & a_roles:
                    synergy -= 5
                else:
                    synergy += 5

        return min(100, max(0, synergy))

    def calculate_recommendations(self, enemy_team, ally_team, role_filter=None, limit=10):
        recommendations = []

        for name, h in self.heroes.items():
            if name in enemy_team or name in ally_team:
                continue

            if role_filter and role_filter not in h.get('roles', []):
                continue

            base = self.calculate_team_strength([name])
            counter = self.get_counter_score(name, enemy_team)
            synergy = self.get_synergy_score(name, ally_team)

            score = base * 0.3 + counter * 0.5 + synergy * 0.2
            recommendations.append({
                'name': name,
                'score': score,
                'base': base,
                'counter': counter,
                'synergy': synergy,
                'roles': h.get('roles', []),
                'winrate': h.get('winrate', 50)
            })

        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]

    def analyze_draft(self, radiant, dire):
        r_strength = self.calculate_team_strength(radiant)
        d_strength = self.calculate_team_strength(dire)

        recs_radiant = self.calculate_recommendations(dire, radiant)
        recs_dire = self.calculate_recommendations(radiant, dire)

        return {
            'radiant_strength': r_strength,
            'dire_strength': d_strength,
            'radiant_recommendations': recs_radiant,
            'dire_recommendations': recs_dire
        }

    def get_hero_info(self, hero_name):
        return self.heroes.get(hero_name)
