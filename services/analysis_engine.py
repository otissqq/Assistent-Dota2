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
    Scores every hero not already in the draft based on:
      - base winrate
      - bonus if it synergizes with current team
      - bonus if it counters an enemy hero
      - small random "meta" jitter so results feel alive
    """
    taken = set(team_heroes) | set(enemy_heroes)
    candidates = [h for h in HEROES if h["name"] not in taken]
    scored = []
    for h in candidates:
        score = h["win"]
        reasons = []
        for t in team_heroes:
            if (t, h["name"]) in SYNERGIES or (h["name"], t) in SYNERGIES:
                score += 5
                reasons.append(f"синергія з {t}")
        for e in enemy_heroes:
            if e in COUNTERS and h["role"] in {"Initiator", "Offlane", "Support"}:
                score += 1.5
        if h["name"] in COUNTERS:
            score += 4
            reasons.append(f"контрить {h['name']}")
        score += random.Random(h["id"] * 13 + len(team_heroes)).uniform(-1.5, 1.5)
        explanation = _build_reco_explanation(h, team_heroes, enemy_heroes)
        scored.append({
            "name": h["name"], "role": h["role"], "score": round(min(99, score), 1),
            "explanation": explanation,
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_n]


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


def run_full_analysis(team_heroes, enemy_heroes, side="Radiant"):
    start = time.time()
    recs = recommend_heroes(team_heroes, enemy_heroes, top_n=5)
    strengths, weaknesses = strengths_weaknesses(team_heroes, enemy_heroes)
    synergies = compute_synergies(team_heroes)
    counters = compute_counters(enemy_heroes)
    radar = radar_scores(team_heroes, enemy_heroes)
    team_score = team_strength(team_heroes)
    enemy_score = team_strength(enemy_heroes)
    duration = round(time.time() - start + random.uniform(2.5, 4.2), 1)  # simulate analysis latency for UX

    return {
        "side": side,
        "team_heroes": team_heroes,
        "enemy_heroes": enemy_heroes,
        "recommendations": recs,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "strategy": strategy_tips(enemy_heroes),
        "synergies": synergies,
        "counters": counters,
        "radar": radar,
        "team_score": team_score,
        "enemy_score": enemy_score,
        "duration_s": duration,
        "result": "win" if team_score >= enemy_score else "loss",
    }
