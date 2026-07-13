import random
import time

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.heroes_data import HEROES, HERO_BY_NAME, SYNERGIES, COUNTERS


def _hero(name):
    return HERO_BY_NAME.get(name, {"name": name, "win": 50.0, "role": "Unknown", "attr": "Universal"})


def compute_synergies(team_heroes):
    found = []
    for (a, b), desc in SYNERGIES.items():
        if a in team_heroes and b in team_heroes:
            found.append({"pair": [a, b], "desc": desc})
    return found


def compute_counters(enemy_heroes):
    found = []
    for name, desc in COUNTERS.items():
        if name in enemy_heroes:
            found.append({"hero": name, "desc": desc})
    return found


def team_strength(team_heroes):
    if not team_heroes:
        return 50
    avg_win = sum(_hero(h)["win"] for h in team_heroes) / len(team_heroes)
    bonus = len(compute_synergies(team_heroes)) * 4
    return round(min(99, max(1, avg_win + bonus)))


def radar_scores(team_heroes, enemy_heroes):
    """Returns 6-axis radar comparison: team vs enemy (0-100 scale)."""
    def axis(team, key_roles):
        roles = [_hero(h)["role"] for h in team]
        hits = sum(1 for r in roles if r in key_roles)
        base = 45 + hits * 10 + random.Random(len(team) + hash(tuple(team)) % 7).randint(-5, 10)
        return max(10, min(95, base))

    axes = ["Ініціація", "Стійкість", "Контроль", "Дамаг", "Пуш потенціал", "Синергія"]
    team_vals = [
        axis(team_heroes, {"Initiator", "Offlane"}),
        axis(team_heroes, {"Durable", "Support"}),
        axis(team_heroes, {"Support", "Initiator"}),
        axis(team_heroes, {"Mid", "Carry"}),
        axis(team_heroes, {"Carry", "Pusher"}),
        45 + len(compute_synergies(team_heroes)) * 15,
    ]
    enemy_vals = [
        axis(enemy_heroes, {"Initiator", "Offlane"}),
        axis(enemy_heroes, {"Durable", "Support"}),
        axis(enemy_heroes, {"Support", "Initiator"}),
        axis(enemy_heroes, {"Mid", "Carry"}),
        axis(enemy_heroes, {"Carry", "Pusher"}),
        45 + len(compute_synergies(enemy_heroes)) * 15,
    ]
    return {"axes": axes, "team": [min(95, v) for v in team_vals], "enemy": [min(95, v) for v in enemy_vals]}



def recommend_heroes(team_heroes, enemy_heroes, top_n=5):
    """
    Context-based recommendations for the user's draft.

    Important:
    - this function is NOT the STRATZ meta top;
    - it should not simply sort by winrate;
    - it recommends heroes that close weaknesses of the current draft,
      create synergy, counter enemy heroes, and fill missing roles.
    """
    team_heroes = list(team_heroes or [])
    enemy_heroes = list(enemy_heroes or [])

    taken = set(team_heroes) | set(enemy_heroes)
    candidates = [h for h in HEROES if h["name"] not in taken]

    team_roles = [_hero(h).get("role", "Unknown") for h in team_heroes]
    enemy_roles = [_hero(h).get("role", "Unknown") for h in enemy_heroes]
    team_attrs = [_hero(h).get("attr", "Universal") for h in team_heroes]
    enemy_attrs = [_hero(h).get("attr", "Universal") for h in enemy_heroes]

    # What our team probably needs.
    needed_roles = []
    if "Carry" not in team_roles:
        needed_roles.append("Carry")
    if "Mid" not in team_roles:
        needed_roles.append("Mid")
    if not any(r in team_roles for r in ("Offlane", "Initiator", "Durable")):
        needed_roles.append("Offlane")
    if team_roles.count("Support") < 2:
        needed_roles.append("Support")
    if not any(r in team_roles for r in ("Initiator", "Disabler")):
        needed_roles.append("Initiator")

    if not needed_roles:
        needed_roles = ["Support", "Initiator", "Carry", "Mid"]

    # Draft problems.
    no_control = not any(r in team_roles for r in ("Support", "Initiator", "Disabler"))
    no_late = "Carry" not in team_roles
    no_frontline = not any(r in team_roles for r in ("Offlane", "Durable", "Initiator"))
    many_physical = team_attrs.count("Agility") + team_roles.count("Carry") >= 3
    many_magic_enemy = enemy_attrs.count("Intelligence") >= 2 or enemy_roles.count("Mid") >= 1
    enemy_has_mobility = any(_hero(e).get("role") in {"Mid", "Carry"} for e in enemy_heroes)

    # Deterministic variety for different drafts.
    seed_text = "|".join(sorted(team_heroes) + ["vs"] + sorted(enemy_heroes))
    seed = sum(ord(ch) for ch in seed_text)

    scored = []
    for h in candidates:
        name = h["name"]
        role = h.get("role", "Unknown")
        tag = h.get("tag", "")
        attr = h.get("attr", "Universal")

        # Start from neutral score. Winrate is only a very small tie-breaker,
        # not the main reason.
        score = 50.0
        reasons = []

        # Fill missing roles.
        if role in needed_roles:
            score += 14.0
            reasons.append(f"закриває потрібну роль {role}")
        if tag in needed_roles:
            score += 8.0
            reasons.append(f"додає потрібну функцію {tag}")

        # Synergy with existing allies.
        for t in team_heroes:
            if (t, name) in SYNERGIES:
                score += 10.0
                reasons.append(f"має синергію з {t}")
            elif (name, t) in SYNERGIES:
                score += 10.0
                reasons.append(f"має синергію з {t}")

        # Counter enemy threats.
        for e in enemy_heroes:
            # If we have a counter record for enemy hero, prefer heroes with control/frontline/support.
            if e in COUNTERS and role in {"Support", "Initiator", "Offlane", "Mid"}:
                score += 6.0
                reasons.append(f"допомагає грати проти {e}")
            # Universal lightweight logic for common gaps.
            enemy_role = _hero(e).get("role", "Unknown")
            if enemy_role in {"Carry", "Mid"} and role in {"Support", "Initiator"}:
                score += 4.0
                reasons.append(f"дає контроль проти ключового героя {e}")

        # Fix our draft weaknesses.
        if no_control and role in {"Support", "Initiator"}:
            score += 9.0
            reasons.append("додає контроль, якого не вистачає команді")
        if no_late and role == "Carry":
            score += 8.0
            reasons.append("закриває нестачу лейт-керрі")
        if no_frontline and role in {"Offlane", "Initiator"}:
            score += 7.0
            reasons.append("додає ініціацію або фронтлайн")
        if many_physical and attr in {"Intelligence", "Universal"}:
            score += 4.0
            reasons.append("балансує фізичний драфт магічним впливом")
        if many_magic_enemy and role in {"Support", "Initiator", "Offlane"}:
            score += 3.0
            reasons.append("допомагає пережити магічний тиск суперника")
        if enemy_has_mobility and role in {"Support", "Initiator"}:
            score += 3.0
            reasons.append("корисний проти мобільних героїв")

        # Small meta tie-breaker only.
        score += float(h.get("win", 50.0) - 50.0) * 0.12
        score += float(h.get("pick", 0.0)) * 0.04
        score += ((seed + int(h.get("id", 0)) * 11) % 17) / 20.0

        if not reasons:
            if role in needed_roles:
                reasons.append(f"закриває роль {role}")
            else:
                reasons.append("може доповнити поточний драфт за роллю та функцією")

        scored.append({
            "name": name,
            "role": role,
            "score": round(min(99, max(1, score)), 1),
            "explanation": ", ".join(dict.fromkeys(reasons[:3])) + ".",
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    # Prefer variety: first take best candidates for needed roles, then fill rest.
    result = []
    used = set()

    for need in needed_roles:
        for item in scored:
            hero = _hero(item["name"])
            if item["name"] in used:
                continue
            if item["role"] == need or hero.get("tag") == need:
                result.append(item)
                used.add(item["name"])
                break
        if len(result) >= top_n:
            break

    for item in scored:
        if item["name"] not in used:
            result.append(item)
            used.add(item["name"])
        if len(result) >= top_n:
            break

    return result[:top_n]

def predict_enemy_picks(team_heroes, enemy_heroes, top_n=5):
    """
    Contextual prediction of enemy picks.

    It does NOT add heroes to the real draft. It only predicts what the enemy
    may need if their team is incomplete. The old version mostly sorted heroes
    by winrate, so the same heroes appeared almost every game.
    """
    team_heroes = list(team_heroes or [])
    enemy_heroes = list(enemy_heroes or [])

    slots_left = max(0, 5 - len(enemy_heroes))
    if slots_left <= 0:
        return []

    taken = set(team_heroes) | set(enemy_heroes)
    candidates = [h for h in HEROES if h["name"] not in taken]

    team_roles = [_hero(h).get("role", "Unknown") for h in team_heroes]
    enemy_roles = [_hero(h).get("role", "Unknown") for h in enemy_heroes]
    team_attrs = [_hero(h).get("attr", "Universal") for h in team_heroes]

    # What the enemy probably still needs in a normal draft.
    needed_roles = []
    if "Carry" not in enemy_roles:
        needed_roles.append("Carry")
    if "Mid" not in enemy_roles:
        needed_roles.append("Mid")
    if not any(r in enemy_roles for r in ("Offlane", "Initiator", "Durable")):
        needed_roles.append("Offlane")
    if enemy_roles.count("Support") < 2:
        needed_roles.append("Support")
    if not any(r in enemy_roles for r in ("Initiator", "Disabler")):
        needed_roles.append("Initiator")

    # Keep only as many needs as empty slots, but always leave enough variety.
    if len(needed_roles) > slots_left:
        needed_roles = needed_roles[:slots_left]
    if not needed_roles:
        needed_roles = ["Carry", "Mid", "Support", "Initiator"][:slots_left]

    # Deterministic small variety: same draft = same result, different draft = different result.
    seed_text = "|".join(sorted(team_heroes) + ["vs"] + sorted(enemy_heroes))
    seed = sum(ord(ch) for ch in seed_text)

    # A few lightweight "danger patterns" against the user's current draft.
    user_has_no_support_control = team_roles.count("Support") == 0
    user_has_many_strength = team_attrs.count("Strength") >= 2
    user_has_many_int = team_attrs.count("Intelligence") >= 2
    user_has_no_late_carry = "Carry" not in team_roles

    scored = []
    for h in candidates:
        name = h["name"]
        role = h.get("role", "Unknown")
        tag = h.get("tag", "")
        attr = h.get("attr", "Universal")

        # Base meta weight is intentionally smaller now, so it will not always
        # show the same global winrate heroes.
        score = float(h.get("win", 50.0)) * 0.35 + float(h.get("pick", 0.0)) * 0.20
        reasons = []

        if role in needed_roles:
            score += 12.0
            reasons.append(f"закриває роль {role}, якої може не вистачати супернику")

        if tag in needed_roles or tag in {"Disabler", "Nuker", "Pusher", "Durable"}:
            score += 2.0

        if user_has_no_support_control and (role in {"Initiator", "Support"} or tag in {"Disabler", "Nuker"}):
            score += 4.0
            reasons.append("небезпечний проти складу без стабільного контролю")

        if user_has_many_strength and attr in {"Intelligence", "Universal"}:
            score += 3.0
            reasons.append("може дати магічний тиск проти силових героїв")

        if user_has_many_int and role in {"Carry", "Initiator"}:
            score += 2.5
            reasons.append("може швидко вриватися в магів і тиснути по позиції")

        if user_has_no_late_carry and role == "Carry":
            score += 3.0
            reasons.append("може переграти вашу команду у лейті")

        # If a hero has direct counter/synergy data, use it as a small signal.
        for ally in team_heroes:
            if ally in COUNTERS and role in {"Initiator", "Support", "Carry", "Mid"}:
                score += 0.8

        # Avoid repeating only the same global-meta heroes every match.
        # This does not make results random; it just changes order for different drafts.
        score += ((seed + int(h.get("id", 0)) * 17) % 23) / 10.0

        if not reasons:
            if role in needed_roles:
                reasons.append(f"може закрити роль {role} у драфті суперника")
            else:
                reasons.append("контекстний прогноз для неповного ворожого драфту")

        scored.append({
            "name": name,
            "role": role,
            "score": round(min(99, score), 1),
            "explanation": "Ймовірний пік ворога: " + ", ".join(reasons[:2]) + ".",
        })

    # First choose the best hero for each needed role, then fill the rest.
    scored.sort(key=lambda x: x["score"], reverse=True)
    result = []
    used = set()

    for need in needed_roles:
        for item in scored:
            hero = _hero(item["name"])
            if item["name"] not in used and (item["role"] == need or hero.get("tag") == need):
                result.append(item)
                used.add(item["name"])
                break
        if len(result) >= top_n:
            break

    for item in scored:
        if item["name"] not in used:
            result.append(item)
            used.add(item["name"])
        if len(result) >= top_n:
            break

    return result[:top_n]

def _build_reco_explanation(hero, team_heroes, enemy_heroes):
    bits = []
    for e in enemy_heroes:
        if e in COUNTERS and hero["role"] in {"Initiator", "Offlane", "Support", "Carry"}:
            bits.append(f"Контрить {e}")
    for t in team_heroes:
        if (t, hero["name"]) in SYNERGIES or (hero["name"], t) in SYNERGIES:
            bits.append(f"синергія з {t}")
    if not bits:
        bits.append(f"Сильний {hero['role']} у поточній меті")
    return ", ".join(bits) + "."


def strengths_weaknesses(team_heroes, enemy_heroes):
    strengths, weaknesses = [], []
    roles = [_hero(h)["role"] for h in team_heroes]
    if roles.count("Initiator") + roles.count("Offlane") >= 2:
        strengths.append("Добрий командний контроль")
    attrs = [_hero(h)["attr"] for h in team_heroes]
    if "Strength" in attrs and "Intelligence" in attrs:
        strengths.append("Комбінований магічний та фізичний урон")
    syn = compute_synergies(team_heroes)
    if syn:
        strengths.append(f"Сильна ініціація ({', '.join(syn[0]['pair'])})")
    if any(_hero(h)["name"] == "Phoenix" for h in team_heroes):
        strengths.append("Глобальний потенціал (Phoenix)")
    if not strengths:
        strengths.append("Збалансований склад команди")

    if "Carry" not in roles:
        weaknesses.append("Немає сильного лейт-керрі")
    if roles.count("Support") == 0:
        weaknesses.append("Вразливість до пайву та маг. імунітету")
    if syn:
        weaknesses.append("Залежність від успішної ініціації")
    if not weaknesses:
        weaknesses.append("Потребує точної координації")

    return strengths[:4], weaknesses[:4]


def strategy_tips(enemy_heroes):
    tips = ["Ранній тиск і активність", "Контроль по карті"]
    danger = [e for e in enemy_heroes if e in COUNTERS]
    if danger:
        tips.append(f"Фокус на пріоритетних цілях ({', '.join(danger)})")
    return tips



def meta_top_heroes(top_n=5):
    """
    ТОП-5 поточної мети для окремого STRATZ/meta-блоку.

    Тут winrate/pickrate використовуються спеціально, бо це саме блок мети.
    Рекомендації під конкретний драфт рахуються окремо у recommend_heroes().
    """
    pool = []
    for h in HEROES:
        try:
            win = float(h.get("win", 0) or 0)
        except Exception:
            win = 0.0
        try:
            pick = float(h.get("pick", 0) or 0)
        except Exception:
            pick = 0.0

        pool.append({
            "name": h.get("name", "Unknown"),
            "role": h.get("role", "Unknown"),
            "score": round(win, 1),
            "pick": round(pick, 1),
            "explanation": f"Герой має сильні показники в поточній меті: winrate {round(win, 1)}%, pickrate {round(pick, 1)}%."
        })

    pool.sort(key=lambda x: (x["score"], x["pick"]), reverse=True)
    return pool[:top_n]


def run_full_analysis(team_heroes, enemy_heroes, side="Radiant"):
    start = time.time()

    # Use only heroes that are really present in the draft.
    # The program no longer auto-fills empty slots with heroes.
    team_heroes = list(team_heroes or [])
    enemy_heroes = list(enemy_heroes or [])

    ally_recs = recommend_heroes(team_heroes, enemy_heroes, top_n=5)
    enemy_predictions = predict_enemy_picks(team_heroes, enemy_heroes, top_n=5)
    meta_recs = meta_top_heroes(top_n=5)

    strengths, weaknesses = strengths_weaknesses(team_heroes, enemy_heroes)
    synergies = compute_synergies(team_heroes)
    counters = compute_counters(enemy_heroes)
    radar = radar_scores(team_heroes, enemy_heroes)
    team_score = team_strength(team_heroes)
    enemy_score = team_strength(enemy_heroes)
    duration = round(time.time() - start, 2)

    return {
        "side": side,
        "team_heroes": team_heroes,
        "enemy_heroes": enemy_heroes,
        "recommendations": ally_recs,
        "ally_recommendations": ally_recs,
        "enemy_predictions": enemy_predictions,
        "meta_recommendations": meta_recs,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "strategy": strategy_tips(enemy_heroes),
        "synergies": synergies,
        "counters": counters,
        "radar": radar,
        "team_score": team_score,
        "enemy_score": enemy_score,
        "duration_s": duration,
        "result": "analysis",
    }