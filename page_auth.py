"""
Authentication screen — two views stacked in a QStackedWidget:
  index 0 → LoginForm
  index 1 → RegisterForm

The left side paints an original dark-fantasy scene (same palette/mood as
the mockup) without reproducing licensed Dota 2 key-art. The right side is
a styled card that matches the mockup layout pixel-for-pixel.
"""
import math, os, random

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QStackedWidget, QFrame, QComboBox, QMessageBox, QGridLayout,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt6.QtGui import (QPainter, QLinearGradient, QRadialGradient, QColor, QPen,
                          QPolygonF, QPixmap, QPainterPath)

from services import auth_service, i18n
from ui.widgets import AnimatedButton, FancyCheckBox, load_pixmap, contain_pixmap

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _asset_pixmap(filename):
    return load_pixmap(os.path.join(ASSETS_DIR, filename))


def _logo_pixmap(filename, size=64, radius=16):
    """Centre-crops an asset image to a size x size square and rounds its
    corners -- used for the app logo wherever a compact square mark is
    needed (login/register headers, titlebar)."""
    src = _asset_pixmap(filename)
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
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
    p.setClipPath(path)
    p.drawPixmap(0, 0, cropped)
    p.end()
    return out


# ═══════════════════════════════ LEFT BRAND PANEL ═══════════════════════════

class BrandCanvas(QWidget):
    """Paints the *entire* auth screen's background using assets/auth_bg.jpg
    -- previously this only covered the left ~55% of the window while the
    right (login/register) side sat on a flat, unrelated solid colour,
    which read as two disconnected halves instead of one screen.

    The picture is shown 'in full' (contain scaling, never cropped) across
    the area behind the feature text on the left. The area behind the
    login/register card (right) intentionally only shows the softly
    blurred, darkened backdrop copy -- never the sharp image -- so the
    card's text stays legible while the whole window still reads as one
    continuous background instead of a hard seam."""
    def __init__(self, parent=None, sharp_area_frac=0.66, darken_from_frac=0.55):
        super().__init__(parent)
        self._bg = _asset_pixmap("auth_bg.jpg")
        self._blur_cache_key = None
        self._blur_cache_pix = None
        # fraction of the width (from the left) where the sharp, uncropped
        # image is allowed to show; beyond that only the blurred backdrop
        # is visible (this is where the login card sits)
        self._sharp_area_frac = sharp_area_frac
        # fraction of the width where the extra darkening gradient begins
        self._darken_from_frac = darken_from_frac

    def _blurred_cover(self, w, h):
        """Cheap box-blur approximation: downscale a lot, then upscale back
        with smooth interpolation. Cached per output size so it isn't
        recomputed on every repaint/resize tick."""
        key = (w, h)
        if self._blur_cache_key == key and self._blur_cache_pix is not None:
            return self._blur_cache_pix
        cover = self._bg.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                 Qt.TransformationMode.SmoothTransformation)
        cx = max(0, (cover.width() - w) // 2)
        cy = max(0, (cover.height() - h) // 2)
        cover = cover.copy(cx, cy, w, h)
        small = cover.scaled(max(1, w // 24), max(1, h // 24),
                              Qt.AspectRatioMode.IgnoreAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        blurred = small.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio,
                                Qt.TransformationMode.SmoothTransformation)
        self._blur_cache_key = key
        self._blur_cache_pix = blurred
        return blurred

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        if not self._bg.isNull() and w > 0 and h > 0:
            # 1) blurred, darkened cover backdrop -- fills the *entire*
            #    window, so there's never a bare/mismatched area anywhere,
            #    including behind the login card on the right
            backdrop = self._blurred_cover(w, h)
            p.drawPixmap(0, 0, backdrop)
            p.fillRect(0, 0, w, h, QColor(6, 7, 15, 130))

            # 2) the full, uncropped image on top ("contain" scaling) --
            #    but only within the left "sharp area"; the login card's
            #    side never shows the crisp photo, only the blurred one
            #    from step 1, which reads as an intentionally blurred
            #    background behind the form rather than a mismatch.
            sharp_w = int(w * self._sharp_area_frac)
            if sharp_w > 0:
                p.save()
                p.setClipRect(0, 0, sharp_w, h)
                fit = self._bg.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
                fx = (w - fit.width()) // 2
                fy = (h - fit.height()) // 2
                p.drawPixmap(fx, fy, fit)
                p.restore()
        else:
            p.fillRect(0, 0, w, h, QColor("#0b0e1a"))

        # dark gradient overlay for text legibility (darkest at the edges
        # where the title/feature copy and footer sit)
        overlay = QLinearGradient(0, 0, 0, h)
        overlay.setColorAt(0.0, QColor(6, 7, 15, 205))
        overlay.setColorAt(0.35, QColor(6, 7, 15, 130))
        overlay.setColorAt(0.7, QColor(6, 7, 15, 150))
        overlay.setColorAt(1.0, QColor(6, 7, 15, 220))
        p.fillRect(0, 0, w, h, overlay)

        # extra horizontal darkening ramp toward the right, so the login
        # card always sits on a comfortably dark, blurred surface
        darken_x0 = w * self._darken_from_frac
        if darken_x0 < w:
            side = QLinearGradient(darken_x0, 0, w, 0)
            side.setColorAt(0.0, QColor(6, 7, 15, 0))
            side.setColorAt(1.0, QColor(6, 7, 15, 195))
            p.fillRect(int(darken_x0), 0, int(w - darken_x0), h, side)
        p.end()


def _feature_icon_pixmap(filename, size=48, radius=12):
    src = _asset_pixmap(filename)
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
    path = QPainterPath()
    path.addRoundedRect(QRectF(0, 0, size, size), radius, radius)
    p.setClipPath(path)
    p.drawPixmap(0, 0, cropped)
    p.end()
    return out


def _feature_item(icon, bg_color, title, subtitle):
    """`icon` may be an emoji glyph (str) or an image filename under
    assets/ -- image filenames are detected by having a file extension."""
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(16)
    icon_box = QLabel()
    icon_box.setFixedSize(48, 48)
    icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
    is_image = "." in icon and not icon.startswith(("http",))
    pix = _feature_icon_pixmap(icon) if is_image else QPixmap()
    if not pix.isNull():
        icon_box.setPixmap(pix)
        icon_box.setStyleSheet("background:transparent; border:none;")
    else:
        icon_box.setText(icon)
        icon_box.setStyleSheet(f"background:{bg_color}; border-radius:12px; font-size:19px;")
    lay.addWidget(icon_box)
    txt = QVBoxLayout(); txt.setSpacing(3)
    t = QLabel(title)
    t.setStyleSheet("color:#fff; font-weight:700; font-size:15px; border:none; background:transparent;")
    _add_text_shadow(t)
    s = QLabel(subtitle)
    s.setWordWrap(True)
    s.setStyleSheet("color:#c7cadb; font-size:12px; border:none; background:transparent;")
    s.setMaximumWidth(340)
    _add_text_shadow(s, blur=6, alpha=200)
    txt.addWidget(t); txt.addWidget(s)
    lay.addLayout(txt, 1)
    return w


def _add_text_shadow(label, blur=8, alpha=230, offset=1):
    """Drop shadow behind a QLabel's glyphs so light-coloured text stays
    legible over a busy photographic background, regardless of how bright
    the pixels underneath happen to be."""
    shadow = QGraphicsDropShadowEffect(label)
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset)
    shadow.setColor(QColor(0, 0, 0, alpha))
    label.setGraphicsEffect(shadow)


def _build_text_block():
    """The left-side marketing copy (title + feature list) as a plain
    transparent widget -- no longer owns its own BrandCanvas, since
    AuthScreen now paints a single canvas across the *whole* window and
    places this block on top of it."""
    text_col = QWidget()
    text_col.setMaximumWidth(460)
    text_col.setStyleSheet("QWidget { background: transparent; }")
    overlay_layout = QVBoxLayout(text_col)
    overlay_layout.setContentsMargins(0, 0, 0, 0)
    overlay_layout.setSpacing(20)

    title = QLabel("Інтелектуальний помічник\nдля аналізу драфту")
    title.setStyleSheet("color:#fff; font-size:32px; font-weight:800; border:none; background:transparent;")
    _add_text_shadow(title, blur=10, alpha=235)
    overlay_layout.addWidget(title)

    dota_lbl = QLabel("Dota 2")
    dota_lbl.setStyleSheet("color:#b3a8ff; font-size:32px; font-weight:800; border:none; background:transparent;")
    _add_text_shadow(dota_lbl, blur=10, alpha=235)
    overlay_layout.addWidget(dota_lbl)

    tagline = QLabel("Аналізуй драфт. Обирай найкраще. Перемагай.")
    tagline.setStyleSheet("color:#d3d6e6; font-size:15px; border:none; background:transparent;")
    _add_text_shadow(tagline, blur=6, alpha=210)
    overlay_layout.addWidget(tagline)

    overlay_layout.addSpacing(14)
    overlay_layout.addWidget(_feature_item("detect_heroes.webp", "#2a2560", "Розпізнавання героїв",
                                            "Автоматичне визначення героїв зі скриншота драфту"))
    overlay_layout.addWidget(_feature_item("analys_draft.png", "#1c3d26", "Аналіз драфту",
                                            "Контрпіки, синергії, мета та оцінка сили команд"))
    overlay_layout.addWidget(_feature_item("recomendation_ai.jpg", "#403016", "Рекомендації від ШІ",
                                            "ТОП-5 героїв для вибору з поясненнями"))
    overlay_layout.addWidget(_feature_item("statistic_actual.png", "#153048", "Актуальна статистика",
                                            "Дані з STRATZ API для точного аналізу"))
    return text_col


def _build_footer_label():
    footer = QLabel("© 2026. Всі права захищені.")
    footer.setStyleSheet("color:#c7cadb; font-size:11px; border:none; background:transparent;")
    _add_text_shadow(footer, blur=6, alpha=210)
    return footer


# ═══════════════════════════════ SHARED FORM HELPERS ═══════════════════════

def _input_field(placeholder, icon="", password=False):
    """Returns (wrapper_widget, QLineEdit)."""
    wrap = QFrame()
    wrap.setMinimumHeight(56)
    wrap.setStyleSheet("""
        QFrame { background:#090a12; border:1px solid #252a3f; border-radius:12px; }
        QFrame:focus-within { border:1px solid #4F46E5; }
    """)
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(20, 0, 14, 0)
    lay.setSpacing(14)
    if icon:
        ic = QLabel(icon)
        ic.setFixedWidth(18)
        ic.setStyleSheet("border:none; background:transparent; color:#6c7085; font-size:15px;")
        lay.addWidget(ic)
    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    edit.setStyleSheet("""
        QLineEdit { border:none; background:transparent; color:#f2f3fa; font-size:14px; padding:14px 2px; }
    """)
    if password:
        edit.setEchoMode(QLineEdit.EchoMode.Password)
    lay.addWidget(edit, 1)
    if password:
        eye = QPushButton("👁")
        eye.setFixedSize(32, 32)
        eye.setStyleSheet("QPushButton{background:transparent;border:none;color:#6c7085;font-size:14px;} QPushButton:hover{color:#fff;}")
        eye.clicked.connect(lambda: edit.setEchoMode(
            QLineEdit.EchoMode.Normal if edit.echoMode() == QLineEdit.EchoMode.Password
            else QLineEdit.EchoMode.Password))
        lay.addWidget(eye)
    return wrap, edit


def _or_divider():
    row = QHBoxLayout()
    for _ in range(2):
        ln = QFrame(); ln.setFixedHeight(1)
        ln.setStyleSheet("background:#222639;")
        row.addWidget(ln, 1)
        if _ == 0:
            lbl = QLabel("або")
            lbl.setStyleSheet("color:#4a4f66; font-size:11px; border:none; background:transparent; padding:0 12px;")
            row.addWidget(lbl)
    return row


def _primary_btn(text):
    b = AnimatedButton(text, base_color="#4F46E5", hover_color="#6366F1", press_color="#4338CA", radius=12)
    b.setMinimumHeight(54)
    f = b.font(); f.setPointSize(f.pointSize() + 1); b.setFont(f)
    return b


def _ghost_btn(text):
    b = QPushButton(text)
    b.setMinimumHeight(52)
    b.setStyleSheet("""
        QPushButton { background:transparent; color:#e7e9f3; border:1px solid #252a3f;
            border-radius:12px; font-weight:600; font-size:14px; }
        QPushButton:hover { background:#161a28; }
    """)
    return b


def _google_logo_pixmap(height=18):
    """Loads the Google "G" mark, scaled to a fixed height while keeping
    its aspect ratio.

    Uses a pre-cleaned, tightly-cropped, transparent-background PNG
    (google_logo_clean.png) instead of the raw google_logo.webp asset --
    the original file carries a ~1px near-white edge halo around the
    circular mark that, once the image is scaled far down for a small
    button icon, turns into a visible grey/black "frame" around the logo.
    The cleaned asset has that halo removed and true transparency instead,
    so the logo blends seamlessly onto any background."""
    src = _asset_pixmap("google_logo_clean.png")
    if src.isNull():
        src = _asset_pixmap("google_logo.webp")
    if src.isNull():
        return QPixmap()
    return src.scaledToHeight(height, Qt.TransformationMode.SmoothTransformation)


def _google_btn(text=None):
    """A clean, Google-style 'Continue with Google' button: white pill,
    dark text, real Google logo image -- matching Google's actual sign-in
    buttons instead of a hand-drawn approximation.

    The logo is positioned with a real QHBoxLayout (not by monkey-patching
    resizeEvent with a lambda) -- overriding a Qt virtual like resizeEvent
    with something that returns a non-None value is exactly what causes
    'TypeError: invalid argument to sipBadCatcherResult()' when Qt's C++
    side calls it back."""
    text = text or i18n.t("google_continue")
    # the logo image already spells out "Google", so strip the duplicate
    # word from the translated label and keep just the lead-in phrase
    prefix = text.replace("Google", "").strip(" :-–") or text
    b = QPushButton()
    b.setMinimumHeight(46)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet("""
        QPushButton { background:#ffffff; color:#1f2430; border:1px solid #dadce0;
            border-radius:10px; font-weight:600; font-size:13px; text-align:center; }
        QPushButton:hover { background:#f7f8fb; }
        QPushButton:pressed { background:#eceef3; }
    """)
    inner = QHBoxLayout(b)
    inner.setContentsMargins(24, 0, 24, 0)
    inner.setSpacing(8)
    inner.addStretch()
    logo_pix = _google_logo_pixmap(18)
    prefix_lbl = QLabel(prefix if not logo_pix.isNull() else text)
    prefix_lbl.setStyleSheet("background:transparent; border:none; color:#1f2430; font-weight:600; font-size:13px;")
    prefix_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    inner.addWidget(prefix_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
    if not logo_pix.isNull():
        logo_lbl = QLabel()
        logo_lbl.setPixmap(logo_pix)
        logo_lbl.setStyleSheet("background:transparent; border:none;")
        logo_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        inner.addWidget(logo_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
    inner.addStretch()
    # Exposed so retranslate() can update the visible label -- the QPushButton
    # itself must NEVER get its own .setText(), since Qt would then draw its
    # native text *on top of* this custom label/logo layout, producing
    # garbled, overlapping text.
    b._prefix_lbl = prefix_lbl
    b._logo_present = not logo_pix.isNull()
    return b


def _set_google_btn_text(button, text):
    """Safely updates a _google_btn()'s visible label without ever calling
    QPushButton.setText() on it (see the warning in _google_btn)."""
    prefix = text.replace("Google", "").strip(" :-–") or text
    button._prefix_lbl.setText(prefix if button._logo_present else text)


def _link_btn(text):
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet("""
        QPushButton { background:transparent; border:none; color:#9d90f5;
            font-size:12px; font-weight:600; padding:0; }
        QPushButton:hover { color:#b6abf9; }
    """)
    return b


# ═══════════════════════════════ LOGIN FORM ══════════════════════════════════

class LoginForm(QWidget):
    login_succeeded  = pyqtSignal(dict)
    switch_register  = pyqtSignal()
    guest_requested  = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(64, 56, 64, 48)
        lay.setSpacing(18)

        # App logo (assets/dota_logo.jpg), falls back to a glyph if missing
        logo_pix = _logo_pixmap("dota_logo.jpg", size=96, radius=22)
        logo_lbl = QLabel()
        if not logo_pix.isNull():
            logo_lbl.setFixedSize(96, 96)
            logo_lbl.setPixmap(logo_pix)
        else:
            logo_lbl.setText("⛨")
            logo_lbl.setStyleSheet("font-size:72px; color:#e03030; border:none; background:transparent;")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel(i18n.t("login_title"))
        title.setStyleSheet("color:#fff; font-size:25px; font-weight:800; border:none; background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        self._title_lbl = title

        sub = QLabel(i18n.t("login_subtitle"))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color:#8a8fa8; font-size:12px; border:none; background:transparent;")
        lay.addWidget(sub)
        self._sub_lbl = sub

        lay.addSpacing(4)

        id_wrap, self.id_edit = _input_field(i18n.t("field_id"), "👤")
        lay.addWidget(id_wrap)

        pw_wrap, self.pw_edit = _input_field(i18n.t("field_password"), "🔒", password=True)
        lay.addWidget(pw_wrap)

        rem_row = QHBoxLayout()
        self.remember_chk = FancyCheckBox(i18n.t("remember_me"), checked=True)
        rem_row.addWidget(self.remember_chk)
        rem_row.addStretch()
        lay.addLayout(rem_row)

        login_btn = _primary_btn(i18n.t("btn_login"))
        login_btn.clicked.connect(self._on_login)
        lay.addWidget(login_btn)
        self._login_btn = login_btn

        self._divider_row = _or_divider()
        lay.addLayout(self._divider_row)

        guest_btn = _ghost_btn(i18n.t("continue_guest"))
        guest_btn.clicked.connect(self.guest_requested.emit)
        lay.addWidget(guest_btn)
        self._guest_btn = guest_btn

        bottom = QHBoxLayout()
        reg_link = _link_btn(i18n.t("create_account"))
        reg_link.clicked.connect(self.switch_register.emit)
        forgot_link = _link_btn(i18n.t("forgot_password"))
        forgot_link.clicked.connect(self._on_forgot)
        bottom.addWidget(reg_link)
        bottom.addStretch()
        bottom.addWidget(forgot_link)
        lay.addLayout(bottom)
        self._reg_link = reg_link
        self._forgot_link = forgot_link

        lay.addStretch()

    def retranslate(self):
        self._title_lbl.setText(i18n.t("login_title"))
        self._sub_lbl.setText(i18n.t("login_subtitle"))
        self.id_edit.setPlaceholderText(i18n.t("field_id"))
        self.pw_edit.setPlaceholderText(i18n.t("field_password"))
        self.remember_chk.setText(i18n.t("remember_me"))
        self._login_btn.setText(i18n.t("btn_login"))
        self._guest_btn.setText(i18n.t("continue_guest"))
        self._reg_link.setText(i18n.t("create_account"))
        self._forgot_link.setText(i18n.t("forgot_password"))

    def prefill(self, email: str):
        self.id_edit.setText(email)

    def _on_forgot(self):
        QMessageBox.information(self, "Відновлення паролю",
                                 "Ця функція потребує поштового сервісу і буде доступна "
                                 "в наступному оновленні.")

    def _on_login(self):
        # Guard against re-entrancy: QMessageBox.warning()/.information() runs
        # its own nested event loop, so a queued double-click on the login
        # button would otherwise re-enter this method while the first call
        # is still on the stack (e.g. showing a dialog) -- causing confusing
        # double-registration/"already exists"-style symptoms.
        if getattr(self, "_busy", False):
            return
        self._busy = True
        self._login_btn.setEnabled(False)
        try:
            identifier = self.id_edit.text().strip()
            password   = self.pw_edit.text()
            if not identifier or not password:
                QMessageBox.warning(self, "Вхід", "Заповніть усі поля.")
                return
            ok, msg, user = auth_service.login_user(identifier, password)
            if not ok:
                QMessageBox.warning(self, "Помилка входу", msg)
                return
            auth_service.remember_user(user["email"] if self.remember_chk.isChecked() else None)
            self.login_succeeded.emit(user)
        finally:
            self._busy = False
            self._login_btn.setEnabled(True)


# ═══════════════════════════════ REGISTER FORM ═══════════════════════════════

class GoogleSignInDialog(QWidget):
    """
    Lightweight modal imitating a Google account picker. Real OAuth needs a
    registered client + backend redirect, which this offline desktop app
    doesn't have -- so this collects the Google email/name directly and
    creates a locally-linked account, clearly labeled as such.
    """
    signed_in = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Увійти з Google")
        # Fixed width keeps the card a consistent, comfortable size; height
        # is left to the layout's own size hint (setFixedSize(400, 400) used
        # to hard-clip the content -- the note text alone needs ~3 lines,
        # plus two inputs and two buttons, which never fit in 400px tall).
        self.setFixedWidth(440)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.result_user = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)

        card = QFrame()
        card.setStyleSheet("""
            QFrame { background:#151824; border:1px solid #2a2f45; border-radius:16px; }
        """)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 160))
        card.setGraphicsEffect(shadow)
        outer.addWidget(card)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(30, 26, 30, 26)
        lay.setSpacing(10)

        close_row = QHBoxLayout()
        close_row.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("QPushButton{background:transparent;border:none;color:#6c7085;font-size:13px;}"
                                 "QPushButton:hover{color:#fff;}")
        close_btn.clicked.connect(self.close)
        close_row.addWidget(close_btn)
        lay.addLayout(close_row)

        badge_row = QHBoxLayout()
        badge_row.addStretch()
        badge_wrap = QFrame()
        badge_wrap.setFrameShape(QFrame.Shape.NoFrame)
        badge_wrap.setFixedSize(150, 56)
        badge_wrap.setStyleSheet("QFrame { background:#ffffff; border-radius:16px; border:none; }")
        bl = QVBoxLayout(badge_wrap); bl.setContentsMargins(0, 0, 0, 0)
        bl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_pix = _google_logo_pixmap(26)
        logo_lbl = QLabel()
        logo_lbl.setStyleSheet("background:transparent; border:none;")
        if not logo_pix.isNull():
            logo_lbl.setPixmap(logo_pix)
        else:
            logo_lbl.setText("Google")
            logo_lbl.setStyleSheet("color:#1f2430; font-weight:800; font-size:18px; background:transparent; border:none;")
        bl.addWidget(logo_lbl)
        badge_row.addWidget(badge_wrap)
        badge_row.addStretch()
        lay.addLayout(badge_row)
        lay.addSpacing(4)

        title = QLabel("Увійти через Google")
        title.setStyleSheet("color:#fff; font-size:17px; font-weight:800; border:none; background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        note = QLabel("Спрощений локальний вхід: введіть ваш Google email. "
                       "Повна OAuth-інтеграція потребує реєстрації клієнта в Google Cloud "
                       "і серверної частини, недоступної в цьому офлайн-застосунку.")
        note.setWordWrap(True)
        note.setStyleSheet("color:#8a8fa8; font-size:10px; border:none; background:transparent;")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(note)
        lay.addSpacing(6)

        name_wrap, self.name_edit = _input_field("Ім'я", "👤")
        lay.addWidget(name_wrap)
        email_wrap, self.email_edit = _input_field("your.name@gmail.com", "✉")
        lay.addWidget(email_wrap)
        lay.addSpacing(4)

        continue_btn = _primary_btn("Продовжити")
        continue_btn.clicked.connect(self._on_continue)
        lay.addWidget(continue_btn)

        cancel_btn = _ghost_btn("Скасувати")
        cancel_btn.clicked.connect(self.close)
        lay.addWidget(cancel_btn)

        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def _on_continue(self):
        if getattr(self, "_busy", False):
            return
        self._busy = True
        try:
            email = self.email_edit.text().strip()
            name = self.name_edit.text().strip()
            if not email:
                QMessageBox.warning(self, "Google", "Введіть email.")
                return
            ok, msg, user = auth_service.google_login(email, name)
            if not ok:
                QMessageBox.warning(self, "Google", msg)
                return
            self.result_user = user
            self.signed_in.emit(user)
            self.close()
        finally:
            self._busy = False


class RegisterForm(QWidget):
    register_succeeded = pyqtSignal(dict)
    switch_login       = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(64, 44, 64, 40)
        lay.setSpacing(14)

        # Registration uses its own icon (assets/adduser.png) instead of the
        # generic Dota logo, sized to match the Login screen's 96px logo.
        logo_pix = _logo_pixmap("adduser.png", size=96, radius=22)
        logo_lbl = QLabel()
        if not logo_pix.isNull():
            logo_lbl.setFixedSize(96, 96)
            logo_lbl.setPixmap(logo_pix)
        else:
            logo_lbl.setText("👤+")
            logo_lbl.setStyleSheet("font-size:72px; color:#9d90f5; border:none; background:transparent;")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        title = QLabel(i18n.t("register_title"))
        title.setStyleSheet("color:#fff; font-size:21px; font-weight:800; border:none; background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)
        self._title_lbl = title

        sub = QLabel(i18n.t("register_subtitle"))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color:#8a8fa8; font-size:12px; border:none; background:transparent;")
        lay.addWidget(sub)
        self._sub_lbl = sub

        # name row
        name_row = QHBoxLayout(); name_row.setSpacing(12)
        fn_wrap, self.fn_edit = _input_field(i18n.t("field_firstname"), "👤")
        ln_wrap, self.ln_edit = _input_field(i18n.t("field_lastname"), "👤")
        name_row.addWidget(fn_wrap, 1)
        name_row.addWidget(ln_wrap, 1)
        lay.addLayout(name_row)

        email_wrap, self.email_edit = _input_field(i18n.t("field_email"), "✉")
        lay.addWidget(email_wrap)

        pw_wrap, self.pw_edit   = _input_field(i18n.t("field_password"), "🔒", password=True)
        pw2_wrap, self.pw2_edit = _input_field(i18n.t("field_password2"), "🔒", password=True)
        lay.addWidget(pw_wrap)
        lay.addWidget(pw2_wrap)
        self.pw_edit.textChanged.connect(self._update_reqs)

        # password requirements grid
        req_title = QLabel("Пароль має містити:")
        req_title.setStyleSheet("color:#8a8fa8; font-size:11px; border:none; background:transparent;")
        lay.addWidget(req_title)

        self.req_labels: dict[str, QLabel] = {}
        specs = [
            ("length", "Мінімум 8 символів"), ("lower", "Малу літеру (a-z)"),
            ("upper", "Велику літеру (A-Z)"), ("digit", "Цифру (0-9)"),
        ]
        grid = QGridLayout(); grid.setHorizontalSpacing(24); grid.setVerticalSpacing(4)
        for i, (key, label) in enumerate(specs):
            lbl = QLabel(f"○  {label}")
            lbl.setStyleSheet("color:#4a4f66; font-size:11px; border:none; background:transparent;")
            self.req_labels[key] = lbl
            grid.addWidget(lbl, i // 2, i % 2)
        lay.addLayout(grid)
        self._update_reqs()

        # terms
        terms_row = QHBoxLayout(); terms_row.setSpacing(10)
        self.terms_chk = FancyCheckBox(box_size=17)
        terms_lbl = QLabel(
            'Я приймаю <span style="color:#9d90f5; font-weight:600;">Умови використання</span>'
            ' та <span style="color:#9d90f5; font-weight:600;">Політику конфіденційності</span>'
        )
        terms_lbl.setStyleSheet("color:#8a8fa8; font-size:11px; border:none; background:transparent;")
        terms_lbl.setWordWrap(True)
        terms_row.addWidget(self.terms_chk, 0, Qt.AlignmentFlag.AlignTop)
        terms_row.addWidget(terms_lbl, 1)
        lay.addLayout(terms_row)

        reg_btn = _primary_btn(i18n.t("btn_register"))
        reg_btn.clicked.connect(self._on_register)
        lay.addWidget(reg_btn)
        self._reg_btn = reg_btn

        lay.addLayout(_or_divider())

        google_btn = _google_btn()
        google_btn.clicked.connect(self._on_google)
        lay.addWidget(google_btn)
        self._google_btn = google_btn

        bottom = QHBoxLayout()
        bottom.addStretch()
        have_lbl = QLabel(i18n.t("have_account"))
        have_lbl.setStyleSheet("color:#8a8fa8; font-size:12px; border:none; background:transparent;")
        login_link = _link_btn(i18n.t("login_link"))
        login_link.clicked.connect(self.switch_login.emit)
        bottom.addWidget(have_lbl)
        bottom.addWidget(login_link)
        bottom.addStretch()
        lay.addLayout(bottom)
        self._have_lbl = have_lbl
        self._login_link = login_link

        lay.addStretch()

    def retranslate(self):
        self._title_lbl.setText(i18n.t("register_title"))
        self._sub_lbl.setText(i18n.t("register_subtitle"))
        self.fn_edit.setPlaceholderText(i18n.t("field_firstname"))
        self.ln_edit.setPlaceholderText(i18n.t("field_lastname"))
        self.email_edit.setPlaceholderText(i18n.t("field_email"))
        self.pw_edit.setPlaceholderText(i18n.t("field_password"))
        self.pw2_edit.setPlaceholderText(i18n.t("field_password2"))
        self._reg_btn.setText(i18n.t("btn_register"))
        _set_google_btn_text(self._google_btn, i18n.t("google_continue"))
        self._have_lbl.setText(i18n.t("have_account"))
        self._login_link.setText(i18n.t("login_link"))

    def _update_reqs(self):
        reqs = auth_service.password_requirements(self.pw_edit.text())
        for key, ok in reqs.items():
            lbl = self.req_labels[key]
            label_text = lbl.text().split("  ", 1)[1]
            lbl.setText(f"{'●' if ok else '○'}  {label_text}")
            lbl.setStyleSheet(
                f"color:{'#5ee08a' if ok else '#4a4f66'}; font-size:11px; "
                "border:none; background:transparent;"
            )

    def _on_google(self):
        dialog = GoogleSignInDialog(self)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.signed_in.connect(self.register_succeeded.emit)
        dialog.show()
        self._google_dialog = dialog  # keep a reference alive

    def _on_register(self):
        # Same re-entrancy guard as LoginForm._on_login -- without it, a
        # queued second click delivered during the "Готово!" QMessageBox's
        # nested event loop would re-run registration for the *same*
        # already-created account, surface a confusing "already exists"
        # warning on top of the success dialog, and could leave the user
        # unsure whether the account was actually created.
        if getattr(self, "_busy", False):
            return
        self._busy = True
        self._reg_btn.setEnabled(False)
        try:
            fn    = self.fn_edit.text().strip()
            ln    = self.ln_edit.text().strip()
            email = self.email_edit.text().strip()
            pw    = self.pw_edit.text()
            pw2   = self.pw2_edit.text()

            if not fn or not email or not pw:
                QMessageBox.warning(self, "Реєстрація", "Заповніть обов'язкові поля.")
                return
            if pw != pw2:
                QMessageBox.warning(self, "Реєстрація", "Паролі не співпадають.")
                return
            if not auth_service.password_is_valid(pw):
                QMessageBox.warning(self, "Реєстрація", "Пароль не відповідає вимогам.")
                return
            if not self.terms_chk.isChecked():
                QMessageBox.warning(self, "Реєстрація", "Необхідно прийняти умови використання.")
                return

            ok, msg = auth_service.register_user(fn, ln, email, pw)
            if not ok:
                QMessageBox.warning(self, "Помилка реєстрації", msg)
                return

            QMessageBox.information(self, "Готово!", msg)
            _, _, user = auth_service.login_user(email, pw)
            if user:
                self.register_succeeded.emit(user)
            else:
                self.switch_login.emit()
        finally:
            self._busy = False
            self._reg_btn.setEnabled(True)


# ═══════════════════════════════ AUTH SCREEN ════════════════════════════════

class AuthScreen(QWidget):
    """
    Full-window auth screen: BrandPanel (left) + card with
    login/register stacked (right). Emits login_succeeded(user_dict)
    when the user logs in or registers, or guest_requested() when
    they click "Продовжити без входу".

    This widget is meant to be shown as a frameless top-level window;
    it draws its own titlebar (drag-to-move + minimize/maximize/close)
    since the OS chrome is disabled.
    """
    login_succeeded = pyqtSignal(dict)
    guest_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("authScreen")
        self.setStyleSheet("#authScreen { background:#07080f; }")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_titlebar())

        # ── one background canvas spans the *entire* window; the login
        # side simply shows a blurred/darkened crop of the same image
        # instead of an unrelated flat panel ─────────────────────────
        canvas = BrandCanvas(sharp_area_frac=0.66, darken_from_frac=0.55)
        canvas_v = QVBoxLayout(canvas)
        canvas_v.setContentsMargins(48, 28, 48, 24)
        canvas_v.setSpacing(0)

        middle_row = QHBoxLayout()
        middle_row.setSpacing(0)

        # left: feature text, centred vertically within its column
        text_wrap = QWidget()
        text_wrap.setStyleSheet("background:transparent;")
        text_v = QVBoxLayout(text_wrap)
        text_v.setContentsMargins(0, 0, 0, 0)
        text_v.addStretch(1)
        text_v.addWidget(_build_text_block())
        text_v.addStretch(1)
        middle_row.addWidget(text_wrap, 6)

        # right: the login/register card, centred both horizontally
        # and vertically within its column
        card = QFrame()
        card.setFixedWidth(580)
        card.setStyleSheet("""
            QFrame { background: rgba(13,15,28,242); border:1px solid rgba(255,255,255,25); border-radius:26px; }
        """)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 18)
        shadow.setColor(QColor(0, 0, 0, 160))
        card.setGraphicsEffect(shadow)

        self._stack = QStackedWidget(card)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.addWidget(self._stack)

        self._login_form    = LoginForm()
        self._register_form = RegisterForm()
        self._stack.addWidget(self._login_form)     # index 0
        self._stack.addWidget(self._register_form)  # index 1

        # cross-form navigation
        self._login_form.switch_register.connect(lambda: self._stack.setCurrentIndex(1))
        self._register_form.switch_login.connect(lambda: self._stack.setCurrentIndex(0))

        # propagate auth signals
        self._login_form.login_succeeded.connect(self.login_succeeded.emit)
        self._register_form.register_succeeded.connect(self.login_succeeded.emit)
        self._login_form.guest_requested.connect(self.guest_requested.emit)

        # pre-fill remembered email
        remembered = auth_service.get_remembered_user()
        if remembered:
            self._login_form.prefill(remembered["email"])

        card_wrap = QWidget()
        card_wrap.setStyleSheet("background:transparent;")
        card_v = QVBoxLayout(card_wrap)
        card_v.setContentsMargins(0, 0, 0, 0)
        card_v.addStretch(1)
        card_v.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        card_v.addStretch(1)
        middle_row.addWidget(card_wrap, 5)

        canvas_v.addLayout(middle_row, 1)

        # footer (left) + language selector (right), pinned to the bottom
        # and spanning the full width of the shared canvas
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(_build_footer_label())
        bottom_row.addStretch()
        self._lang_combo = QComboBox()
        self._lang_combo.addItems([f"🌐  {i18n.UK}", f"🌐  {i18n.EN}"])
        self._lang_combo.setFixedWidth(170)
        self._lang_combo.setStyleSheet("""
            QComboBox { background:#11131e; border:1px solid #252a3f; border-radius:8px;
                padding:8px 12px; color:#e7e9f3; font-size:12px; }
            QComboBox::drop-down { border:none; }
            QComboBox QAbstractItemView { background:#161a28; color:#e7e9f3;
                selection-background-color:#4F46E5; border:1px solid #252a3f; }
        """)
        self._lang_combo.setCurrentIndex(1 if i18n.get_language() == i18n.EN else 0)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        bottom_row.addWidget(self._lang_combo)
        canvas_v.addLayout(bottom_row)

        root.addWidget(canvas, 1)

    def _on_language_changed(self, index):
        import database as db
        lang = i18n.EN if index == 1 else i18n.UK
        db.set_setting("ui_language", lang)
        self._login_form.retranslate()
        self._register_form.retranslate()
        self._title_lbl.setText(i18n.t("app_title"))
        self.setWindowTitle(i18n.t("app_title"))

    def _build_titlebar(self):
        from ui.widgets import DraggableTitleBar
        bar = DraggableTitleBar(target_window=self)
        bar.setFixedHeight(44)
        bar.setStyleSheet("background:#07080f; border-bottom:1px solid #16192a;")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 10, 0)
        lay.setSpacing(8)

        icon_pix = _logo_pixmap("dota_logo.jpg", size=22, radius=6)
        icon = QLabel()
        if not icon_pix.isNull():
            icon.setFixedSize(22, 22)
            icon.setPixmap(icon_pix)
        else:
            icon.setText("⛨")
            icon.setStyleSheet("color:#e03030; font-size:16px; border:none; background:transparent;")
        lay.addWidget(icon)
        title = QLabel(i18n.t("app_title"))
        title.setStyleSheet("color:#c4c7d6; font-size:12px; font-weight:600; border:none; background:transparent;")
        lay.addWidget(title)
        self._title_lbl = title
        lay.addStretch()

        for sym, handler in (("—", lambda: self.window().showMinimized()),
                              ("□", self._toggle_max),
                              ("✕", lambda: self.window().close())):
            b = QPushButton(sym)
            b.setFixedSize(32, 28)
            b.setStyleSheet(
                "QPushButton{background:transparent;border:none;color:#8a8fa8;font-size:12px;}"
                "QPushButton:hover{background:#1a1d2c;border-radius:4px;color:#fff;}"
            )
            b.clicked.connect(handler)
            lay.addWidget(b)
        return bar

    def _toggle_max(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
        else:
            win.showMaximized()
