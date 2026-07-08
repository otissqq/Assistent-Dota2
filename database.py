import sqlite3
import json
import os
from datetime import datetime

APP_DIR = os.path.join(os.path.expanduser("~"), ".dota_draft_assistant")
os.makedirs(APP_DIR, exist_ok=True)
DB_PATH = os.path.join(APP_DIR, "app.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            side TEXT NOT NULL,
            result TEXT NOT NULL,           -- 'win' | 'loss'
            score_team INTEGER NOT NULL,
            score_enemy INTEGER NOT NULL,
            team_heroes TEXT NOT NULL,       -- JSON list
            enemy_heroes TEXT NOT NULL,      -- JSON list
            recommendations TEXT NOT NULL,   -- JSON list
            strengths TEXT NOT NULL,         -- JSON list
            weaknesses TEXT NOT NULL,        -- JSON list
            synergies TEXT NOT NULL,         -- JSON list
            counters TEXT NOT NULL,          -- JSON list
            ai_explanation TEXT NOT NULL,
            radar TEXT NOT NULL,             -- JSON dict
            duration_s REAL NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()


DEFAULT_SETTINGS = {
    "ui_language": "Українська",
    "theme": "dark",
    "auto_update_stats": "1",
    "start_with_windows": "0",
    "screenshot_hotkey": "Print Screen",
    "auto_open_screenshot": "1",
    "screenshot_folder": os.path.join(os.path.expanduser("~"), "DotaDraftAssistant", "Screenshots"),
    "gemini_api_key": "",
    "ai_response_language": "Українська",
    "stratz_api_key": "",
    "last_stratz_sync": "",
}


def get_setting(key, default=None):
    conn = get_conn()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    if row is not None:
        return row["value"]
    return DEFAULT_SETTINGS.get(key, default)


def get_all_settings():
    conn = get_conn()
    rows = conn.execute("SELECT key, value FROM settings").fetchall()
    conn.close()
    merged = dict(DEFAULT_SETTINGS)
    merged.update({r["key"]: r["value"] for r in rows})
    return merged


def set_setting(key, value):
    conn = get_conn()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )
    conn.commit()
    conn.close()


def set_settings(d: dict):
    conn = get_conn()
    for k, v in d.items():
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (k, str(v)),
        )
    conn.commit()
    conn.close()


def save_analysis(record: dict) -> int:
    conn = get_conn()
    cur = conn.execute("""
        INSERT INTO analyses (created_at, side, result, score_team, score_enemy,
            team_heroes, enemy_heroes, recommendations, strengths, weaknesses,
            synergies, counters, ai_explanation, radar, duration_s)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        record["created_at"], record["side"], record["result"],
        record["score_team"], record["score_enemy"],
        json.dumps(record["team_heroes"]), json.dumps(record["enemy_heroes"]),
        json.dumps(record["recommendations"]), json.dumps(record["strengths"]),
        json.dumps(record["weaknesses"]), json.dumps(record["synergies"]),
        json.dumps(record["counters"]), record["ai_explanation"],
        json.dumps(record["radar"]), record["duration_s"],
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def list_analyses(search="", side_filter="Усі сторони"):
    conn = get_conn()
    q = "SELECT * FROM analyses"
    clauses, params = [], []
    if side_filter and side_filter != "Усі сторони":
        clauses.append("side = ?")
        params.append("Radiant" if "Radiant" in side_filter else "Dire")
    if clauses:
        q += " WHERE " + " AND ".join(clauses)
    q += " ORDER BY id DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    results = [dict(r) for r in rows]
    if search:
        s = search.lower()
        def matches(rec):
            heroes = json.loads(rec["team_heroes"]) + json.loads(rec["enemy_heroes"])
            return any(s in h.lower() for h in heroes)
        results = [r for r in results if matches(r)]
    return results


def get_analysis(analysis_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM analyses WHERE id=?", (analysis_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_analysis(analysis_id):
    conn = get_conn()
    conn.execute("DELETE FROM analyses WHERE id=?", (analysis_id,))
    conn.commit()
    conn.close()


def clear_history():
    conn = get_conn()
    conn.execute("DELETE FROM analyses")
    conn.commit()
    conn.close()


def export_history(path):
    conn = get_conn()
    rows = [dict(r) for r in conn.execute("SELECT * FROM analyses ORDER BY id").fetchall()]
    conn.close()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    return len(rows)
