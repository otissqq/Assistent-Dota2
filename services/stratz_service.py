"""
STRATZ API integration.
STRATZ дає win rate / pick rate.
OpenDota дає атрибут, роль, тип атаки, складність.
"""

import copy
from datetime import datetime
import requests

import data.heroes_data as heroes_data
from data.heroes_data import HEROES as CACHED_HEROES


STRATZ_URL = "https://api.stratz.com/graphql"
DOTA_HEROLIST_URL = "https://www.dota2.com/datafeed/herolist?language=english"
OPENDOTA_HEROES_URL = "https://api.opendota.com/api/heroes"


QUERY_HERO_STATS = """
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


def _headers(api_key: str):
    return {
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "STRATZ_API",
        "Content-Type": "application/json",
    }


def _request_stratz(api_key: str):
    response = requests.post(
        STRATZ_URL,
        json={"query": QUERY_HERO_STATS},
        headers=_headers(api_key),
        timeout=15,
    )

    if response.status_code == 401:
        raise Exception("Неправильний або прострочений STRATZ API ключ")

    if response.status_code == 403:
        raise Exception("STRATZ API заборонив доступ. Перевір ключ")

    if response.status_code == 429:
        raise Exception("Забагато запитів до STRATZ API. Спробуй пізніше")

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise Exception(str(data["errors"][0].get("message", "GraphQL error")))

    return data["data"]["heroStats"]["winWeek"]


def _load_dota_hero_names():
    """
    STRATZ повертає heroId, а нам треба назва героя.
    Назви беремо з dota2.com.
    """
    response = requests.get(
        DOTA_HEROLIST_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    response.raise_for_status()

    data = response.json()
    heroes = data["result"]["data"]["heroes"]

    result = {}

    for hero in heroes:
        hero_id = int(hero["id"])
        hero_name = hero.get("name_english_loc") or hero.get("name_loc")

        if hero_name:
            result[hero_id] = hero_name

    return result


def _main_role_from_roles(roles):
    priority = [
        "Carry",
        "Support",
        "Initiator",
        "Disabler",
        "Nuker",
        "Durable",
        "Escape",
        "Pusher",
        "Jungler",
    ]

    for role in priority:
        if role in roles:
            return role

    return "Unknown"


def _tag_from_roles(roles, main_role):
    for role in roles:
        if role != main_role:
            return role

    return "Meta"


def _difficulty_from_roles(roles, name):
    hard_heroes = {
        "Invoker", "Meepo", "Chen", "Arc Warden", "Visage",
        "Earth Spirit", "Brewmaster", "Lone Druid", "Rubick",
        "Tinker", "Morphling", "Io", "Oracle"
    }

    medium_heroes = {
        "Puck", "Storm Spirit", "Ember Spirit", "Void Spirit",
        "Shadow Demon", "Dark Seer", "Naga Siren", "Beastmaster",
        "Elder Titan", "Phoenix", "Pangolier"
    }

    if name in hard_heroes:
        return 3

    if name in medium_heroes:
        return 2

    return 1


def _load_opendota_metadata():
    """
    Дані героя: Strength/Agility/Intelligence/Universal,
    атака, ролі, складність.
    Ключ — heroId.
    """
    response = requests.get(
        OPENDOTA_HEROES_URL,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    response.raise_for_status()

    data = response.json()
    result = {}

    for hero in data:
        hero_id = int(hero.get("id"))
        name = hero.get("localized_name", "")

        roles = hero.get("roles") or []
        main_role = _main_role_from_roles(roles)
        tag = _tag_from_roles(roles, main_role)

        result[hero_id] = {
            "name": name,
            "attr": ATTR_MAP.get(hero.get("primary_attr"), "Universal"),
            "role": main_role,
            "tag": tag,
            "attack": ATTACK_MAP.get(hero.get("attack_type"), "Невідомо"),
            "difficulty": _difficulty_from_roles(roles, name),
        }

    return result


def _merge_stratz_with_local(stratz_rows, hero_names):
    local_by_name = {h["name"]: h for h in CACHED_HEROES}

    try:
        static_by_id = _load_opendota_metadata()
    except Exception:
        static_by_id = {}

    total_picks = sum(int(row.get("matchCount") or 0) for row in stratz_rows)
    estimated_matches = total_picks / 10 if total_picks else 0

    result = []

    for row in stratz_rows:
        hero_id = int(row.get("heroId"))
        name = hero_names.get(hero_id)

        if not name:
            continue

        match_count = int(row.get("matchCount") or 0)
        win_count = int(row.get("winCount") or 0)

        win_rate = round((win_count / match_count) * 100, 1) if match_count else 0
        pick_rate = round((match_count / estimated_matches) * 100, 1) if estimated_matches else 0

        local = local_by_name.get(name, {})
        static = static_by_id.get(hero_id, {})

        hero = {
            "id": hero_id,
            "name": name,

            "attr": static.get("attr", local.get("attr", "Universal")),
            "role": static.get("role", local.get("role", "Unknown")),
            "tag": static.get("tag", local.get("tag", "Meta")),

            "win": win_rate,
            "pick": pick_rate,
            "ban": local.get("ban", 0.0),

            "desc": local.get(
                "desc",
                "Герой Dota 2. Статистика оновлена через STRATZ API."
            ),

            "difficulty": static.get("difficulty", local.get("difficulty", 1)),
            "attack": static.get("attack", local.get("attack", "Невідомо")),
        }

        result.append(hero)

    result.sort(key=lambda h: h["name"])
    return result


def _apply_to_runtime_cache(heroes):
    heroes_data.HEROES[:] = heroes

    if hasattr(heroes_data, "HERO_BY_NAME"):
        heroes_data.HERO_BY_NAME.clear()
        heroes_data.HERO_BY_NAME.update({h["name"]: h for h in heroes_data.HEROES})


def test_connection(api_key: str):
    if not api_key or len(api_key.strip()) < 8:
        return False, "Порожній або занадто короткий STRATZ API ключ"

    try:
        rows = _request_stratz(api_key.strip())
        return True, f"Підключення успішне. Отримано статистику для {len(rows)} героїв"
    except Exception as e:
        return False, f"Помилка STRATZ API: {e}"


def fetch_hero_stats(api_key: str):
    """
    Повертає:
    heroes, used_live_data, message
    """
    if not api_key:
        return copy.deepcopy(CACHED_HEROES), False, "STRATZ API ключ не вказано. Використано локальні дані"

    try:
        stratz_rows = _request_stratz(api_key.strip())
        hero_names = _load_dota_hero_names()

        heroes = _merge_stratz_with_local(stratz_rows, hero_names)

        if not heroes:
            return copy.deepcopy(CACHED_HEROES), False, "STRATZ API відповів, але герої не були оброблені"

        _apply_to_runtime_cache(heroes)

        return heroes, True, "Статистику оновлено з STRATZ API"

    except Exception as e:
        return copy.deepcopy(CACHED_HEROES), False, f"Не вдалося отримати STRATZ статистику: {e}"


def now_str():
    return datetime.now().strftime("%d.%m.%Y %H:%M")