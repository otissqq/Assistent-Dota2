"""
Local hero dataset used as a cached fallback for the STRATZ API and as the
source pool for the demo draft / hero-recognition simulation.

In production, populate_from_stratz() in services/stratz_service.py
overwrites HEROES with live data fetched from the real STRATZ API once a
valid API key is provided in Settings.
"""

ATTR_COLORS = {
    "Strength": "#e05c5c",
    "Agility": "#5cc270",
    "Intelligence": "#5c8ce0",
    "Universal": "#b15ce0",
}

HEROES = [
    {"id": 1, "name": "Abaddon", "attr": "Strength", "role": "Support", "tag": "Durable",
     "win": 52.1, "pick": 17.8, "ban": 7.2, "desc": "Витривалий підтримка, який захищає союзників та допомагає їм виживати в складних ситуаціях.",
     "difficulty": 2, "attack": "Ближній бій"},
    {"id": 2, "name": "Alchemist", "attr": "Strength", "role": "Carry", "tag": "Pusher",
     "win": 51.3, "pick": 18.6, "ban": 9.1, "desc": "Жадібний керрі, що швидко накопичує золото та тиснить на будівлі.",
     "difficulty": 2, "attack": "Ближній бій"},
    {"id": 3, "name": "Ancient Apparition", "attr": "Intelligence", "role": "Support", "tag": "Disabler",
     "win": 50.4, "pick": 12.3, "ban": 4.3, "desc": "Холодний маг, що карає ворогів за відновлення здоров'я.",
     "difficulty": 3, "attack": "Дальній бій"},
    {"id": 4, "name": "Anti-Mage", "attr": "Agility", "role": "Carry", "tag": "Escape",
     "win": 49.7, "pick": 17.1, "ban": 8.5, "desc": "Спритний мисливець на магів зі здатністю до миттєвих переміщень.",
     "difficulty": 2, "attack": "Ближній бій"},
    {"id": 5, "name": "Arc Warden", "attr": "Agility", "role": "Carry", "tag": "Pusher",
     "win": 52.6, "pick": 8.4, "ban": 15.2, "desc": "Створює власну копію, подвоюючи тиск на карті.",
     "difficulty": 4, "attack": "Дальній бій"},
    {"id": 6, "name": "Axe", "attr": "Strength", "role": "Initiator", "tag": "Durable",
     "win": 51.0, "pick": 20.4, "ban": 10.3, "desc": "Безстрашний берсерк, що затягує ворогів у ближній бій.",
     "difficulty": 1, "attack": "Ближній бій"},
    {"id": 7, "name": "Bane", "attr": "Intelligence", "role": "Support", "tag": "Disabler",
     "win": 50.6, "pick": 6.9, "ban": 2.6, "desc": "Кошмарний дух, що позбавляє ворогів контролю над власним розумом.",
     "difficulty": 3, "attack": "Дальній бій"},
    {"id": 8, "name": "Batrider", "attr": "Universal", "role": "Initiator", "tag": "Disabler",
     "win": 50.2, "pick": 9.2, "ban": 3.7, "desc": "Підпалює і затягує ворогів, добре заходить у будь-який склад.",
     "difficulty": 3, "attack": "Дальній бій"},
    {"id": 9, "name": "Primal Beast", "attr": "Strength", "role": "Offlane", "tag": "Initiator",
     "win": 53.0, "pick": 14.1, "ban": 6.0, "desc": "Грубий ініціатор з потужним контролем та стрибком у бій.",
     "difficulty": 2, "attack": "Ближній бій"},
    {"id": 10, "name": "Lion", "attr": "Intelligence", "role": "Support", "tag": "Disabler",
     "win": 51.8, "pick": 16.0, "ban": 5.4, "desc": "Класичний дизейблер з фінішером, що добре працює проти лейт-керрі.",
     "difficulty": 1, "attack": "Дальній бій"},
    {"id": 11, "name": "Spirit Breaker", "attr": "Strength", "role": "Offlane", "tag": "Ganker",
     "win": 50.9, "pick": 11.3, "ban": 4.9, "desc": "Заряджається через всю карту, щоб приголомшити одну ціль.",
     "difficulty": 1, "attack": "Ближній бій"},
    {"id": 12, "name": "Earth Spirit", "attr": "Strength", "role": "Support", "tag": "Disabler",
     "win": 50.1, "pick": 10.0, "ban": 4.1, "desc": "Маневрений дух каменю з потужними сейвами та контролем.",
     "difficulty": 4, "attack": "Ближній бій"},
    {"id": 13, "name": "Pangolier", "attr": "Strength", "role": "Offlane", "tag": "Initiator",
     "win": 51.4, "pick": 13.2, "ban": 6.8, "desc": "Швидкий ініціатор, що крутиться в гущі бою і відкидає зайвий урон.",
     "difficulty": 4, "attack": "Ближній бій"},
    {"id": 14, "name": "Lina", "attr": "Intelligence", "role": "Mid", "tag": "Nuker",
     "win": 52.4, "pick": 19.5, "ban": 7.0, "desc": "Вогняна чарівниця з вибуховим бурстом урону на дальній дистанції.",
     "difficulty": 2, "attack": "Дальній бій"},
    {"id": 15, "name": "Magnus", "attr": "Strength", "role": "Offlane", "tag": "Initiator",
     "win": 51.6, "pick": 12.7, "ban": 5.5, "desc": "Силовий ініціатор, що групує ворогів і підсилює союзників.",
     "difficulty": 2, "attack": "Ближній бій"},
    {"id": 16, "name": "Phoenix", "attr": "Universal", "role": "Support", "tag": "Durable",
     "win": 50.8, "pick": 9.8, "ban": 4.0, "desc": "Космічна сутність із сейвом для всієї команди та глобальною мобільністю.",
     "difficulty": 3, "attack": "Дальній бій"},
    {"id": 17, "name": "Crystal Maiden", "attr": "Intelligence", "role": "Support", "tag": "Disabler",
     "win": 51.1, "pick": 14.4, "ban": 3.2, "desc": "Льодяна чарівниця, що сповільнює ворогів і живить команду маною.",
     "difficulty": 1, "attack": "Дальній бій"},
    {"id": 18, "name": "Timbersaw", "attr": "Strength", "role": "Offlane", "tag": "Durable",
     "win": 51.9, "pick": 8.1, "ban": 4.4, "desc": "Лісоруб, що карає героїв сили і важко вбивається в лісі.",
     "difficulty": 3, "attack": "Ближній бій"},
    {"id": 19, "name": "Tinker", "attr": "Intelligence", "role": "Mid", "tag": "Pusher",
     "win": 53.5, "pick": 7.4, "ban": 11.0, "desc": "Технічний маг, що засипає карту ракетами і швидко відновлює здібності.",
     "difficulty": 4, "attack": "Дальній бій"},
    {"id": 20, "name": "Dark Willow", "attr": "Intelligence", "role": "Support", "tag": "Disabler",
     "win": 50.3, "pick": 10.6, "ban": 3.9, "desc": "Зловісна фея з ілюзіями та потужним контролем на дистанції.",
     "difficulty": 3, "attack": "Дальній бій"},
    {"id": 21, "name": "Tidehunter", "attr": "Strength", "role": "Offlane", "tag": "Initiator",
     "win": 52.2, "pick": 9.0, "ban": 5.1, "desc": "Морський тиран з ультою для масового контролю команди.",
     "difficulty": 1, "attack": "Ближній бій"},
]

SYNERGIES = {
    ("Pangolier", "Magnus"): "Відмінна ініціація",
    ("Phoenix", "Lina"): "Сильний магічний урон по площі",
    ("Magnus", "Crystal Maiden"): "Контроль та підтримка",
}

COUNTERS = {
    "Tinker": "Сильний у лейті",
    "Tidehunter": "Контрить ініціацію",
    "Batrider": "Мобільність та виживання",
}

HERO_BY_NAME = {h["name"]: h for h in HEROES}
