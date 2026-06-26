import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from config.settings import GEMINI_API_KEY

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

class GeminiAnalyzer:
    def __init__(self, model_name="gemini-1.5-flash"):
        self.api_key = GEMINI_API_KEY
        self.model_name = model_name
        self.model = None
        if GENAI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model_name)

    def generate_analysis(self, radiant_heroes, dire_heroes, radiant_strength, dire_strength, recommendations, lang="uk"):
        if not self.model:
            return self._fallback_analysis(radiant_heroes, dire_heroes, radiant_strength, dire_strength, recommendations, lang)

        prompt = self._build_prompt(radiant_heroes, dire_heroes, radiant_strength, dire_strength, recommendations, lang)
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return self._fallback_analysis(radiant_heroes, dire_heroes, radiant_strength, dire_strength, recommendations, lang) + f"\n[AI Error: {str(e)}]"

    def _build_prompt(self, radiant, dire, r_str, d_str, recs, lang):
        rec_text = "\n".join([f"{i+1}. {r['name']} (score: {r['score']:.1f}%)" for i, r in enumerate(recs[:5])])
        if lang == "uk":
            return f"""Ти — експерт з Dota 2 (патч 7.41d). Проаналізуй драфт та дай детальні рекомендації.

Команда Radiant: {', '.join(radiant)}
Сила Radiant: {r_str:.1f}%

Команда Dire: {', '.join(dire)}
Сила Dire: {d_str:.1f}%

Рекомендовані контрпіки для Dire:
{rec_text}

Опиши:
1. Сильні сторони кожної команди
2. Слабкі сторони кожної команди
3. Як Radiant може виграти гру
4. Ключові предмети та стратегії
5. Прогноз на тривалість гри та шанси на перемогу

Відповідай українською мовою, структуровано."""
        elif lang == "ru":
            return f"""Ты — эксперт по Dota 2 (патч 7.41d). Проанализируй драфт и дай детальные рекомендации.

Команда Radiant: {', '.join(radiant)}
Сила Radiant: {r_str:.1f}%

Команда Dire: {', '.join(dire)}
Сила Dire: {d_str:.1f}%

Рекомендуемые контрпики для Dire:
{rec_text}

Опиши:
1. Сильные стороны каждой команды
2. Слабые стороны каждой команды
3. Как Radiant может выиграть игру
4. Ключевые предметы и стратегии
5. Прогноз на длительность игры и шансы на победу

Отвечай на русском языке, структурированно."""
        else:
            return f"""You are a Dota 2 expert (patch 7.41d). Analyze the draft and provide detailed recommendations.

Radiant team: {', '.join(radiant)}
Radiant strength: {r_str:.1f}%

Dire team: {', '.join(dire)}
Dire strength: {d_str:.1f}%

Recommended counters for Dire:
{rec_text}

Describe:
1. Strong sides of each team
2. Weak sides of each team
3. How Radiant can win the game
4. Key items and strategies
5. Game duration prediction and win chance

Answer in English, structured."""

    def _fallback_analysis(self, radiant, dire, r_str, d_str, recs, lang):
        if lang == "uk":
            return f"""AI Аналіз (офлайн режим)

Сильні сторони Radiant:
- Командна сила: {r_str:.1f}%
- Добре збалансований склад

Сильні сторони Dire:
- Командна сила: {d_str:.1f}%
- Потенціал для камбеку

Слабкі сторони Radiant:
- Залежність від ранньої гри

Слабкі сторони Dire:
- Мало контролю

Ітог: Radiant має {'перевагу' if r_str > d_str else 'невелику перевагу'} завдяки кращому драфту.

Рекомендації: {', '.join([r['name'] for r in recs[:3]])}"""
        elif lang == "ru":
            return f"""AI Анализ (офлайн режим)

Сильные стороны Radiant:
- Командная сила: {r_str:.1f}%
- Хорошо сбалансированный состав

Сильные стороны Dire:
- Командная сила: {d_str:.1f}%
- Потенциал для камбека

Слабые стороны Radiant:
- Зависимость от ранней игры

Слабые стороны Dire:
- Мало контроля

Итог: Radiant имеет {'преимущество' if r_str > d_str else 'незначительное преимущество'}.

Рекомендации: {', '.join([r['name'] for r in recs[:3]])}"""
        else:
            return f"""AI Analysis (offline mode)

Radiant strengths: {r_str:.1f}%
Dire strengths: {d_str:.1f}%

Recommended: {', '.join([r['name'] for r in recs[:3]])}"""
