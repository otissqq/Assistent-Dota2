import os
from PyQt6.QtWidgets import (QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
                              QPushButton, QCheckBox, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QPolygonF
from PyQt6.QtCore import Qt, QPointF
import math

HERO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "heroes")


def hero_pixmap(name, size=64):
    path = os.path.join(HERO_DIR, f"{name}.png")
    pix = QPixmap(path) if os.path.exists(path) else QPixmap()
    if pix.isNull():
        pix = QPixmap(size, size)
        pix.fill(QColor("#2a2f45"))
    return pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                       Qt.TransformationMode.SmoothTransformation)


def round_pixmap(pix: QPixmap, radius=10):
    out = QPixmap(pix.size())
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    path_rect = out.rect()
    from PyQt6.QtGui import QPainterPath
    path = QPainterPath()
    path.addRoundedRect(0, 0, pix.width(), pix.height(), radius, radius)
    p.setClipPath(path)
    p.drawPixmap(0, 0, pix)
    p.end()
    return out


class Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setStyleSheet("")  # uses .card from qss via dynamic property below
        self.setObjectName("")
        self._apply_card_style()

    def _apply_card_style(self):
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            Card {
                background-color: #131625;
                border: 1px solid #1f2436;
                border-radius: 12px;
            }
        """)


def make_card():
    f = QFrame()
    f.setStyleSheet("""
        QFrame {
            background-color: #131625;
            border: 1px solid #1f2436;
            border-radius: 12px;
        }
    """)
    return f


def card_title(text, icon=""):
    lbl = QLabel(f"{icon}  {text}" if icon else text)
    lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff; border: none; background: transparent;")
    return lbl


def small_label(text, color="#7c8096"):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 11px; color: {color}; border: none; background: transparent;")
    return lbl


def body_label(text, color="#c4c7d6", size=13, weight=400):
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(f"font-size: {size}px; color: {color}; font-weight: {weight}; border: none; background: transparent;")
    return lbl


def pill(text, bg="#221c44", fg="#a99bf5"):
    lbl = QLabel(text)
    lbl.setStyleSheet(f"""
        background-color: {bg};
        color: {fg};
        font-size: 11px;
        font-weight: 600;
        border-radius: 6px;
        padding: 3px 9px;
        border: none;
    """)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


class HeroChip(QWidget):
    """Vertical hero portrait + name, used in 'Розпізнані герої' rows."""
    def __init__(self, name, size=64, clickable=False, on_click=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        img_lbl = QLabel()
        img_lbl.setFixedSize(size, size)
        img_lbl.setPixmap(round_pixmap(hero_pixmap(name, size), 10))
        img_lbl.setStyleSheet("border: 1px solid #262b40; border-radius: 10px;")
        layout.addWidget(img_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 11px; color: #c4c7d6; border: none; background: transparent;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(name_lbl)
        if clickable and on_click:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.mousePressEvent = lambda e: on_click(name)


class ToggleRow(QWidget):
    def __init__(self, title, subtitle, checked=False, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        t = QLabel(title)
        t.setStyleSheet("font-size: 13px; color: #e7e9f3; font-weight: 600; border:none; background:transparent;")
        s = QLabel(subtitle)
        s.setStyleSheet("font-size: 11px; color: #7c8096; border:none; background:transparent;")
        text_box.addWidget(t)
        text_box.addWidget(s)
        layout.addLayout(text_box)
        layout.addStretch()
        self.checkbox = QCheckBox()
        self.checkbox.setProperty("class", "toggle")
        self.checkbox.setChecked(checked)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator { width: 40px; height: 22px; border-radius: 11px; background-color: #2a2f45; }
            QCheckBox::indicator:checked { background-color: #6c5ce7; }
        """)
        layout.addWidget(self.checkbox)


class RadarChart(QWidget):
    def __init__(self, axes, team_vals, enemy_vals, parent=None):
        super().__init__(parent)
        self.axes = axes
        self.team_vals = team_vals
        self.enemy_vals = enemy_vals
        self.setMinimumSize(280, 260)

    def set_data(self, axes, team_vals, enemy_vals):
        self.axes, self.team_vals, self.enemy_vals = axes, team_vals, enemy_vals
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2 - 6
        radius = min(w, h) / 2 - 36
        n = len(self.axes)

        def point(i, val, maxv=100):
            angle = -math.pi / 2 + i * 2 * math.pi / n
            r = radius * (val / maxv)
            return QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle))

        # rings
        for frac in (0.25, 0.5, 0.75, 1.0):
            poly = QPolygonF([point(i, 100 * frac) for i in range(n)])
            p.setPen(QPen(QColor("#232739"), 1))
            p.drawPolygon(poly)

        # axis lines + labels
        p.setFont(QFont("Segoe UI", 8))
        for i, label in enumerate(self.axes):
            edge = point(i, 100)
            p.setPen(QPen(QColor("#232739"), 1))
            p.drawLine(QPointF(cx, cy), edge)
            angle = -math.pi / 2 + i * 2 * math.pi / n
            lx = cx + (radius + 20) * math.cos(angle)
            ly = cy + (radius + 20) * math.sin(angle)
            p.setPen(QColor("#7c8096"))
            rect_w, rect_h = 70, 16
            p.drawText(int(lx - rect_w / 2), int(ly - rect_h / 2), rect_w, rect_h,
                       Qt.AlignmentFlag.AlignCenter, label)

        # enemy polygon (red)
        enemy_poly = QPolygonF([point(i, v) for i, v in enumerate(self.enemy_vals)])
        p.setPen(QPen(QColor("#ef6f7a"), 2))
        p.setBrush(QColor(239, 111, 122, 40))
        p.drawPolygon(enemy_poly)

        # team polygon (green)
        team_poly = QPolygonF([point(i, v) for i, v in enumerate(self.team_vals)])
        p.setPen(QPen(QColor("#5ee08a"), 2))
        p.setBrush(QColor(94, 224, 138, 40))
        p.drawPolygon(team_poly)

        p.end()
