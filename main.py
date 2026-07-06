import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QStackedWidget, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db
from ui.page_home import HomePage
from ui.page_history import HistoryPage
from ui.page_statistics import StatisticsPage
from ui.page_settings import SettingsPage
from ui.page_about import AboutPage
from ui.page_auth import AuthScreen


class AppState:
    """Shared state: current logged-in user (or None for guest)."""
    def __init__(self):
        self.user = None   # dict with id, first_name, last_name, email | None


NAV_ITEMS = [
    ("home",     "🏠", "Головна"),
    ("history",  "🕘", "Історія аналізів"),
    ("stats",    "📊", "Статистика"),
    ("settings", "⚙",  "Налаштування"),
    ("about",    "ℹ",  "Про програму"),
]


class MainWindow(QMainWindow):
    def __init__(self, app_state: AppState):
        super().__init__()
        self.setWindowTitle("Інтелектуальний помічник для аналізу драфту Dota 2")
        self.resize(1536, 1024)
        self.app_state = app_state
        self.nav_buttons = {}

        root = QWidget()
        root.setObjectName("root")
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())

        right_side = QVBoxLayout()
        right_side.setContentsMargins(0, 0, 0, 0)
        right_side.setSpacing(0)
        right_side.addWidget(self._build_titlebar())

        self.stack = QStackedWidget()
        self.pages = {}
        self.pages["home"]     = HomePage(self.app_state, on_open_history_item=self._open_history_item)
        self.pages["history"]  = HistoryPage(self.app_state)
        self.pages["stats"]    = StatisticsPage(self.app_state)
        self.pages["settings"] = SettingsPage(self.app_state)
        self.pages["about"]    = AboutPage(self.app_state)
        for key in ["home", "history", "stats", "settings", "about"]:
            self.stack.addWidget(self.pages[key])

        right_side.addWidget(self.stack, 1)
        right_wrap = QWidget()
        right_wrap.setLayout(right_side)
        root_layout.addWidget(right_wrap, 1)

        self.setCentralWidget(root)
        self.set_active_page("home")

    # ---------------------------------------------------------------- titlebar
    def _build_titlebar(self):
        bar = QWidget()
        bar.setFixedHeight(56)
        bar.setStyleSheet("background-color:#0c0e16; border-bottom:1px solid #1d2030;")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 8, 16, 8)

        title = QLabel("Інтелектуальний помічник для аналізу драфту Dota 2")
        title.setStyleSheet("color:#fff; font-size:14px; font-weight:700; border:none; background:transparent;")
        sub = QLabel("Аналізуй. Обирай. Перемагай.")
        sub.setStyleSheet("color:#7c8096; font-size:10px; border:none; background:transparent;")
        title_box = QVBoxLayout(); title_box.setSpacing(0)
        title_box.addWidget(title)
        title_box.addWidget(sub)
        lay.addLayout(title_box)
        lay.addStretch()

        # user badge
        if self.app_state.user:
            u = self.app_state.user
            name = u.get("first_name") or u.get("email", "")
            user_lbl = QLabel(f"👤  {name}")
            user_lbl.setStyleSheet("color:#9d90f5; font-size:12px; font-weight:600; border:none; background:transparent;")
            lay.addWidget(user_lbl)
            lay.addSpacing(12)
        else:
            guest_lbl = QLabel("👤  Гість")
            guest_lbl.setStyleSheet("color:#5a5f78; font-size:12px; border:none; background:transparent;")
            lay.addWidget(guest_lbl)
            lay.addSpacing(12)

        for sym, handler in (("—", self.showMinimized), ("□", self._toggle_max), ("✕", self.close)):
            b = QPushButton(sym)
            b.setFixedSize(34, 30)
            b.setStyleSheet(
                "QPushButton{background:transparent;border:none;color:#aeb2c4;font-size:13px;}"
                "QPushButton:hover{background:#1a1d2c;border-radius:4px;}"
            )
            b.clicked.connect(handler)
            lay.addWidget(b)
        return bar

    def _toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    # ---------------------------------------------------------------- sidebar
    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet("#sidebar{background-color:#11131e;border-right:1px solid #1d2030;}")
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(14, 18, 14, 14)
        lay.setSpacing(6)

        logo_row = QHBoxLayout()
        logo = QLabel("🛡")
        logo.setStyleSheet("font-size:22px;border:none;background:transparent;")
        logo_row.addWidget(logo)
        t = QLabel("Dota Draft\nAssistant")
        t.setStyleSheet("color:#fff;font-size:13px;font-weight:800;border:none;background:transparent;")
        logo_row.addWidget(t)
        logo_row.addStretch()
        lay.addLayout(logo_row)
        lay.addSpacing(14)

        for key, icon, label in NAV_ITEMS:
            btn = QPushButton(f"  {icon}   {label}")
            btn.setCheckable(True)
            btn.setStyleSheet(self._nav_btn_style(False))
            btn.clicked.connect(lambda checked, k=key: self.set_active_page(k))
            lay.addWidget(btn)
            self.nav_buttons[key] = btn

        lay.addStretch()

        # STRATZ status indicator
        status_card = QWidget()
        status_card.setStyleSheet("background-color:#161a28;border:1px solid #232739;border-radius:10px;")
        sl = QHBoxLayout(status_card)
        sl.setContentsMargins(12, 10, 12, 10)
        dot = QLabel(); dot.setFixedSize(8, 8)
        dot.setStyleSheet("background-color:#5ee08a;border-radius:4px;")
        sl.addWidget(dot)
        sl.addWidget(QLabel("Підключено\nSTRATZ API",
                             styleSheet="color:#bfead0;font-size:11px;font-weight:600;border:none;background:transparent;"))
        lay.addWidget(status_card)

        lay.addWidget(QLabel("v1.0.0",
                              styleSheet="color:#5a5f78;font-size:10px;border:none;background:transparent;"))
        return sidebar

    def _nav_btn_style(self, active):
        if active:
            return ("QPushButton{text-align:left;padding:10px 12px;border-radius:8px;"
                    "background:#2c2768;color:#fff;font-size:13px;font-weight:700;border:none;}")
        return ("QPushButton{text-align:left;padding:10px 12px;border-radius:8px;"
                "background:transparent;color:#aeb2c4;font-size:13px;border:none;}"
                "QPushButton:hover{background:#1a1d2c;color:#fff;}")

    def set_active_page(self, key):
        index_map = {"home": 0, "history": 1, "stats": 2, "settings": 3, "about": 4}
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
            btn.setStyleSheet(self._nav_btn_style(k == key))
        self.stack.setCurrentIndex(index_map[key])
        if key == "history":
            self.pages["history"].refresh()
        if key == "home":
            self.pages["home"].refresh_history_panel()

    def _open_history_item(self, record_id):
        self.set_active_page("history")
        hist_page = self.pages["history"]
        hist_page.selected_id = record_id
        rec = db.get_analysis(record_id)
        if rec:
            hist_page._render_detail(rec)


# ═══════════════════════════════ ENTRY POINT ════════════════════════════════

def main():
    db.init_db()
    app = QApplication(sys.argv)

    qss_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "style.qss")
    with open(qss_path, "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    app_state = AppState()

    # ── show auth screen first ───────────────────────────────────────
    auth_screen = AuthScreen()
    auth_screen.setWindowTitle("Інтелектуальний помічник для аналізу драфту Dota 2")
    auth_screen.resize(1340, 860)
    auth_screen.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    main_win = None

    def on_login(user: dict):
        nonlocal main_win
        app_state.user = user
        auth_screen.hide()
        main_win = MainWindow(app_state)
        main_win.show()

    def on_guest():
        nonlocal main_win
        app_state.user = None
        auth_screen.hide()
        main_win = MainWindow(app_state)
        main_win.show()

    auth_screen.login_succeeded.connect(on_login)
    auth_screen.guest_requested.connect(on_guest)
    auth_screen.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
