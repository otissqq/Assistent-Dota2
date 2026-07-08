"""
STRATZ API integration for the Dota 2 Draft Assistant.

What this service does:
- checks a STRATZ API token;
- downloads weekly win/match statistics from STRATZ GraphQL;
- combines STRATZ live statistics with static hero metadata;
- keeps working offline by falling back to data/heroes_data.py.

No API key is stored here. The key is saved in the local SQLite settings table
through the Settings page.
"""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any

import requests

import data.heroes_data as heroes_data
from data.heroes_data import HEROES as CACHED_HEROES


STRATZ_URL = "https://api.stratz.com/graphql"
OPENDOTA_HEROES_URL = "https://api.opendota.com/api/heroes"
DOTA_HEROLIST_URL = "https://www.dota2.com/datafeed/herolist?language=english"

USER_AGENT = "DotaDraftAssistantCourseProject/1.0"

# This query keeps the STRATZ part small and fast. STRATZ supplies the live
# match/win counts; hero names and roles are merged from constants/OpenDota.
QUERY_HERO_STATS = """
query {
  constants {
    heroes {
      id
      displayName
      shortName
    }
  }
  heroStats {
    winWeek(take: 1) {
      heroId
      winCount
      matchCount
    }
  }
}
"""

ATTR_MAP = {
    "str": "Strength",
    "agi": "Agility",
    "int": "Intelligence",
    "all": "Universal",
}

ATTACK_MAP = {
    "Melee": "Ближній бій",
    "Ranged": "Дальній бій",
}

DIFFICULTY_BY_HERO = {
    "Abaddon": 1,
    "Alchemist": 2,
    "Ancient Apparition": 2,
    "Anti-Mage": 2,
    "Arc Warden": 4,
    "Axe": 1,
    "Bane": 2,
    "Batrider": 3,
    "Beastmaster": 3,
    "Bloodseeker": 1,
    "Bounty Hunter": 2,
    "Brewmaster": 4,
    "Bristleback": 1,
    "Broodmother": 4,
    "Centaur Warrunner": 1,
    "Chaos Knight": 2,
    "Chen": 4,
    "Clinkz": 2,
    "Clockwerk": 2,
    "Crystal Maiden": 1,
    "Dark Seer": 3,
    "Dark Willow": 3,
    "Dazzle": 2,
    "Death Prophet": 2,
    "Disruptor": 2,
    "Doom": 2,
    "Dragon Knight": 1,
    "Drow Ranger": 1,
    "Earth Spirit": 4,
    "Earthshaker": 2,
    "Elder Titan": 3,
    "Ember Spirit": 3,
    "Enchantress": 3,
    "Enigma": 3,
    "Faceless Void": 2,
    "Grimstroke": 2,
    "Gyrocopter": 1,
    "Hoodwink": 2,
    "Huskar": 2,
    "Invoker": 4,
    "Io": 4,
    "Jakiro": 1,
    "Juggernaut": 1,
    "Keeper of the Light": 2,
    "Kez": 3,
    "Kunkka": 2,
    "Legion Commander": 1,
    "Leshrac": 2,
    "Lich": 1,
    "Lifestealer": 1,
    "Lina": 2,
    "Lion": 1,
    "Lone Druid": 4,
    "Luna": 1,
    "Lycan": 3,
    "Magnus": 2,
    "Marci": 2,
    "Mars": 2,
    "Medusa": 1,
    "Meepo": 4,
    "Mirana": 2,
    "Monkey King": 2,
    "Morphling": 4,
    "Muerta": 2,
    "Naga Siren": 3,
    "Nature's Prophet": 3,
    "Necrophos": 1,
    "Night Stalker": 1,
    "Nyx Assassin": 2,
    "Ogre Magi": 1,
    "Omniknight": 1,
    "Oracle": 4,
    "Outworld Destroyer": 2,
    "Pangolier": 3,
    "Phantom Assassin": 1,
    "Phantom Lancer": 2,
    "Phoenix": 3,
    "Primal Beast": 2,
    "Puck": 3,
    "Pudge": 2,
    "Pugna": 2,
    "Queen of Pain": 2,
    "Razor": 1,
    "Riki": 1,
    "Ringmaster": 2,
    "Rubick": 4,
    "Sand King": 2,
    "Shadow Demon": 3,
    "Shadow Fiend": 2,
    "Shadow Shaman": 1,
    "Silencer": 1,
    "Skywrath Mage": 1,
    "Slardar": 1,
    "Slark": 2,
    "Snapfire": 2,
    "Sniper": 1,
    "Spectre": 1,
    "Spirit Breaker": 1,
    "Storm Spirit": 3,
    "Sven": 1,
    "Techies": 3,
    "Templar Assassin": 2,
    "Terrorblade": 2,
    "Tidehunter": 1,
    "Timbersaw": 3,
    "Tinker": 4,
    "Tiny": 2,
    "Treant Protector": 1,
    "Troll Warlord": 1,
    "Tusk": 2,
    "Underlord": 1,
    "Undying": 1,
    "Ursa": 1,
    "Vengeful Spirit": 1,
    "Venomancer": 1,
    "Viper": 1,
    "Visage": 4,
    "Void Spirit": 3,
    "Warlock": 1,
    "Weaver": 2,
    "Windranger": 2,
    "Winter Wyvern": 2,
    "Witch Doctor": 1,
    "Wraith King": 1,
    "Zeus": 1,
}


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key.strip()}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _request_stratz(api_key: str) -> dict[str, Any]:
    response = requests.post(
        STRATZ_URL,
        json={"query": QUERY_HERO_STATS},
        headers=_headers(api_key),
        timeout=15,
    )

    if response.status_code == 401:
        raise RuntimeError("Неправильний або прострочений STRATZ API ключ")
    if response.status_code == 403:
        detail = (response.text or "").strip()[:220]
        raise RuntimeError("STRATZ API заборонив доступ. Перевір ключ або спробуй пізніше" + (f". {detail}" if detail else ""))
    if response.status_code == 429:
        raise RuntimeError("Забагато запитів до STRATZ API. Спробуй пізніше")

    response.raise_for_status()
    payload = response.json() or {}

    if payload.get("errors"):
        first = payload["errors"][0]
        raise RuntimeError(first.get("message", str(first)))

    data = payload.get("data")
    if not isinstance(data, dict):
        raise RuntimeError("STRATZ повернув порожню або некоректну відповідь")

    return data


def _safe_get_json(url: str) -> Any:
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=15)
    response.raise_for_status()
    return response.json()


def _main_role_from_roles(roles: list[str]) -> str:
    priority = [
        "Carry", "Support", "Initiator", "Disabler", "Nuker",
        "Durable", "Escape", "Pusher", "Jungler",
    ]
    for role in priority:
        if role in roles:
            return role
    return roles[0] if roles else "Unknown"


def _tag_from_roles(roles: list[str], main_role: str) -> str:
    for role in roles:
        if role != main_role:
            return role
    return "Meta"


def _difficulty_for(hero_name: str) -> int:
    return max(1, min(5, int(DIFFICULTY_BY_HERO.get(hero_name, 2))))


def _load_opendota_metadata() -> dict[int, dict[str, Any]]:
    """Static hero metadata keyed by hero id."""
    data = _safe_get_json(OPENDOTA_HEROES_URL)
    result: dict[int, dict[str, Any]] = {}

    for hero in data:
        hero_id = int(hero.get("id"))
        name = hero.get("localized_name") or "Unknown"
        roles = hero.get("roles") or []
        main_role = _main_role_from_roles(roles)
        tag = _tag_from_roles(roles, main_role)

        result[hero_id] = {
            "id": hero_id,
            "name": name,
            "attr": ATTR_MAP.get(hero.get("primary_attr"), "Universal"),
            "role": main_role,
            "tag": tag,
            "attack": ATTACK_MAP.get(hero.get("attack_type"), "Невідомо"),
            "difficulty": _difficulty_for(name),
            "desc": "Герой Dota 2. Статистика оновлена через STRATZ API.",
        }

    return result


def _load_dota_hero_names() -> dict[int, str]:
    """Fallback name map from official Dota 2 datafeed."""
    data = _safe_get_json(DOTA_HEROLIST_URL)
    heroes = (((data or {}).get("result") or {}).get("data") or {}).get("heroes") or []
    result: dict[int, str] = {}
    for hero in heroes:
        hero_id = hero.get("id")
        name = hero.get("name_english_loc") or hero.get("name_loc")
        if hero_id is not None and name:
            result[int(hero_id)] = name
    return result


def _stratz_name_map(data: dict[str, Any]) -> dict[int, str]:
    constants = ((data.get("constants") or {}).get("heroes")) or []
    result: dict[int, str] = {}
    for hero in constants:
        hero_id = hero.get("id")
        name = hero.get("displayName")
        if hero_id is not None and name:
            result[int(hero_id)] = name
    return result


def _merge_stats(data: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    local_by_name = {h.get("name", "").strip().lower(): h for h in CACHED_HEROES}
    local_by_id = {int(h.get("id")): h for h in CACHED_HEROES if h.get("id") is not None}

    try:
        static_by_id = _load_opendota_metadata()
    except Exception:
        static_by_id = {}

    name_by_id = _stratz_name_map(data)
    if not name_by_id:
        try:
            name_by_id = _load_dota_hero_names()
        except Exception:
            name_by_id = {}

    win_rows = ((data.get("heroStats") or {}).get("winWeek")) or []
    total_picks = sum(int(row.get("matchCount") or 0) for row in win_rows)
    estimated_matches = total_picks / 10 if total_picks else 0

    result: list[dict[str, Any]] = []
    updated = 0

    for row in win_rows:
        hero_id = row.get("heroId")
        if hero_id is None:
            continue
        hero_id = int(hero_id)

        name = name_by_id.get(hero_id) or static_by_id.get(hero_id, {}).get("name")
        if not name:
            continue

        match_count = int(row.get("matchCount") or 0)
        win_count = int(row.get("winCount") or 0)
        if match_count <= 0:
            continue

        win_rate = round((win_count / match_count) * 100, 1)
        pick_rate = round(min(100.0, (match_count / estimated_matches) * 100), 1) if estimated_matches else 0.0

        local = local_by_id.get(hero_id) or local_by_name.get(name.strip().lower(), {})
        static = static_by_id.get(hero_id, {})

        hero = {
            "id": hero_id,
            "name": name,
            "attr": static.get("attr", local.get("attr", "Universal")),
            "role": static.get("role", local.get("role", "Unknown")),
            "tag": static.get("tag", local.get("tag", "Meta")),
            "win": win_rate,
            "pick": pick_rate,
            "ban": float(local.get("ban", 0.0) or 0.0),
            "desc": local.get("desc") or static.get("desc") or "Герой Dota 2. Статистика оновлена через STRATZ API.",
            "difficulty": int(static.get("difficulty", local.get("difficulty", 2)) or 2),
            "attack": static.get("attack", local.get("attack", "Невідомо")),
        }
        result.append(hero)
        updated += 1

    result.sort(key=lambda h: h["name"])
    return result, updated


def _apply_to_runtime_cache(heroes: list[dict[str, Any]]) -> None:
    """Keep other app pages that import HEROES in sync during this run."""
    heroes_data.HEROES[:] = heroes
    if hasattr(heroes_data, "HERO_BY_NAME"):
        heroes_data.HERO_BY_NAME.clear()
        heroes_data.HERO_BY_NAME.update({h["name"]: h for h in heroes})


def test_connection(api_key: str) -> tuple[bool, str]:
    api_key = (api_key or "").strip()
    if len(api_key) < 8:
        return False, "Порожній або занадто короткий STRATZ API ключ"

    try:
        data = _request_stratz(api_key)
        rows = ((data.get("heroStats") or {}).get("winWeek")) or []
        return True, f"Підключення успішне. Отримано статистику для {len(rows)} героїв"
    except Exception as e:
        return False, f"Помилка STRATZ API: {e}"


def fetch_hero_stats(api_key: str) -> tuple[list[dict[str, Any]], bool, str]:
    """
    Returns: heroes, used_live_data, message.
    If STRATZ is unavailable, cached local data is returned and used_live_data=False.
    """
    api_key = (api_key or "").strip()
    if not api_key:
        return copy.deepcopy(CACHED_HEROES), False, "STRATZ API ключ не вказано. Використано локальні дані"

    try:
        data = _request_stratz(api_key)
        heroes, updated = _merge_stats(data)
        if not heroes or updated == 0:
            return copy.deepcopy(CACHED_HEROES), False, "STRATZ API відповів, але статистику героїв не вдалося обробити"

        _apply_to_runtime_cache(heroes)
        return heroes, True, f"Статистику оновлено з STRATZ API ({updated} героїв)"
    except Exception as e:
        return copy.deepcopy(CACHED_HEROES), False, f"Не вдалося отримати STRATZ статистику: {e}"


def now_str() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M")
