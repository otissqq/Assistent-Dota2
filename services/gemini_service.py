"""
Gemini AI integration for the Dota 2 Draft Assistant.

What it does:
1) Generates the text in the "Пояснення від ШІ" block.
2) If the draft is incomplete, suggests missing allied heroes and returns
   valid hero names only from the local HEROES database.

If the API key is missing or the request fails, the app falls back to local
recommendations, so the program continues to work offline.
"""

from __future__ import annotations

import json
import re
from typing import Iterable

import requests

from data.heroes_data import HEROES
from services import analysis_engine

# generateContent REST endpoint. The code tries several models so that the app
# still works if one model is not available for a particular API key.
GEMINI_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_MODELS = ["gemini-2.0-flash"]
FAST_GEMINI_TIMEOUT = 6


def _hero_names() -> set[str]:
    return {h["name"] for h in HEROES}


def _normalize_list(names: Iterable[str]) -> list[str]:
    valid = _hero_names()
    result = []
    seen = set()
    for name in names or []:
        if not isinstance(name, str):
            continue
        clean = name.strip()
        if clean in valid and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result


def _extract_text_from_generate_content(data: dict) -> str:
    """Extract text from a Gemini generateContent response."""
    parts = []
    for candidate in data.get("candidates", []) or []:
        content = candidate.get("content", {}) or {}
        for part in content.get("parts", []) or []:
            text = part.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    return "\n".join(parts).strip()


def _call_gemini(api_key: str, prompt: str, timeout: int = 20) -> str:
    timeout = min(int(timeout or FAST_GEMINI_TIMEOUT), FAST_GEMINI_TIMEOUT)
    if not api_key or len(api_key.strip()) < 8:
        raise ValueError("Gemini API key is empty")

    last_error = None

    for model in GEMINI_MODELS:
        try:
            response = requests.post(
                GEMINI_GENERATE_URL.format(model=model),
                headers={
                    "x-goog-api-key": api_key.strip(),
                    "Content-Type": "application/json",
                },
                json={
                    "contents": [
                        {
                            "parts": [
                                {"text": prompt}
                            ]
                        }
                    ]
                },
                timeout=timeout,
            )

            if response.status_code in (400, 401, 403):
                last_error = "Gemini API key is invalid, blocked, or the model is not available"
                continue
            if response.status_code == 429:
                raise RuntimeError("Gemini API rate limit exceeded")

            response.raise_for_status()
            data = response.json()
            text = _extract_text_from_generate_content(data)
            if text:
                return text

            last_error = "Gemini API returned an empty response"

        except Exception as e:
            last_error = str(e)

    raise RuntimeError(last_error or "Gemini API request failed")


def test_connection(api_key: str) -> tuple[bool, str]:
    try:
        text = _call_gemini(
            api_key,
            "Відповідай одним словом українською: працює",
            timeout=FAST_GEMINI_TIMEOUT,
        )
        return True, "Gemini API підключено успішно. Відповідь моделі: " + text[:80]
    except Exception as e:
        return False, f"Помилка Gemini API: {e}"


def _build_explanation_prompt(analysis: dict, language: str) -> str:
    lang = "українською" if language == "Українська" else "English"
    ally_recs = analysis.get("ally_recommendations") or analysis.get("recommendations", [])
    enemy_preds = analysis.get("enemy_predictions", [])
    recommendations = ", ".join(r["name"] for r in ally_recs)
    predicted = ", ".join(r["name"] for r in enemy_preds)
    return f"""
Ти — аналітик Dota 2. Поясни {lang} конкретний драфт.
Відповідь має бути коротка: 2-4 абзаци.

Важливо:
- Не додавай героїв у драфт автоматично.
- Якщо у команді менше 5 героїв, аналізуй тільки тих, хто реально є.
- Окремо поясни рекомендований пік для користувача.
- Окремо поясни, яких героїв може взяти суперник і чому.

Сторона користувача: {analysis.get('side')}
Герої команди користувача: {', '.join(analysis.get('team_heroes', [])) or 'не обрані'}
Герої команди суперника: {', '.join(analysis.get('enemy_heroes', [])) or 'не обрані'}
Рекомендований пік для користувача: {recommendations}
Ймовірний пік суперника: {predicted}
Сильні сторони: {', '.join(analysis.get('strengths', []))}
Слабкі сторони: {', '.join(analysis.get('weaknesses', []))}
Синергії: {json.dumps(analysis.get('synergies', []), ensure_ascii=False)}
Контрпіки: {json.dumps(analysis.get('counters', []), ensure_ascii=False)}
""".strip()

def _offline_explanation(analysis: dict) -> str:
    recs = analysis.get("recommendations") or []
    if not recs:
        return "ШІ-пояснення недоступне, але локальний аналіз виконано. Додайте героїв у драфт і повторіть аналіз."

    top = recs[0]
    others = ", ".join(r["name"] for r in recs[1:3]) or "інші герої з ТОП-5"
    strengths = analysis.get("strengths") or ["збалансований склад"]
    weaknesses = analysis.get("weaknesses") or ["потреба в координації"]
    return (
        f"Команда має {strengths[0].lower()}, але варто врахувати: {weaknesses[0].lower()}. "
        f"Локальний аналіз пропонує закрити слабкі місця героями з контролем, корисними ролями або високим win rate.\n\n"
        f"Найкращий варіант — {top['name']}: {top.get('explanation', '')} "
        f"Також можна розглянути {others}."
    )


def generate_explanation(api_key: str, analysis: dict, language: str = "Українська") -> tuple[str, bool]:
    """Returns: text, used_live_ai."""
    if api_key:
        try:
            return _call_gemini(api_key, _build_explanation_prompt(analysis, language)), True
        except Exception:
            pass
    return _offline_explanation(analysis), False


def _extract_json_object(text: str) -> dict:
    """Gemini can wrap JSON in markdown. This extracts the first JSON object."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object in Gemini response")
    return json.loads(text[start:end + 1])


def _fallback_missing_picks(team_heroes: list[str], enemy_heroes: list[str], missing_count: int) -> tuple[list[str], str]:
    recs = analysis_engine.recommend_heroes(team_heroes, enemy_heroes, top_n=max(10, missing_count + 3))
    taken = set(team_heroes) | set(enemy_heroes)
    picks = []
    for rec in recs:
        name = rec.get("name")
        if name and name not in taken and name not in picks:
            picks.append(name)
        if len(picks) >= missing_count:
            break
    reason = "Gemini недоступний, тому порожні місця заповнені локальним алгоритмом рекомендацій."
    return picks, reason



def _validate_recommendations(items, fallback):
    valid = _hero_names()
    result = []
    seen = set()
    for item in items or []:
        if isinstance(item, str):
            name = item.strip()
            role = "Unknown"
            score = 50.0
            explanation = "Рекомендовано AI для поточного драфту."
        elif isinstance(item, dict):
            name = str(item.get("name", "")).strip()
            role = str(item.get("role", "Unknown"))
            try:
                score = round(float(item.get("score", 50.0)), 1)
            except Exception:
                score = 50.0
            explanation = str(item.get("explanation", "Рекомендовано AI для поточного драфту."))
        else:
            continue
        if name in valid and name not in seen:
            seen.add(name)
            result.append({"name": name, "role": role, "score": score, "explanation": explanation})
        if len(result) >= 5:
            break
    for item in fallback or []:
        name = item.get("name")
        if name in valid and name not in seen:
            seen.add(name)
            result.append(item)
        if len(result) >= 5:
            break
    return result[:5]



def generate_match_assistant(api_key: str, analysis: dict, language: str = "Українська") -> tuple[dict, bool]:
    """Fast AI match assistant.

    The local analysis is rendered immediately if Gemini is missing/slow.
    Gemini receives only compact candidate lists instead of the whole hero database,
    so the analysis button works much faster.
    """
    fallback = {
        "ally_recommendations": analysis.get("ally_recommendations") or analysis.get("recommendations", []),
        "enemy_predictions": analysis.get("enemy_predictions", []),
        "strengths": analysis.get("strengths", []),
        "weaknesses": analysis.get("weaknesses", []),
        "strategy": analysis.get("strategy", []),
        "synergies": analysis.get("synergies", []),
        "counters": analysis.get("counters", []),
        "explanation": _offline_explanation(analysis),
    }

    if not api_key:
        return fallback, False

    lang = "українською" if language == "Українська" else "English"
    taken = set(analysis.get("team_heroes", [])) | set(analysis.get("enemy_heroes", []))

    # Short candidate list = much faster Gemini response.
    candidate_names = []
    for group_key in ("ally_recommendations", "recommendations", "enemy_predictions", "meta_recommendations"):
        for item in analysis.get(group_key, []) or []:
            name = item.get("name") if isinstance(item, dict) else str(item)
            if name and name not in taken and name not in candidate_names:
                candidate_names.append(name)
            if len(candidate_names) >= 35:
                break
        if len(candidate_names) >= 35:
            break

    # If the local engine returned too few candidates, fill from HEROES by winrate.
    if len(candidate_names) < 20:
        for h in sorted(HEROES, key=lambda x: x.get("win", 50), reverse=True):
            name = h.get("name")
            if name and name not in taken and name not in candidate_names:
                candidate_names.append(name)
            if len(candidate_names) >= 35:
                break

    prompt = f"""
Ти — Dota 2 Draft Assistant. Дай швидкий аналіз конкретного драфту.
Відповідай ЛИШЕ JSON без markdown. Мова: {lang}.

Моя команда: {analysis.get('team_heroes', [])}
Команда суперника: {analysis.get('enemy_heroes', [])}
Кандидати, з яких можна вибирати: {candidate_names}
Локальні рекомендації для мене: {fallback['ally_recommendations']}
Локальний прогноз ворога: {fallback['enemy_predictions']}

Поверни JSON:
{{
  "ally_recommendations": [
    {{"name": "Hero", "role": "Role", "score": 55.5, "explanation": "коротко чому хороший пік"}}
  ],
  "enemy_predictions": [
    {{"name": "Hero", "role": "Role", "score": 55.5, "explanation": "прогноз, не реальний герой у драфті"}}
  ],
  "strengths": ["коротко"],
  "weaknesses": ["коротко"],
  "strategy": ["коротко"],
  "synergies": [{{"pair": ["Hero1", "Hero2"], "desc": "коротко"}}],
  "counters": [{{"hero": "EnemyHero", "desc": "коротко"}}],
  "explanation": "1-2 короткі абзаци"
}}

Правила:
- ally_recommendations = 5 героїв.
- enemy_predictions = 5 героїв.
- Не повторюй героїв, які вже є у драфті.
- Не додавай прогнозованих героїв у реальний список команд.
""".strip()

    try:
        raw = _call_gemini(api_key, prompt, timeout=FAST_GEMINI_TIMEOUT)
        parsed = _extract_json_object(raw)
        result = dict(fallback)
        result.update({k: v for k, v in parsed.items() if v})
        result["ally_recommendations"] = _validate_recommendations(
            result.get("ally_recommendations"),
            fallback["ally_recommendations"],
        )
        result["enemy_predictions"] = _validate_recommendations(
            result.get("enemy_predictions"),
            fallback["enemy_predictions"],
        )
        if not result.get("explanation"):
            result["explanation"] = fallback["explanation"]
        return result, True
    except Exception:
        return fallback, False

def suggest_missing_picks(
    api_key: str,
    team_heroes: list[str],
    enemy_heroes: list[str],
    missing_count: int,
    language: str = "Українська",
) -> tuple[list[str], str, bool]:
    """
    Suggests heroes for empty allied slots.

    Returns: picks, reason, used_live_ai
    """
    missing_count = max(0, min(5, int(missing_count)))
    if missing_count <= 0:
        return [], "У команді вже 5 героїв, автодоповнення не потрібне.", False

    taken = set(team_heroes) | set(enemy_heroes)
    local_recs = analysis_engine.recommend_heroes(team_heroes, enemy_heroes, top_n=20)
    allowed = [r["name"] for r in local_recs if r.get("name") not in taken]

    if len(allowed) < missing_count:
        valid = _hero_names()
        allowed += [h["name"] for h in HEROES if h["name"] in valid and h["name"] not in taken and h["name"] not in allowed]

    allowed = allowed[:30]

    if not api_key:
        picks, reason = _fallback_missing_picks(team_heroes, enemy_heroes, missing_count)
        return picks, reason, False

    lang = "українською" if language == "Українська" else "English"
    prompt = f"""
Ти — Dota 2 draft assistant. Треба заповнити порожні місця у команді користувача.
Відповідай ЛИШЕ JSON без markdown.

Мова пояснення: {lang}
Уже вибрані герої команди користувача: {team_heroes}
Герої суперника: {enemy_heroes}
Скільки героїв потрібно додати: {missing_count}
Можна вибирати ТІЛЬКИ з цього списку дозволених героїв: {allowed}

Правила:
- Не повторюй героїв, які вже є у будь-якій команді.
- Не вигадуй героїв поза дозволеним списком.
- Обери героїв, які закривають слабкі місця драфту, дають синергію або контрять суперника.

Формат відповіді:
{{
  "picks": ["Hero 1", "Hero 2"],
  "reason": "коротке пояснення"
}}
""".strip()

    try:
        text = _call_gemini(api_key, prompt, timeout=FAST_GEMINI_TIMEOUT)
        data = _extract_json_object(text)
        picks = _normalize_list(data.get("picks", []))
        picks = [p for p in picks if p not in taken][:missing_count]
        reason = str(data.get("reason", "Герої додані на основі AI-аналізу драфту.")).strip()

        if len(picks) < missing_count:
            fallback, fallback_reason = _fallback_missing_picks(team_heroes + picks, enemy_heroes, missing_count - len(picks))
            picks += [p for p in fallback if p not in picks]
            if not reason:
                reason = fallback_reason

        return picks[:missing_count], reason, True

    except Exception:
        picks, reason = _fallback_missing_picks(team_heroes, enemy_heroes, missing_count)
        return picks, reason, False
