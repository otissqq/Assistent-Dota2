import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QScrollArea, QFrame
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPainterPath

from ui.widgets import make_card, card_title, small_label, body_label, load_pixmap, icon_pixmap, page_title
from ui import theme
from services import i18n

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _logo_pixmap(filename, size=56, radius=16):
    src = load_pixmap(os.path.join(ASSETS_DIR, filename))
    if src.isNull():
        return None
    scaled = src.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                         Qt.TransformationMode.SmoothTransformation)
    x = max(0, (scaled.width() - size) // 2)
    y = max(0, (scaled.height() - size) // 2)
    cropped = scaled.copy(x, y, size, size)
    from PyQt6.QtGui import QPixmap
    out = QPixmap(size, size)
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
    p.setClipPath(path)
    p.drawPixmap(0, 0, cropped)
    p.end()
    return out

# Each technology tile shows a real logo asset instead of an emoji glyph.
TECH = [
    ("python_logo.png", "Python 3.12"),
    ("pyqt6.png", "PyQt6"),
    ("opencv.jpg", "OpenCV"),
    ("pillow.jpg", "Pillow"),
    ("numpy.jpg", "NumPy"),
    ("python_logo.png", "PyAutoGUI"),
    ("sqlite.webp", "SQLite"),
    ("stratz_logo.png", "STRATZ API"),
    ("gemini_logo.webp", "Gemini 3 Pro"),
    ("git_logo.webp", "Git"),
    ("github_logo.png", "GitHub"),
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
        self.t = theme.current()
        self._build_ui()

    def _build_ui(self):
        t = self.t
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(18)

        outer.addWidget(page_title(i18n.t("about_title"), "info_icon.webp", "ℹ"))

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(16)

        # Hero card
        hero_card = make_card()
        hero_lay = QHBoxLayout(hero_card)
        hero_lay.setContentsMargins(22, 20, 22, 20)
        hero_lay.setSpacing(18)

        badge = QLabel()
        badge.setFixedSize(56, 56)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_pix = _logo_pixmap("dota_logo.jpg", size=56, radius=16)
        if logo_pix is not None:
            badge.setPixmap(logo_pix)
        else:
            badge.setText("🛡")
            badge.setStyleSheet(f"background:{t['accent']}; border-radius:16px; font-size:26px;")
        hero_lay.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)

        hero_text = QVBoxLayout(); hero_text.setSpacing(6)
        hname = QLabel("Інтелектуальний помічник для аналізу драфту\nта рекомендації героя в Dota 2")
        hname.setStyleSheet(f"color:{t['text_bright']}; font-size:17px; font-weight:800; border:none; background:transparent;")
        hero_text.addWidget(hname)
        desc = body_label(
            "Програма автоматично розпізнає героїв зі скриншота, аналізує склад команд, "
            "враховує контрпіки, синергії та статистику STRATZ API, після чого рекомендує "
            "найкращих героїв для вибору й пояснює свої рекомендації за допомогою штучного інтелекту.",
            size=13)
        hero_text.addWidget(desc)
        hero_lay.addLayout(hero_text, 1)
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

    def _list_row(self, icon, text, icon_color=None):
        t = self.t
        row = QFrame()
        row.setStyleSheet(f"QFrame {{ background:{t['surface_alt']}; border-radius:8px; }}")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(10, 8, 10, 8)
        rl.setSpacing(10)
        ic = QLabel(icon)
        ic.setFixedWidth(18)
        ic.setStyleSheet(f"color:{icon_color or t['green']}; font-weight:800; border:none; background:transparent;")
        rl.addWidget(ic)
        rl.addWidget(body_label(text, size=12), 1)
        return row

    def _features_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(8)
        lay.addWidget(card_title("Основні можливості", "★"))
        for f in FEATURES:
            lay.addWidget(self._list_row("✓", f))
        return card

    def _tech_card(self):
        t = self.t
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)
        lay.addWidget(card_title("Використані технології", "⚙"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        for i, (icon_file, label) in enumerate(TECH):
            tile = QFrame()
            tile.setFixedSize(90, 84)
            tile.setStyleSheet(
                f"QFrame {{ background-color:{t['surface_alt']}; border:1px solid {t['border_soft']}; border-radius:10px; }}"
                f"QFrame:hover {{ border:1px solid {t['accent']}; }}"
            )
            tl = QVBoxLayout(tile)
            tl.setContentsMargins(6, 10, 6, 8)
            tl.setSpacing(6)
            icon_lbl = QLabel()
            icon_lbl.setFixedSize(28, 28)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pix = icon_pixmap(icon_file, size=28, radius=6)
            if not pix.isNull():
                icon_lbl.setPixmap(pix)
                icon_lbl.setStyleSheet("background:transparent; border:none;")
            else:
                icon_lbl.setText("❔")
                icon_lbl.setStyleSheet("font-size:18px; border:none; background:transparent;")
            tl.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignHCenter)
            text_lbl = QLabel(label)
            text_lbl.setWordWrap(True)
            text_lbl.setStyleSheet(f"font-size:9px; color:{t['text_dim']}; font-weight:600; border:none; background:transparent;")
            text_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            tl.addWidget(text_lbl)
            grid.addWidget(tile, i // 5, i % 5)
        lay.addLayout(grid)
        return card

    def _authors_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(8)
        lay.addWidget(card_title("Автори", "👥"))
        for a in AUTHORS:
            lay.addWidget(self._list_row("👤", a, icon_color=self.t["accent_soft"]))
        lay.addWidget(self._hline())
        lay.addWidget(self._list_row("✉", "Група", icon_color=self.t["text_faint"]))
        lay.addWidget(self._list_row("🎓", "ІПЗ-240086", icon_color=self.t["text_faint"]))
        return card

    def _version_card(self):
        t = self.t
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)
        lay.addWidget(card_title("Версія", "ⓘ"))
        for k, v in [("Версія програми:", "1.0.0"), ("Дата збірки:", "29.06.2026")]:
            row = QHBoxLayout()
            row.addWidget(small_label(k))
            row.addStretch()
            vl = QLabel(v)
            vl.setStyleSheet(f"color:{t['text_bright']}; font-weight:700; font-size:12px; border:none; background:transparent;")
            row.addWidget(vl)
            lay.addLayout(row)
        lay.addWidget(self._hline())
        copyright_lbl = small_label("© 2026 Всі права захищені")
        lay.addWidget(copyright_lbl)
        lay.addStretch()
        return card

    def _hline(self):
        line = QFrame(); line.setFixedHeight(1)
        line.setStyleSheet(f"background-color:{self.t['border_soft']}; border:none;")
        return line
