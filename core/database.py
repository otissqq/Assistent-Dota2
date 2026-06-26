import sqlite3
import json
from datetime import datetime, timedelta
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from config.settings import DB_PATH

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self._create_tables()
        self._seed_demo_data()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                radiant_heroes TEXT,
                dire_heroes TEXT,
                radiant_strength REAL,
                dire_strength REAL,
                recommendations TEXT,
                ai_analysis TEXT,
                screenshot_path TEXT,
                patch TEXT,
                mode TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hero_cache (
                hero_id INTEGER PRIMARY KEY,
                name TEXT,
                localized_name TEXT,
                localized_name_ru TEXT,
                localized_name_en TEXT,
                primary_attr TEXT,
                attack_type TEXT,
                roles TEXT,
                winrate REAL,
                pickrate REAL,
                banrate REAL,
                complexity INTEGER,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matchups_cache (
                hero_id INTEGER,
                opponent_id INTEGER,
                wins INTEGER,
                games_played INTEGER,
                winrate REAL,
                updated_at TEXT,
                PRIMARY KEY (hero_id, opponent_id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS item_builds (
                hero_id INTEGER,
                item_name TEXT,
                category TEXT,
                winrate REAL,
                PRIMARY KEY (hero_id, item_name)
            )
        """)
        self.conn.commit()

    def _seed_demo_data(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hero_cache")
        if cursor.fetchone()[0] > 0:
            return

        demo_heroes = [
            (1, "npc_dota_hero_antimage", "Anti-Mage", "Anti-Mage", "Anti-Mage", "agi", "Melee", json.dumps(["Carry", "Escape", "Nuker"]), 49.2, 8.1, 2.3, 1, datetime.now().isoformat()),
            (2, "npc_dota_hero_axe", "Axe", "Axe", "Axe", "str", "Melee", json.dumps(["Initiator", "Durable", "Disabler", "Jungler"]), 54.1, 12.5, 3.1, 1, datetime.now().isoformat()),
            (3, "npc_dota_hero_bane", "Bane", "Bane", "Bane", "int", "Ranged", json.dumps(["Support", "Disabler", "Nuker", "Durable"]), 53.4, 4.2, 1.8, 2, datetime.now().isoformat()),
            (4, "npc_dota_hero_bloodseeker", "Bloodseeker", "Bloodseeker", "Bloodseeker", "agi", "Melee", json.dumps(["Carry", "Disabler", "Jungler", "Nuker", "Initiator"]), 48.7, 3.5, 0.9, 1, datetime.now().isoformat()),
            (5, "npc_dota_hero_crystal_maiden", "Crystal Maiden", "Crystal Maiden", "Crystal Maiden", "int", "Ranged", json.dumps(["Support", "Disabler", "Nuker", "Jungler"]), 51.8, 9.2, 1.1, 1, datetime.now().isoformat()),
            (6, "npc_dota_hero_drow_ranger", "Drow Ranger", "Drow Ranger", "Drow Ranger", "agi", "Ranged", json.dumps(["Carry", "Disabler", "Pusher"]), 50.3, 7.8, 1.5, 1, datetime.now().isoformat()),
            (7, "npc_dota_hero_earthshaker", "Earthshaker", "Earthshaker", "Earthshaker", "str", "Melee", json.dumps(["Support", "Initiator", "Disabler", "Nuker"]), 52.6, 6.1, 0.8, 2, datetime.now().isoformat()),
            (8, "npc_dota_hero_juggernaut", "Juggernaut", "Juggernaut", "Juggernaut", "agi", "Melee", json.dumps(["Carry", "Pusher", "Escape"]), 51.9, 15.3, 2.1, 1, datetime.now().isoformat()),
            (9, "npc_dota_hero_mirana", "Mirana", "Mirana", "Mirana", "agi", "Ranged", json.dumps(["Carry", "Support", "Escape", "Nuker", "Disabler"]), 50.8, 11.2, 1.9, 2, datetime.now().isoformat()),
            (10, "npc_dota_hero_morphling", "Morphling", "Morphling", "Morphling", "agi", "Ranged", json.dumps(["Carry", "Escape", "Durable", "Nuker", "Disabler"]), 47.3, 4.8, 1.2, 3, datetime.now().isoformat()),
            (11, "npc_dota_hero_nevermore", "Shadow Fiend", "Shadow Fiend", "Shadow Fiend", "agi", "Ranged", json.dumps(["Carry", "Nuker"]), 49.1, 8.7, 2.4, 2, datetime.now().isoformat()),
            (12, "npc_dota_hero_pudge", "Pudge", "Pudge", "Pudge", "str", "Melee", json.dumps(["Disabler", "Initiator", "Durable", "Nuker"]), 51.2, 22.1, 5.3, 2, datetime.now().isoformat()),
            (13, "npc_dota_hero_razor", "Razor", "Razor", "Razor", "agi", "Ranged", json.dumps(["Carry", "Durable", "Nuker", "Pusher"]), 50.5, 5.4, 0.7, 1, datetime.now().isoformat()),
            (14, "npc_dota_hero_sand_king", "Sand King", "Sand King", "Sand King", "str", "Melee", json.dumps(["Initiator", "Disabler", "Support", "Nuker", "Escape", "Jungler"]), 51.3, 4.9, 0.6, 2, datetime.now().isoformat()),
            (15, "npc_dota_hero_storm_spirit", "Storm Spirit", "Storm Spirit", "Storm Spirit", "int", "Ranged", json.dumps(["Carry", "Escape", "Nuker", "Initiator", "Disabler"]), 56.0, 3.2, 1.5, 2, datetime.now().isoformat()),
            (16, "npc_dota_hero_sven", "Sven", "Sven", "Sven", "str", "Melee", json.dumps(["Carry", "Disabler", "Initiator", "Durable", "Nuker"]), 50.1, 6.3, 0.9, 1, datetime.now().isoformat()),
            (17, "npc_dota_hero_tiny", "Tiny", "Tiny", "Tiny", "str", "Melee", json.dumps(["Carry", "Nuker", "Pusher", "Initiator", "Durable", "Disabler"]), 49.8, 5.7, 1.1, 2, datetime.now().isoformat()),
            (18, "npc_dota_hero_vengefulspirit", "Vengeful Spirit", "Vengeful Spirit", "Vengeful Spirit", "agi", "Ranged", json.dumps(["Support", "Initiator", "Disabler", "Nuker", "Escape"]), 54.3, 7.1, 1.4, 1, datetime.now().isoformat()),
            (19, "npc_dota_hero_windrunner", "Windranger", "Windranger", "Windranger", "int", "Ranged", json.dumps(["Carry", "Support", "Disabler", "Escape", "Nuker"]), 50.9, 8.4, 1.6, 2, datetime.now().isoformat()),
            (20, "npc_dota_hero_zuus", "Zeus", "Zeus", "Zeus", "int", "Ranged", json.dumps(["Nuker"]), 51.7, 10.3, 2.8, 1, datetime.now().isoformat()),
            (21, "npc_dota_hero_invoker", "Invoker", "Invoker", "Invoker", "int", "Ranged", json.dumps(["Carry", "Nuker", "Disabler", "Escape", "Pusher"]), 53.6, 15.9, 4.2, 3, datetime.now().isoformat()),
            (22, "npc_dota_hero_sniper", "Sniper", "Sniper", "Sniper", "agi", "Ranged", json.dumps(["Carry", "Nuker"]), 50.2, 12.8, 3.1, 1, datetime.now().isoformat()),
            (23, "npc_dota_hero_spectre", "Spectre", "Spectre", "Spectre", "agi", "Melee", json.dumps(["Carry", "Durable", "Escape"]), 55.5, 6.2, 1.8, 2, datetime.now().isoformat()),
            (24, "npc_dota_hero_faceless_void", "Faceless Void", "Faceless Void", "Faceless Void", "agi", "Melee", json.dumps(["Carry", "Initiator", "Disabler", "Escape", "Durable"]), 52.8, 13.4, 3.5, 2, datetime.now().isoformat()),
            (25, "npc_dota_hero_ursa", "Ursa", "Ursa", "Ursa", "agi", "Melee", json.dumps(["Carry", "Jungler", "Durable", "Disabler"]), 53.1, 7.9, 1.7, 1, datetime.now().isoformat()),
            (26, "npc_dota_hero_lich", "Lich", "Lich", "Lich", "int", "Ranged", json.dumps(["Support", "Nuker"]), 51.4, 8.6, 1.3, 1, datetime.now().isoformat()),
            (27, "npc_dota_hero_lion", "Lion", "Lion", "Lion", "int", "Ranged", json.dumps(["Support", "Disabler", "Nuker", "Initiator"]), 52.9, 11.7, 2.1, 1, datetime.now().isoformat()),
            (28, "npc_dota_hero_tidehunter", "Tidehunter", "Tidehunter", "Tidehunter", "str", "Melee", json.dumps(["Initiator", "Durable", "Disabler", "Nuker"]), 50.7, 5.3, 0.8, 1, datetime.now().isoformat()),
            (29, "npc_dota_hero_witch_doctor", "Witch Doctor", "Witch Doctor", "Witch Doctor", "int", "Ranged", json.dumps(["Support", "Nuker", "Disabler"]), 51.1, 6.8, 0.9, 1, datetime.now().isoformat()),
            (30, "npc_dota_hero_enigma", "Enigma", "Enigma", "Enigma", "int", "Ranged", json.dumps(["Disabler", "Jungler", "Initiator", "Pusher"]), 55.9, 3.1, 1.2, 2, datetime.now().isoformat()),
            (31, "npc_dota_hero_tinker", "Tinker", "Tinker", "Tinker", "int", "Ranged", json.dumps(["Carry", "Nuker", "Pusher"]), 47.8, 4.2, 2.1, 2, datetime.now().isoformat()),
            (32, "npc_dota_hero_silencer", "Silencer", "Silencer", "Silencer", "int", "Ranged", json.dumps(["Carry", "Support", "Disabler", "Initiator", "Nuker"]), 50.3, 5.1, 0.7, 2, datetime.now().isoformat()),
            (33, "npc_dota_hero_necrolyte", "Necrophos", "Necrophos", "Necrophos", "int", "Ranged", json.dumps(["Carry", "Nuker", "Durable", "Disabler"]), 52.4, 7.3, 1.5, 1, datetime.now().isoformat()),
            (34, "npc_dota_hero_warlock", "Warlock", "Warlock", "Warlock", "int", "Ranged", json.dumps(["Support", "Initiator", "Disabler"]), 51.6, 3.8, 0.4, 1, datetime.now().isoformat()),
            (35, "npc_dota_hero_beastmaster", "Beastmaster", "Beastmaster", "Beastmaster", "str", "Melee", json.dumps(["Initiator", "Disabler", "Durable", "Nuker"]), 49.5, 3.2, 0.6, 2, datetime.now().isoformat()),
            (36, "npc_dota_hero_queenofpain", "Queen of Pain", "Queen of Pain", "Queen of Pain", "int", "Ranged", json.dumps(["Carry", "Nuker", "Escape"]), 49.2, 6.5, 1.3, 2, datetime.now().isoformat()),
            (37, "npc_dota_hero_venomancer", "Venomancer", "Venomancer", "Venomancer", "agi", "Ranged", json.dumps(["Support", "Nuker", "Initiator", "Pusher"]), 50.6, 4.9, 0.5, 1, datetime.now().isoformat()),
            (38, "npc_dota_hero_phantom_assassin", "Phantom Assassin", "Phantom Assassin", "Phantom Assassin", "agi", "Melee", json.dumps(["Carry", "Escape"]), 51.3, 11.2, 2.3, 1, datetime.now().isoformat()),
            (39, "npc_dota_hero_treant", "Treant Protector", "Treant Protector", "Treant Protector", "str", "Melee", json.dumps(["Support", "Initiator", "Durable", "Disabler", "Escape"]), 54.7, 4.7, 0.6, 2, datetime.now().isoformat()),
            (40, "npc_dota_hero_ogre_magi", "Ogre Magi", "Ogre Magi", "Ogre Magi", "int", "Melee", json.dumps(["Support", "Nuker", "Durable", "Disabler", "Initiator"]), 52.1, 8.3, 0.9, 1, datetime.now().isoformat()),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO hero_cache VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, demo_heroes)

        # Demo history
        demo_analyses = [
            (datetime.now().isoformat(), json.dumps(["Axe", "Pudge", "Zeus", "Lion", "Juggernaut"]), json.dumps(["Invoker", "Shadow Fiend", "Sniper", "Vengeful Spirit", "Medusa"]), 58.7, 41.3, json.dumps([{"name": "Silencer", "score": 54.0}, {"name": "Razor", "score": 53.0}, {"name": "Necrophos", "score": 52.0}]), "Radiant має перевагу завдяки сильному контролю та ранній грі.", "", "7.41d", "All Pick"),
            ((datetime.now() - timedelta(hours=2)).isoformat(), json.dumps(["Anti-Mage", "Crystal Maiden", "Tidehunter", "Lion", "Sniper"]), json.dumps(["Storm Spirit", "Pudge", "Zeus", "Witch Doctor", "Faceless Void"]), 52.1, 47.9, json.dumps([{"name": "Silencer", "score": 56.2}, {"name": "Enigma", "score": 55.1}]), "Dire має кращий лейтгейм через Void та Storm Spirit.", "", "7.41d", "All Pick"),
            ((datetime.now() - timedelta(days=1)).isoformat(), json.dumps(["Invoker", "Pudge", "Spectre", "Shadow Fiend", "Lion"]), json.dumps(["Axe", "Juggernaut", "Zeus", "Crystal Maiden", "Anti-Mage"]), 61.2, 38.8, json.dumps([{"name": "Enigma", "score": 58.3}, {"name": "Bane", "score": 57.1}]), "Сильний драфт Radiant з хорошою синергією між Invoker та Spectre.", "", "7.41c", "Ranked"),
        ]
        cursor.executemany("""
            INSERT INTO analyses (timestamp, radiant_heroes, dire_heroes, radiant_strength, dire_strength, recommendations, ai_analysis, screenshot_path, patch, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, demo_analyses)

        # Demo items
        demo_items = [
            (2, "Blade Mail", "core", 58.2),
            (2, "Blink Dagger", "core", 62.1),
            (2, "Heart of Tarrasque", "core", 55.3),
            (2, "Crimson Guard", "situational", 53.7),
            (2, "Phase Boots", "starting", 51.2),
            (8, "Battle Fury", "core", 59.8),
            (8, "Manta Style", "core", 57.3),
            (8, "Abyssal Blade", "core", 61.2),
            (8, "Power Treads", "starting", 52.1),
            (8, "Black King Bar", "situational", 64.5),
            (21, "Aghanim's Scepter", "core", 63.2),
            (21, "Octarine Core", "core", 58.7),
            (21, "Blink Dagger", "situational", 55.1),
            (21, "Refresher Orb", "situational", 61.8),
            (23, "Radiance", "core", 60.1),
            (23, "Manta Style", "core", 58.9),
            (23, "Diffusal Blade", "core", 56.3),
            (24, "Battle Fury", "core", 61.5),
            (24, "Aghanim's Scepter", "core", 64.2),
            (24, "Skadi", "core", 59.8),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO item_builds VALUES (?, ?, ?, ?)
        """, demo_items)

        self.conn.commit()

    def save_analysis(self, radiant, dire, r_strength, d_strength, recommendations, ai_text, screenshot="", patch="7.41d", mode="All Pick"):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO analyses (timestamp, radiant_heroes, dire_heroes, radiant_strength, dire_strength, recommendations, ai_analysis, screenshot_path, patch, mode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            json.dumps(radiant),
            json.dumps(dire),
            r_strength,
            d_strength,
            json.dumps(recommendations),
            ai_text,
            screenshot,
            patch,
            mode
        ))
        self.conn.commit()
        return cursor.lastrowid

    def get_history(self, limit=50):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM analyses ORDER BY timestamp DESC LIMIT ?", (limit,))
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def get_analysis_by_id(self, analysis_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
        cols = [d[0] for d in cursor.description]
        row = cursor.fetchone()
        return dict(zip(cols, row)) if row else None

    def delete_analysis(self, analysis_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        self.conn.commit()

    def cache_heroes(self, heroes_data):
        cursor = self.conn.cursor()
        for h in heroes_data:
            cursor.execute("""
                INSERT OR REPLACE INTO hero_cache (hero_id, name, localized_name, primary_attr, attack_type, roles, winrate, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (h['id'], h['name'], h.get('localized_name',''), h.get('primary_attr',''), h.get('attack_type',''), json.dumps(h.get('roles',[])), h.get('winrate',0), datetime.now().isoformat()))
        self.conn.commit()

    def get_cached_heroes(self, search="", role_filter=None, sort_by="winrate"):
        cursor = self.conn.cursor()
        query = "SELECT * FROM hero_cache WHERE 1=1"
        params = []
        if search:
            query += " AND (localized_name LIKE ? OR localized_name_ru LIKE ? OR localized_name_en LIKE ? OR name LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"])
        if role_filter:
            query += " AND roles LIKE ?"
            params.append(f"%{role_filter}%")
        query += f" ORDER BY {sort_by} DESC"
        cursor.execute(query, params)
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def get_hero_by_name(self, name):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM hero_cache WHERE localized_name = ? OR localized_name_ru = ? OR localized_name_en = ? OR name = ?", (name, name, name, name))
        cols = [d[0] for d in cursor.description]
        row = cursor.fetchone()
        return dict(zip(cols, row)) if row else None

    def get_top_heroes(self, limit=10):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM hero_cache ORDER BY winrate DESC LIMIT ?", (limit,))
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def get_hero_items(self, hero_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM item_builds WHERE hero_id = ?", (hero_id,))
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def cache_matchups(self, hero_id, matchups):
        cursor = self.conn.cursor()
        for m in matchups:
            cursor.execute("""
                INSERT OR REPLACE INTO matchups_cache (hero_id, opponent_id, wins, games_played, winrate, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (hero_id, m['hero_id'], m.get('wins',0), m.get('games',1), m.get('winrate',0), datetime.now().isoformat()))
        self.conn.commit()

    def get_matchups(self, hero_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM matchups_cache WHERE hero_id = ?", (hero_id,))
        cols = [d[0] for d in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def get_stats_summary(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM analyses")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM hero_cache")
        heroes = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(radiant_strength) FROM analyses")
        avg_r = cursor.fetchone()[0] or 0
        return {"total_analyses": total, "total_heroes": heroes, "avg_radiant_strength": avg_r}
