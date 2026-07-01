"""
Gemini integration: sends draft-analysis results to the Gemini API and
returns a natural-language explanation of the recommendation.

Uses the public Generative Language REST endpoint. If no API key is
configured or the request fails (offline sandbox), falls back to a
locally-generated explanation built from the same analysis data so the
"Пояснення від ШІ" panel is always populated.
"""
import requests
import json

GEMINI_URL_TMPL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3-pro:generateContent?key={key}"
)


def _build_prompt(analysis: dict, language: str) -> str:
    return f"""
Ти — аналітик Dota 2. Поясни користувачу {('українською' if language == 'Українська' else 'English')}
чому рекомендовано саме цих героїв, спираючись на дані нижче. Будь стислим
(2-3 абзаци), згадай контрпіки, синергії та сильні/слабкі сторони команди.

Команда гравця: {', '.join(analysis['team_heroes'])}
Команда суперника: {', '.join(analysis['enemy_heroes'])}
ТОП-5 рекомендацій: {', '.join(r['name'] for r in analysis['recommendations'])}
Сильні сторони: {', '.join(analysis['strengths'])}
Слабкі сторони: {', '.join(analysis['weaknesses'])}
""".strip()


def _offline_explanation(analysis: dict) -> str:
    top = analysis["recommendations"][0]
    others = ", ".join(r["name"] for r in analysis["recommendations"][1:3])
    enemy_threats = ", ".join(analysis["weaknesses"][:2]) if analysis["weaknesses"] else "опір ворожого складу"
    return (
        f"Ваша команда має {analysis['strengths'][0].lower() if analysis['strengths'] else 'непогану базу'} "
        f"та витримує більшість сутичок, але варто враховувати {enemy_threats.lower()}. "
        f"Найкращі варіанти — герої з контролем або ті, хто здатен закрити прогалини у складі.\n\n"
        f"{top['name']} є найкращим вибором: він добре протистоїть ворожому драфту "
        f"і додатково підсилює командну гру завдяки своїй ролі ({top['role']}).\n\n"
        f"Альтернативи: {others} також добре впишуться у поточний склад."
    )


def generate_explanation(api_key: str, analysis: dict, language: str = "Українська"):
    """Returns (text, used_live: bool)"""
    if api_key:
        try:
            prompt = _build_prompt(analysis, language)
            resp = requests.post(
                GEMINI_URL_TMPL.format(key=api_key),
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return text.strip(), True
        except (requests.RequestException, KeyError, IndexError, json.JSONDecodeError):
            pass
    return _offline_explanation(analysis), False
