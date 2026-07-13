import os
from PyQt6.QtWidgets import (QFrame, QLabel, QVBoxLayout, QHBoxLayout, QWidget,
                              QPushButton, QCheckBox, QGraphicsDropShadowEffect, QSizePolicy)
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QPolygonF
from PyQt6.QtCore import (Qt, QPointF, QPropertyAnimation, QEasingCurve,
                           pyqtProperty, pyqtSignal)
import math

from ui import theme

HERO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "heroes")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _section_icon_pixmap(filename, size=20, radius=6):
    """Loads an assets/ image, centre-crops it to a size x size square and
    rounds its corners -- used for card_title()'s icon when a real image
    filename is passed instead of an emoji glyph."""
    return icon_pixmap(filename, size=size, radius=radius)


def icon_pixmap(filename, size=20, radius=6):
    """Loads an assets/ image (by filename, relative to assets/), centre-
    crops it to a size x size square and rounds its corners. Shared helper
    used anywhere a real logo/icon image should replace an emoji glyph
    (card titles, technology tiles, settings section icons, ...)."""
    from PyQt6.QtGui import QPainterPath
    from PyQt6.QtCore import QRectF
    path = os.path.join(ASSETS_DIR, filename)
    src = load_pixmap(path)
    if src.isNull():
        return QPixmap()
    scaled = src.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                         Qt.TransformationMode.SmoothTransformation)
    x = max(0, (scaled.width() - size) // 2)
    y = max(0, (scaled.height() - size) // 2)
    cropped = scaled.copy(x, y, size, size)
    out = QPixmap(size, size)
    out.fill(Qt.GlobalColor.transparent)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    clip = QPainterPath()
    clip.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
    p.setClipPath(clip)
    p.drawPixmap(0, 0, cropped)
    p.end()
    return out


def icon_label(filename, size=20, radius=6, fallback_emoji="", fallback_bg="#232842"):
    """Returns a QLabel showing a real icon image if the asset exists,
    otherwise falls back to an emoji glyph on a soft rounded background --
    used to progressively replace emoji icons with real logos wherever an
    assets/ image is available."""
    pix = icon_pixmap(filename, size=size, radius=radius)
    lbl = QLabel()
    lbl.setFixedSize(size, size)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if not pix.isNull():
        lbl.setPixmap(pix)
        lbl.setStyleSheet("background:transparent; border:none;")
    else:
        lbl.setText(fallback_emoji)
        lbl.setStyleSheet(f"background:{fallback_bg}; border-radius:{radius}px; font-size:{max(10, size // 2)}px;")
    return lbl


def load_pixmap(path):
    """Loads an image file into a QPixmap.

    Qt's built-in image plugins don't always include WebP support (depends
    on how the Qt build was packaged), so a `.webp` asset can silently
    decode as a null QPixmap even though the file is perfectly valid. This
    falls back to Pillow (already a hard dependency of this project) to
    decode the file and hand the raw pixels to Qt whenever QPixmap itself
    fails, so every supported asset format (webp/jpg/png/...) just works."""
    if not path or not os.path.exists(path):
        return QPixmap()
    pix = QPixmap(path)
    if not pix.isNull():
        return pix
    try:
        from PIL import Image
        from PyQt6.QtGui import QImage
        im = Image.open(path).convert("RGBA")
        data = im.tobytes("raw", "RGBA")
        qimg = QImage(data, im.width, im.height, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(qimg.copy())
    except Exception:
        return QPixmap()


def contain_pixmap(pix: QPixmap, box_w, box_h, bg="#131625"):
    """Scales `pix` to fit *entirely inside* a box_w x box_h canvas
    (never cropping any part of the source image, unlike
    KeepAspectRatioByExpanding + centre-crop) and centres it on a solid
    background so the result is always exactly box_w x box_h."""
    out = QPixmap(box_w, box_h)
    out.fill(QColor(bg))
    if pix.isNull():
        return out
    fitted = pix.scaled(box_w, box_h, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
    p = QPainter(out)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    x = (box_w - fitted.width()) // 2
    y = (box_h - fitted.height()) // 2
    p.drawPixmap(x, y, fitted)
    p.end()
    return out


def hero_pixmap_full(name, box=64, bg="#131625"):
    """Hero portrait guaranteed to show the *entire* image, letterboxed on
    a solid background rather than centre-cropped -- used anywhere a hero
    "card" must always display the full artwork (history lists, detail
    views, etc.)."""
    path = os.path.join(HERO_DIR, f"{name}.png")
    src = load_pixmap(path)
    if src.isNull():
        return _placeholder_pixmap(name, box, box)
    return contain_pixmap(src, box, box, bg=bg)


class DraggableTitleBar(QWidget):
    """
    A titlebar widget that, when installed on a frameless QWidget/QMainWindow,
    lets the user drag the window by clicking anywhere on it (except on child
    buttons) and double-click to toggle maximize. Attach via:
        bar = DraggableTitleBar(target_window=self)
    """
    def __init__(self, target_window, parent=None):
        super().__init__(parent)
        self._target = target_window
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self._target.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._target.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if hasattr(self._target, "isMaximized"):
            if self._target.isMaximized():
                self._target.showNormal()
            else:
                self._target.showMaximized()


_PLACEHOLDER_HUES = [
    ("#2a2540", "#171225"), ("#1f2b40", "#111a2b"), ("#2b1f30", "#17101c"),
    ("#20302c", "#101c18"), ("#302422", "#1a1210"), ("#242b3a", "#121722"),
]


def _placeholder_pixmap(name, w, h):
    """A tasteful dark gradient card (never a bare empty square) used when
    a hero portrait asset is missing, with the hero's initial glyph
    softly 'glowing' in the centre to suggest a blurred backdrop."""
    from PyQt6.QtGui import QLinearGradient, QRadialGradient, QBrush
    idx = sum(ord(c) for c in name) % len(_PLACEHOLDER_HUES)
    c1, c2 = _PLACEHOLDER_HUES[idx]
    pix = QPixmap(w, h)
    pix.fill(QColor(c2))
    p = QPainter(pix)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(0, 0, w, h)
    grad.setColorAt(0.0, QColor(c1))
    grad.setColorAt(1.0, QColor(c2))
    p.fillRect(0, 0, w, h, QBrush(grad))
    # soft glow blob behind the initial, to fake a blurred glass backdrop
    glow = QRadialGradient(w / 2, h / 2, max(w, h) * 0.6)
    glow.setColorAt(0.0, QColor(255, 255, 255, 26))
    glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.fillRect(0, 0, w, h, QBrush(glow))
    font = QFont("Segoe UI", int(min(w, h) * 0.42), QFont.Weight.Bold)
    p.setFont(font)
    p.setPen(QColor(255, 255, 255, 60))
    initial = (name or "?").strip()[:1].upper()
    p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, initial)
    p.end()
    return pix


def hero_pixmap(name, size=64, w=None, h=None):
    """Returns a hero portrait scaled/cropped to (w, h) -- or a size x size
    square if w/h aren't given. Falls back to a gradient placeholder
    (never a blank/empty box) when the asset file is missing."""
    tw, th = (w, h) if (w and h) else (size, size)
    path = os.path.join(HERO_DIR, f"{name}.png")
    pix = load_pixmap(path) if os.path.exists(path) else QPixmap()
    if pix.isNull():
        return _placeholder_pixmap(name, tw, th)
    scaled = pix.scaled(tw, th, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                         Qt.TransformationMode.SmoothTransformation)
    # centre-crop to the exact target box (KeepAspectRatioByExpanding only
    # guarantees the box is *covered*, not that it matches exactly)
    if scaled.width() != tw or scaled.height() != th:
        x = max(0, (scaled.width() - tw) // 2)
        y = max(0, (scaled.height() - th) // 2)
        scaled = scaled.copy(x, y, tw, th)
    return scaled


def hero_pixmap_169(name, w=96, h=54):
    """Hero portrait cropped to a 16:9 box, for the horizontal hero rows
    on the main screen ('Розпізнані герої')."""
    return hero_pixmap(name, w=w, h=h)


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
    t = theme.current()
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background-color: {t['surface']};
            border: 1px solid {t['border_soft']};
            border-radius: 16px;
        }}
    """)
    return f


def card_title(text, icon=""):
    t = theme.current()
    is_image = bool(icon) and "." in icon and not icon.startswith("http")
    pix = _section_icon_pixmap(icon, size=20, radius=6) if is_image else QPixmap()
    if not pix.isNull():
        wrap = QWidget()
        wrap.setStyleSheet("background:transparent; border:none;")
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(9)
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(20, 20)
        icon_lbl.setPixmap(pix)
        icon_lbl.setStyleSheet("background:transparent; border:none;")
        row.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        text_lbl = QLabel(text)
        text_lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {t['text_bright']}; border: none; background: transparent;")
        row.addWidget(text_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addStretch(1)
        return wrap
    lbl = QLabel(f"{icon}  {text}" if icon else text)
    lbl.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {t['text_bright']}; border: none; background: transparent;")
    return lbl


def page_title(text, icon_file="", fallback_emoji=""):
    """A page-header title row: real icon image (assets/<icon_file>) at
    20px, or an emoji glyph if the asset is missing, followed by the bold
    title text -- replaces the old approach of baking an emoji glyph
    directly into the title string."""
    t = theme.current()
    wrap = QWidget()
    wrap.setStyleSheet("background:transparent; border:none;")
    row = QHBoxLayout(wrap)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(10)
    ic = icon_label(icon_file, size=22, radius=5, fallback_emoji=fallback_emoji, fallback_bg="transparent")
    row.addWidget(ic)
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size:20px; font-weight:700; color:{t['text_bright']}; border:none; background:transparent;")
    row.addWidget(lbl)
    row.addStretch(1)
    return wrap


def small_label(text, color=None):
    t = theme.current()
    color = color or t["text_faint"]
    lbl = QLabel(text)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(f"font-size: 11px; color: {color}; border: none; background: transparent;")
    return lbl


def body_label(text, color=None, size=13, weight=400):
    t = theme.current()
    color = color or t["text_dim"]
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
        padding: 4px 10px;
        border: none;
    """)
    lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    lbl.setWordWrap(False)
    lbl.adjustSize()
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return lbl


class HeroChip(QWidget):
    """Hero portrait + name, used in 'Розпізнані герої' rows.

    By default renders a 16:9 hero icon (96x54, matching the recognised-
    heroes strip on the main screen); pass square=True for the old 1:1
    avatar look used elsewhere (history list thumbnails, etc.)."""
    def __init__(self, name, size=64, clickable=False, on_click=None, parent=None,
                 square=False, w=96, h=54):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        img_lbl = QLabel()
        if square:
            box_w, box_h, radius = size, size, 10
            pix = hero_pixmap(name, size)
        else:
            box_w, box_h, radius = w, h, 6
            pix = hero_pixmap(name, w=w, h=h)
        img_lbl.setFixedSize(box_w, box_h)
        img_lbl.setScaledContents(False)
        img_lbl.setPixmap(round_pixmap(pix, radius))
        img_lbl.setStyleSheet(f"border: 1px solid #262b40; border-radius: {radius}px;")
        layout.addWidget(img_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.setFixedWidth(box_w)
        name_lbl = QLabel(name)
        name_lbl.setFixedWidth(box_w)
        name_lbl.setWordWrap(True)
        name_lbl.setStyleSheet("font-size: 10px; color: #c4c7d6; border: none; background: transparent;")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(name_lbl)
        if clickable and on_click:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            def _handle_click(e, _name=name):
                on_click(_name)
            self.mousePressEvent = _handle_click


class FancyCheckBox(QWidget):
    """A checkbox that actually shows a checkmark (✓) inside a rounded
    square indicator, instead of relying on Qt's default (often invisible
    on dark themes) QCheckBox indicator. Optionally shows a text label to
    the right, click-toggleable on the whole row."""
    toggled = pyqtSignal(bool)

    def __init__(self, text="", checked=False, parent=None, box_size=18,
                 accent="#4F46E5", border_color="#2a2f45", bg="#11131e"):
        super().__init__(parent)
        self._checked = bool(checked)
        self._box = box_size
        self._accent = QColor(accent)
        self._border = QColor(border_color)
        self._bg = QColor(bg)
        self._fill = 1.0 if self._checked else 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)

        self._indicator = QLabel()
        self._indicator.setFixedSize(box_size, box_size)
        row.addWidget(self._indicator, 0, Qt.AlignmentFlag.AlignVCenter)

        self._label = None
        if text:
            self._label = QLabel(text)
            self._label.setStyleSheet("color:#c4c7d6; font-size:12px; border:none; background:transparent;")
            self._label.setWordWrap(True)
            row.addWidget(self._label, 1)

        self._anim = QPropertyAnimation(self, b"fillAmount", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._redraw()

    def _get_fill(self):
        return self._fill

    def _set_fill(self, value):
        self._fill = value
        self._redraw()

    fillAmount = pyqtProperty(float, _get_fill, _set_fill)

    def isChecked(self):
        return self._checked

    def setText(self, text):
        if self._label is not None:
            self._label.setText(text)

    def text(self):
        return self._label.text() if self._label is not None else ""

    def setChecked(self, checked, animate=True):
        checked = bool(checked)
        if checked == self._checked:
            return
        self._checked = checked
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._fill)
            self._anim.setEndValue(1.0 if checked else 0.0)
            self._anim.start()
        else:
            self._fill = 1.0 if checked else 0.0
            self._redraw()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            self.toggled.emit(self._checked)
            event.accept()

    def _redraw(self):
        s = self._box
        pix = QPixmap(s, s)
        pix.fill(Qt.GlobalColor.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        f = max(0.0, min(1.0, self._fill))
        bg = QColor(
            int(self._bg.red()   + (self._accent.red()   - self._bg.red())   * f),
            int(self._bg.green() + (self._accent.green() - self._bg.green()) * f),
            int(self._bg.blue()  + (self._accent.blue()  - self._bg.blue())  * f),
        )
        border = self._accent if f > 0.01 else self._border
        p.setPen(QPen(border, 1.4))
        p.setBrush(bg)
        r = 5
        p.drawRoundedRect(1, 1, s - 2, s - 2, r, r)

        if f > 0.01:
            pen = QPen(QColor("#ffffff"))
            pen.setWidthF(max(1.6, s * 0.11))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.setOpacity(f)
            check = QPolygonF([
                QPointF(s * 0.24, s * 0.54),
                QPointF(s * 0.43, s * 0.72),
                QPointF(s * 0.78, s * 0.30),
            ])
            p.drawPolyline(check)
        p.end()
        self._indicator.setPixmap(pix)


class AnimatedToggle(QWidget):
    """Smooth, custom-painted on/off switch replacing the flat QCheckBox
    indicator. The knob slides and the track colour cross-fades over
    ~180ms on every change, whether from a click or setChecked()."""
    toggled = pyqtSignal(bool)

    _KNOB_MARGIN = 3
    _WIDTH = 44
    _HEIGHT = 24

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self._checked = bool(checked)
        self._min_x = float(self._KNOB_MARGIN)
        self._max_x = float(self._WIDTH - self._HEIGHT + self._KNOB_MARGIN)
        self._knob_x = self._max_x if self._checked else self._min_x
        self.setFixedSize(self._WIDTH, self._HEIGHT)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._anim = QPropertyAnimation(self, b"knobPos", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def _get_knob_pos(self):
        return self._knob_x

    def _set_knob_pos(self, value):
        self._knob_x = value
        self.update()

    knobPos = pyqtProperty(float, _get_knob_pos, _set_knob_pos)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked, animate=True):
        checked = bool(checked)
        if checked == self._checked and animate:
            return
        self._checked = checked
        target = self._max_x if checked else self._min_x
        if animate:
            self._anim.stop()
            self._anim.setStartValue(self._knob_x)
            self._anim.setEndValue(target)
            self._anim.start()
        else:
            self._knob_x = target
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            self.toggled.emit(self._checked)
            event.accept()

    def paintEvent(self, event):
        t = theme.current()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        frac = (self._knob_x - self._min_x) / max(1.0, (self._max_x - self._min_x))
        frac = max(0.0, min(1.0, frac))
        off = QColor(t["border_input"])
        on = QColor(t["accent"])
        track = QColor(
            int(off.red() + (on.red() - off.red()) * frac),
            int(off.green() + (on.green() - off.green()) * frac),
            int(off.blue() + (on.blue() - off.blue()) * frac),
        )
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(0, 1, self._WIDTH, self._HEIGHT - 2, (self._HEIGHT - 2) / 2, (self._HEIGHT - 2) / 2)

        knob_d = self._HEIGHT - 2 * self._KNOB_MARGIN
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(QPointF(self._knob_x + knob_d / 2, self._HEIGHT / 2), knob_d / 2, knob_d / 2)
        p.end()


class AnimatedButton(QPushButton):
    """QPushButton whose background colour eases smoothly between its base
    and hover colours instead of snapping instantly (Qt stylesheets don't
    support CSS transitions, so this is driven with QPropertyAnimation)."""

    def __init__(self, text, base_color=None, hover_color=None, press_color=None,
                 text_color="#ffffff", radius=10, parent=None, extra_css=""):
        super().__init__(text, parent)
        t = theme.current()
        self._base = QColor(base_color or t["accent"])
        self._hover = QColor(hover_color or t["accent_hover"])
        self._press = QColor(press_color or t["accent_press"])
        self._current = QColor(self._base)
        self._text_color = text_color
        self._radius = radius
        # Extra QSS (e.g. text-align/padding overrides) merged into every
        # recoloured stylesheet -- previously any caller that appended its
        # own rules via `btn.setStyleSheet(btn.styleSheet() + "...")` had
        # them silently wiped the moment the button was hovered/pressed,
        # since _apply_style() replaces the *whole* stylesheet on every
        # animation frame. Passing the extra rules in here keeps them.
        self._extra_css = extra_css
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(46)
        self._anim = QPropertyAnimation(self, b"bgColor", self)
        self._anim.setDuration(160)
        self._apply_style()

    def _get_bg(self):
        return self._current

    def _set_bg(self, color):
        self._current = color
        self._apply_style()

    bgColor = pyqtProperty(QColor, _get_bg, _set_bg)

    def setExtraCss(self, extra_css):
        self._extra_css = extra_css or ""
        self._apply_style()

    def _apply_style(self):
        c = self._current
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgb({c.red()},{c.green()},{c.blue()});
                color: {self._text_color};
                border-radius: {self._radius}px;
                font-weight: 700;
                font-size: 14px;
                border: none;
            }}
            {self._extra_css}
        """)

    def _animate_to(self, color):
        self._anim.stop()
        self._anim.setStartValue(self._current)
        self._anim.setEndValue(color)
        self._anim.start()

    def enterEvent(self, event):
        self._animate_to(self._hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_to(self._base)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._animate_to(self._press)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._animate_to(self._hover if self.underMouse() else self._base)
        super().mouseReleaseEvent(event)


class ToggleRow(QWidget):
    def __init__(self, title, subtitle, checked=False, parent=None):
        super().__init__(parent)
        t = theme.current()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        tl = QLabel(title)
        tl.setStyleSheet(f"font-size: 13px; color: {t['text']}; font-weight: 600; border:none; background:transparent;")
        sl = QLabel(subtitle)
        sl.setStyleSheet(f"font-size: 11px; color: {t['text_faint']}; border:none; background:transparent;")
        text_box.addWidget(tl)
        text_box.addWidget(sl)
        layout.addLayout(text_box)
        layout.addStretch()
        self.checkbox = AnimatedToggle(checked=checked)
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
