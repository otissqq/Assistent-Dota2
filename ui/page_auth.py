"""
Authentication screen — two views stacked in a QStackedWidget:
  index 0 → LoginForm
  index 1 → RegisterForm

The left side paints an original dark-fantasy scene (same palette/mood as
the mockup) without reproducing licensed Dota 2 key-art. The right side is
a styled card that matches the mockup layout pixel-for-pixel.
"""
import math, random

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QCheckBox, QStackedWidget, QFrame, QComboBox, QMessageBox, QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QLinearGradient, QRadialGradient, QColor, QPen, QPolygonF

from services import auth_service


# ═══════════════════════════════ LEFT BRAND PANEL ═══════════════════════════

class BrandCanvas(QWidget):
    """Paints the dark-fantasy background in the same palette as the mockup."""
    def __init__(self, parent=None):
        super().__init__(parent)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # deep background
        bg = QLinearGradient(0, 0, w * 0.4, h)
        bg.setColorAt(0, QColor("#0b0e1a"))
        bg.setColorAt(1, QColor("#06070f"))
        p.fillRect(0, 0, w, h, bg)

        # red volcanic glow (bottom-right, like the lava in the mockup)
        rg = QRadialGradient(w * 0.8, h * 0.75, w * 0.55)
        rg.setColorAt(0, QColor(190, 45, 30, 140))
        rg.setColorAt(0.5, QColor(160, 30, 20, 60))
        rg.setColorAt(1, QColor(160, 30, 20, 0))
        p.setBrush(rg); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(QPointF(w * 0.8, h * 0.75), w * 0.55, w * 0.55)

        # cool purple glow (top-left, matches the obelisk glow)
        pg = QRadialGradient(w * 0.15, h * 0.25, w * 0.5)
        pg.setColorAt(0, QColor(90, 70, 210, 80))
        pg.setColorAt(1, QColor(90, 70, 210, 0))
        p.setBrush(pg)
        p.drawEllipse(QPointF(w * 0.15, h * 0.25), w * 0.5, w * 0.5)

        # obelisk silhouette (left column)
        ox = w * 0.17
        p.setBrush(QColor(18, 22, 40, 220))
        obelisk = QPolygonF([
            QPointF(ox - 36, h * 0.65), QPointF(ox - 28, h * 0.28),
            QPointF(ox, h * 0.14),
            QPointF(ox + 28, h * 0.28), QPointF(ox + 36, h * 0.65),
        ])
        p.drawPolygon(obelisk)
        # rune glow on obelisk
        rune = QRadialGradient(QPointF(ox, h * 0.32), 22)
        rune.setColorAt(0, QColor(160, 190, 255, 230))
        rune.setColorAt(1, QColor(160, 190, 255, 0))
        p.setBrush(rune)
        p.drawEllipse(QPointF(ox, h * 0.32), 22, 22)

        # rocky ground
        p.setBrush(QColor(12, 15, 25, 240))
        ground = QPolygonF([
            QPointF(0, h), QPointF(0, h * 0.83),
            QPointF(w * 0.25, h * 0.79), QPointF(w * 0.5, h * 0.87),
            QPointF(w, h * 0.81), QPointF(w, h),
        ])
        p.drawPolygon(ground)

        # runesword (centred right-area, same position as mockup)
        self._draw_sword(p, w * 0.63, h * 0.5, h * 0.58)

        # floating embers
        rng = random.Random(7)
        p.setPen(Qt.PenStyle.NoPen)
        for _ in range(30):
            ex = rng.uniform(0, w)
            ey = rng.uniform(h * 0.25, h * 0.9)
            r  = rng.uniform(0.9, 2.4)
            a  = rng.randint(40, 160)
            p.setBrush(QColor(255, 140, 80, a))
            p.drawEllipse(QPointF(ex, ey), r, r)
        p.end()

    def _draw_sword(self, p, cx, cy, blade_len):
        angle = math.radians(-54)
        dx, dy = math.cos(angle), math.sin(angle)
        tip  = QPointF(cx + dx * blade_len * 0.55, cy + dy * blade_len * 0.55)
        hilt = QPointF(cx - dx * blade_len * 0.28, cy - dy * blade_len * 0.28)

        # tip glow
        glow = QRadialGradient(tip, 80)
        glow.setColorAt(0, QColor(160, 120, 255, 120))
        glow.setColorAt(1, QColor(160, 120, 255, 0))
        p.setBrush(glow); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(tip, 80, 80)

        perp = QPointF(-dy, dx)
        bw = 10
        blade = QPolygonF([
            QPointF(hilt.x() + perp.x() * bw, hilt.y() + perp.y() * bw),
            tip,
            QPointF(hilt.x() - perp.x() * bw, hilt.y() - perp.y() * bw),
        ])
        grad = QLinearGradient(hilt, tip)
        grad.setColorAt(0, QColor(220, 210, 255, 240))
        grad.setColorAt(1, QColor(180, 140, 255, 255))
        p.setBrush(grad)
        p.drawPolygon(blade)

        # crossguard
        g = QPointF(perp.x() * 24, perp.y() * 24)
        p.setPen(QPen(QColor(80, 60, 140), 6))
        p.drawLine(QPointF(hilt.x() + g.x(), hilt.y() + g.y()),
                   QPointF(hilt.x() - g.x(), hilt.y() - g.y()))
        # handle
        he = QPointF(hilt.x() - dx * 38, hilt.y() - dy * 38)
        p.setPen(QPen(QColor(55, 40, 85), 8))
        p.drawLine(hilt, he)


def _feature_item(icon, bg_color, title, subtitle):
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(14)
    icon_box = QLabel(icon)
    icon_box.setFixedSize(42, 42)
    icon_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon_box.setStyleSheet(f"background:{bg_color}; border-radius:10px; font-size:17px;")
    lay.addWidget(icon_box)
    txt = QVBoxLayout(); txt.setSpacing(2)
    t = QLabel(title)
    t.setStyleSheet("color:#fff; font-weight:700; font-size:13px; border:none; background:transparent;")
    s = QLabel(subtitle)
    s.setWordWrap(True)
    s.setStyleSheet("color:#8a8fa8; font-size:11px; border:none; background:transparent;")
    s.setMaximumWidth(290)
    txt.addWidget(t); txt.addWidget(s)
    lay.addLayout(txt, 1)
    return w


class BrandPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(480)
        canvas = BrandCanvas()
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        overlay_layout = QVBoxLayout(canvas)
        overlay_layout.setContentsMargins(64, 80, 56, 50)
        overlay_layout.setSpacing(20)

        title = QLabel("Інтелектуальний помічник\nдля аналізу драфту")
        title.setStyleSheet("color:#fff; font-size:29px; font-weight:800; border:none; background:transparent;")
        overlay_layout.addWidget(title)

        dota_lbl = QLabel("Dota 2")
        dota_lbl.setStyleSheet("color:#9d90f5; font-size:29px; font-weight:800; border:none; background:transparent;")
        overlay_layout.addWidget(dota_lbl)

        tagline = QLabel("Аналізуй драфт. Обирай найкраще. Перемагай.")
        tagline.setStyleSheet("color:#aeb2c4; font-size:13px; border:none; background:transparent;")
        overlay_layout.addWidget(tagline)

        overlay_layout.addSpacing(24)
        overlay_layout.addWidget(_feature_item("🎯", "#1e1a3a", "Розпізнавання героїв",
                                                "Автоматичне визначення героїв зі скриншота драфту"))
        overlay_layout.addWidget(_feature_item("🛡", "#152818", "Аналіз драфту",
                                                "Контрпіки, синергії, мета та оцінка сили команд"))
        overlay_layout.addWidget(_feature_item("⭐", "#2a2010", "Рекомендації від ШІ",
                                                "ТОП-5 героїв для вибору з поясненнями"))
        overlay_layout.addWidget(_feature_item("📊", "#102030", "Актуальна статистика",
                                                "Дані з STRATZ API для точного аналізу"))
        overlay_layout.addStretch()

        footer_row = QHBoxLayout()
        copy = QLabel("© 2026. Всі права захищені.")
        copy.setStyleSheet("color:#4a4f66; font-size:11px; border:none; background:transparent;")
        footer_row.addWidget(copy)
        footer_row.addStretch()
        overlay_layout.addLayout(footer_row)

        outer.addWidget(canvas)


# ═══════════════════════════════ SHARED FORM HELPERS ═══════════════════════

def _input_field(placeholder, icon="", password=False):
    """Returns (wrapper_widget, QLineEdit)."""
    wrap = QFrame()
    wrap.setMinimumHeight(48)
    wrap.setStyleSheet("""
        QFrame { background:#11131e; border:1px solid #252a3f; border-radius:10px; }
        QFrame:focus-within { border:1px solid #6c5ce7; }
    """)
    lay = QHBoxLayout(wrap)
    lay.setContentsMargins(14, 0, 10, 0)
    lay.setSpacing(10)
    if icon:
        ic = QLabel(icon)
        ic.setStyleSheet("border:none; background:transparent; color:#6c7085; font-size:14px;")
        lay.addWidget(ic)
    edit = QLineEdit()
    edit.setPlaceholderText(placeholder)
    edit.setStyleSheet("""
        QLineEdit { border:none; background:transparent; color:#e7e9f3; font-size:13px; padding:12px 0; }
    """)
    if password:
        edit.setEchoMode(QLineEdit.EchoMode.Password)
    lay.addWidget(edit, 1)
    if password:
        eye = QPushButton("👁")
        eye.setFixedSize(30, 30)
        eye.setStyleSheet("QPushButton{background:transparent;border:none;color:#6c7085;} QPushButton:hover{color:#fff;}")
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
    b = QPushButton(text)
    b.setMinimumHeight(46)
    b.setStyleSheet("""
        QPushButton { background:#6c5ce7; color:#fff; border-radius:10px; font-weight:700;
            font-size:14px; border:none; }
        QPushButton:hover { background:#7b6cf0; }
        QPushButton:pressed { background:#5d4fd1; }
    """)
    return b


def _ghost_btn(text):
    b = QPushButton(text)
    b.setMinimumHeight(44)
    b.setStyleSheet("""
        QPushButton { background:transparent; color:#e7e9f3; border:1px solid #252a3f;
            border-radius:10px; font-weight:600; font-size:13px; }
        QPushButton:hover { background:#161a28; }
    """)
    return b


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
        lay.setContentsMargins(58, 50, 58, 44)
        lay.setSpacing(16)

        # Dota logo icon (approximated with text)
        logo_lbl = QLabel("⛨")
        logo_lbl.setStyleSheet("font-size:52px; color:#e03030; border:none; background:transparent;")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo_lbl)

        title = QLabel("Вхід у програму")
        title.setStyleSheet("color:#fff; font-size:22px; font-weight:800; border:none; background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        sub = QLabel("Користуйтесь усіма можливостями\nінтелектуального аналізу драфту")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color:#8a8fa8; font-size:12px; border:none; background:transparent;")
        lay.addWidget(sub)

        lay.addSpacing(4)

        id_wrap, self.id_edit = _input_field("Ім'я користувача або Email", "👤")
        lay.addWidget(id_wrap)

        pw_wrap, self.pw_edit = _input_field("Пароль", "🔒", password=True)
        lay.addWidget(pw_wrap)

        rem_row = QHBoxLayout()
        self.remember_chk = QCheckBox("Запам'ятати мене")
        self.remember_chk.setChecked(True)
        self.remember_chk.setStyleSheet("""
            QCheckBox { color:#c4c7d6; font-size:12px; spacing:8px; }
            QCheckBox::indicator { width:17px; height:17px; border-radius:5px;
                background:#11131e; border:1px solid #2a2f45; }
            QCheckBox::indicator:checked { background:#6c5ce7; border:1px solid #6c5ce7; }
        """)
        rem_row.addWidget(self.remember_chk)
        rem_row.addStretch()
        lay.addLayout(rem_row)

        login_btn = _primary_btn("Увійти")
        login_btn.clicked.connect(self._on_login)
        lay.addWidget(login_btn)

        lay.addLayout(_or_divider())

        guest_btn = _ghost_btn("👤   Продовжити без входу")
        guest_btn.clicked.connect(self.guest_requested.emit)
        lay.addWidget(guest_btn)

        bottom = QHBoxLayout()
        reg_link = _link_btn("👤+   Створити акаунт")
        reg_link.clicked.connect(self.switch_register.emit)
        forgot_link = _link_btn("🔒   Забули пароль?")
        forgot_link.clicked.connect(self._on_forgot)
        bottom.addWidget(reg_link)
        bottom.addStretch()
        bottom.addWidget(forgot_link)
        lay.addLayout(bottom)

        lay.addStretch()

    def prefill(self, email: str):
        self.id_edit.setText(email)

    def _on_forgot(self):
        QMessageBox.information(self, "Відновлення паролю",
                                 "Ця функція потребує поштового сервісу і буде доступна "
                                 "в наступному оновленні.")

    def _on_login(self):
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


# ═══════════════════════════════ REGISTER FORM ═══════════════════════════════

class RegisterForm(QWidget):
    register_succeeded = pyqtSignal(dict)
    switch_login       = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(58, 36, 58, 32)
        lay.setSpacing(12)

        logo_lbl = QLabel("👤+")
        logo_lbl.setStyleSheet("font-size:36px; color:#9d90f5; border:none; background:transparent;")
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo_lbl)

        title = QLabel("Створення акаунту")
        title.setStyleSheet("color:#fff; font-size:21px; font-weight:800; border:none; background:transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        sub = QLabel("Зареєструйтесь, щоб отримати доступ до\nвсіх можливостей програми")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color:#8a8fa8; font-size:12px; border:none; background:transparent;")
        lay.addWidget(sub)

        # name row
        name_row = QHBoxLayout(); name_row.setSpacing(12)
        fn_wrap, self.fn_edit = _input_field("Ім'я", "👤")
        ln_wrap, self.ln_edit = _input_field("Прізвище", "👤")
        name_row.addWidget(fn_wrap, 1)
        name_row.addWidget(ln_wrap, 1)
        lay.addLayout(name_row)

        email_wrap, self.email_edit = _input_field("Email", "✉")
        lay.addWidget(email_wrap)

        pw_wrap, self.pw_edit   = _input_field("Пароль", "🔒", password=True)
        pw2_wrap, self.pw2_edit = _input_field("Підтвердіть пароль", "🔒", password=True)
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
        self.terms_chk = QCheckBox()
        self.terms_chk.setStyleSheet("""
            QCheckBox::indicator { width:17px; height:17px; border-radius:5px;
                background:#11131e; border:1px solid #2a2f45; }
            QCheckBox::indicator:checked { background:#6c5ce7; border:1px solid #6c5ce7; }
        """)
        terms_lbl = QLabel(
            'Я приймаю <span style="color:#9d90f5; font-weight:600;">Умови використання</span>'
            ' та <span style="color:#9d90f5; font-weight:600;">Політику конфіденційності</span>'
        )
        terms_lbl.setStyleSheet("color:#8a8fa8; font-size:11px; border:none; background:transparent;")
        terms_lbl.setWordWrap(True)
        terms_row.addWidget(self.terms_chk)
        terms_row.addWidget(terms_lbl, 1)
        lay.addLayout(terms_row)

        reg_btn = _primary_btn("Зареєструватися")
        reg_btn.clicked.connect(self._on_register)
        lay.addWidget(reg_btn)

        lay.addLayout(_or_divider())

        google_btn = _ghost_btn("🌐   Продовжити з Google")
        google_btn.clicked.connect(lambda: QMessageBox.information(
            self, "Google OAuth",
            "Вхід через Google потребує реєстрації OAuth-клієнта "
            "і буде доступний у production-збірці."))
        lay.addWidget(google_btn)

        bottom = QHBoxLayout()
        bottom.addStretch()
        have_lbl = QLabel("Вже маєте акаунт? ")
        have_lbl.setStyleSheet("color:#8a8fa8; font-size:12px; border:none; background:transparent;")
        login_link = _link_btn("Увійти")
        login_link.clicked.connect(self.switch_login.emit)
        bottom.addWidget(have_lbl)
        bottom.addWidget(login_link)
        bottom.addStretch()
        lay.addLayout(bottom)

        lay.addStretch()

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

    def _on_register(self):
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


# ═══════════════════════════════ AUTH SCREEN ════════════════════════════════

class AuthScreen(QWidget):
    """
    Full-window auth screen: BrandPanel (left) + card with
    login/register stacked (right). Emits login_succeeded(user_dict)
    when the user logs in or registers, or guest_requested() when
    they click "Продовжити без входу".
    """
    login_succeeded = pyqtSignal(dict)
    guest_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("authScreen")
        self.setStyleSheet("#authScreen { background:#07080f; }")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── left brand ──────────────────────────────────────────────
        outer.addWidget(BrandPanel(), 1)

        # ── right: card centred in a dark column ────────────────────
        right_col = QWidget()
        right_col.setStyleSheet("background:#07080f;")
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(40, 0, 40, 0)

        card = QFrame()
        card.setFixedWidth(560)
        card.setStyleSheet("""
            QFrame { background:#0f1120; border:1px solid #1e2235; border-radius:16px; }
        """)

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

        right_layout.addStretch()
        right_layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignHCenter)
        right_layout.addStretch()

        # language selector at bottom
        lang_row = QHBoxLayout()
        lang_row.addStretch()
        lang_combo = QComboBox()
        lang_combo.addItems(["🌐  Українська", "🌐  English"])
        lang_combo.setFixedWidth(170)
        lang_combo.setStyleSheet("""
            QComboBox { background:#11131e; border:1px solid #252a3f; border-radius:8px;
                padding:8px 12px; color:#e7e9f3; font-size:12px; }
            QComboBox::drop-down { border:none; }
        """)
        lang_row.addWidget(lang_combo)
        right_layout.addLayout(lang_row)
        right_layout.addSpacing(20)

        outer.addWidget(right_col, 1)
