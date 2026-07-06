from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QScrollArea
from PyQt6.QtCore import Qt

from ui.widgets import make_card, card_title, small_label, body_label

TECH = [
    ("🐍", "Python\n3.12"), ("🅀", "PyQt6"), ("👁", "OpenCV"), ("🖼", "Pillow"), ("🔢", "NumPy"),
    ("🖱", "PyAutoGUI"), ("🗄", "SQLite"), ("🌐", "STRATZ API"), ("✨", "Gemini\n3 Pro"), ("🌿", "Git"), ("🐙", "GitHub"),
]

FEATURES = [
    "Завантаження та автоматичне створення скриншотів",
    "Розпізнавання героїв із використанням комп'ютерного зору",
    "Аналіз контрпіків та синергій між героями",
    "Врахування актуальної мети гри та статистики STRATZ API",
    "Формування ТОП-5 рекомендованих героїв",
    "Пояснення рекомендацій за допомогою ШІ",
    "Збереження та перегляд історії аналізів",
]

AUTHORS = ["Горячев Владислав", "Коваляк Ярослав", "Подпорінов Іван"]


class AboutPage(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(14)

        title = QLabel("ℹ  Про програму")
        title.setStyleSheet("font-size:20px; font-weight:700; color:#fff; border:none; background:transparent;")
        outer.addWidget(title)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(16)

        # Hero card
        hero_card = make_card()
        hero_lay = QVBoxLayout(hero_card)
        hero_lay.setContentsMargins(20, 18, 20, 18)
        hname = QLabel("Інтелектуальний помічник для аналізу драфту\nта рекомендації героя в Dota 2")
        hname.setStyleSheet("color:#fff; font-size:18px; font-weight:800; border:none; background:transparent;")
        hero_lay.addWidget(hname)
        desc = body_label(
            "Програма автоматично розпізнає героїв зі скриншота, аналізує склад команд, "
            "враховує контрпіки, синергії та статистику STRATZ API, після чого рекомендує "
            "найкращих героїв для вибору й пояснює свої рекомендації за допомогою штучного інтелекту.",
            size=13)
        hero_lay.addWidget(desc)
        lay.addWidget(hero_card)

        row = QHBoxLayout(); row.setSpacing(16)
        row.addWidget(self._features_card(), 1)
        row.addWidget(self._tech_card(), 1)
        lay.addLayout(row)

        row2 = QHBoxLayout(); row2.setSpacing(16)
        row2.addWidget(self._authors_card(), 1)
        row2.addWidget(self._version_card(), 1)
        lay.addLayout(row2)

        lay.addStretch()
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _features_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(8)
        lay.addWidget(card_title("Основні можливості", "★"))
        for f in FEATURES:
            row = QHBoxLayout()
            check = QLabel("✓")
            check.setStyleSheet("color:#5ee08a; font-weight:800; border:none; background:transparent;")
            row.addWidget(check)
            row.addWidget(body_label(f, size=12))
            lay.addLayout(row)
        return card

    def _tech_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(10)
        lay.addWidget(card_title("Використані технології", "</>"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        for i, (icon, label) in enumerate(TECH):
            tile = make_card()
            tile.setStyleSheet("QFrame { background-color:#0f1220; border:1px solid #1f2436; border-radius:10px; }")
            tl = QVBoxLayout(tile)
            tl.setContentsMargins(10, 10, 10, 10)
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size:22px; border:none; background:transparent;")
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            tl.addWidget(icon_lbl)
            text_lbl = QLabel(label)
            text_lbl.setStyleSheet("font-size:10px; color:#c4c7d6; font-weight:600; border:none; background:transparent;")
            text_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            tl.addWidget(text_lbl)
            grid.addWidget(tile, i // 5, i % 5)
        lay.addLayout(grid)
        return card

    def _authors_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(8)
        lay.addWidget(card_title("Автори", "👥"))
        for a in AUTHORS:
            row = QHBoxLayout()
            icon = QLabel("👤")
            icon.setStyleSheet("border:none; background:transparent;")
            row.addWidget(icon)
            row.addWidget(body_label(a, size=12))
            lay.addLayout(row)
        lay.addWidget(self._hline())
        group_row = QHBoxLayout()
        group_row.addWidget(QLabel("✉"))
        group_row.addWidget(body_label("Група", size=12))
        lay.addLayout(group_row)
        gv_row = QHBoxLayout()
        gv_row.addWidget(QLabel("👤"))
        gv_row.addWidget(body_label("ІПЗ-240086", size=12))
        lay.addLayout(gv_row)
        return card

    def _version_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(10)
        lay.addWidget(card_title("Версія", "ⓘ"))
        for k, v in [("Версія програми:", "1.0.0"), ("Дата збірки:", "29.06.2026")]:
            row = QHBoxLayout()
            row.addWidget(small_label(k))
            row.addStretch()
            vl = QLabel(v)
            vl.setStyleSheet("color:#e7e9f3; font-weight:700; font-size:12px; border:none; background:transparent;")
            row.addWidget(vl)
            lay.addLayout(row)
        lay.addWidget(self._hline())
        copyright_lbl = small_label("© 2026 Всі права захищені")
        lay.addWidget(copyright_lbl)
        lay.addStretch()
        return card

    def _hline(self):
        from PyQt6.QtWidgets import QFrame
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background-color:#1f2436; border:none;")
        return line
