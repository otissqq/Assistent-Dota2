import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QLabel, QPushButton, QStackedWidget, QSizePolicy,
                              QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QGuiApplication, QShortcut, QKeySequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database as db
from ui.page_home import HomePage
from ui.page_history import HistoryPage, HistoryDialog
from ui.page_statistics import StatisticsPage
from ui.page_settings import SettingsPage
from ui.page_about import AboutPage
from ui.page_auth import AuthScreen
from ui import theme as theme_mod
from ui.style import generate_qss
from services import i18n, hotkey_service


class AppState:
    """Shared state: current logged-in user (or None for guest), plus a
    hook pages can call after Settings are saved so the chrome (theme,
    language, hotkey) updates immediately without restarting the app."""
    def __init__(self):
        self.user = None   # dict with id, first_name, last_name, email | None
        self.on_settings_changed = None
        self.on_logout = None


NAV_ITEMS = [
    ("home",     "home_icon.webp",        "🏠", "nav_home"),
    ("history",  "history_icon.webp",     "🕘", "nav_history"),
    ("stats",    "statistic_actual.png",  "📊", "nav_stats"),
    ("settings", "setting_icon.jpg",      "⚙",  "nav_settings"),
    ("about",    "info_icon.webp",        "ℹ", "nav_about"),
]


def _fit_geometry(default_w, default_h, min_w, min_h, margin_ratio=0.94):
    """Returns (w, h) that fit the primary screen's available geometry,
    so windows never open larger than the screen (which was cutting off
    buttons/content on smaller displays)."""
    screen = QGuiApplication.primaryScreen()
    avail = screen.availableGeometry() if screen else None
    if avail is None:
        return default_w, default_h
    w = min(default_w, int(avail.width() * margin_ratio))
    h = min(default_h, int(avail.height() * margin_ratio))
    w = max(w, min(min_w, avail.width()))
    h = max(h, min(min_h, avail.height()))
    return w, h


class MainWindow(QMainWindow):
    def __init__(self, app_state: AppState):
        super().__init__()
        self.setWindowTitle(i18n.t("app_title"))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        w, h = _fit_geometry(1536, 1024, 1180, 700)
        self.resize(w, h)
        self.setMinimumSize(1100, 650)
        self.app_state = app_state
        self.app_state.on_settings_changed = self._apply_settings_changes
        self.app_state.on_logout = self._logout
        self.nav_buttons = {}
        self._current_key = "home"
        self._qshortcut = None
        self._page_anim = None

        self._build_chrome()
        self._build_pages()
        self.set_active_page("home")
        self._register_hotkey()
        # Open maximized so every panel/button has room, regardless of the
        # window manager's default placement.
        self.showMaximized()

    # ---------------------------------------------------------------- chrome
    def _build_chrome(self):
        root = QWidget()
        root.setObjectName("root")
        root_layout_v = QVBoxLayout(root)
        root_layout_v.setContentsMargins(0, 0, 0, 0)
        root_layout_v.setSpacing(0)
        root_layout_v.addWidget(self._build_titlebar())

        body = QWidget()
        root_layout = QHBoxLayout(body)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())

        right_side = QVBoxLayout()
        right_side.setContentsMargins(0, 0, 0, 0)
        right_side.setSpacing(0)

        self.stack = QStackedWidget()
        right_side.addWidget(self.stack, 1)
        right_wrap = QWidget()
        right_wrap.setLayout(right_side)
        root_layout.addWidget(right_wrap, 1)

        root_layout_v.addWidget(body, 1)
        self.setCentralWidget(root)

    def _build_pages(self):
        self.pages = {}
        self.pages["home"]     = HomePage(self.app_state, on_open_history_item=self._open_history_item,
                                           on_open_stats_hero=self._open_stats_hero)
        self.pages["history"]  = HistoryPage(self.app_state)
        self.pages["stats"]    = StatisticsPage(self.app_state)
        self.pages["settings"] = SettingsPage(self.app_state)
        self.pages["about"]    = AboutPage(self.app_state)
        for key in ["home", "history", "stats", "settings", "about"]:
            self.stack.addWidget(self.pages[key])

    def _rebuild_pages(self):
        """Recreates every page so widgets built with make_card()/card_title()
        etc. pick up the (possibly just-changed) theme colours -- Qt has no
        way to retroactively re-run a widget's own setStyleSheet() calls."""
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()
        self._build_pages()
        self.set_active_page(self._current_key)

    # ---------------------------------------------------------------- titlebar
    def _build_titlebar(self):
        from ui.widgets import DraggableTitleBar
        t = theme_mod.current()
        bar = DraggableTitleBar(target_window=self)
        bar.setObjectName("titlebar")
        bar.setFixedHeight(56)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 8, 16, 8)

        self._title_lbl = QLabel(i18n.t("app_title"))
        self._title_lbl.setStyleSheet(f"color:{t['text_bright']}; font-size:14px; font-weight:700; border:none; background:transparent;")
        self._subtitle_lbl = QLabel(i18n.t("app_subtitle"))
        self._subtitle_lbl.setStyleSheet(f"color:{t['text_faint']}; font-size:10px; border:none; background:transparent;")
        title_box = QVBoxLayout(); title_box.setSpacing(0)
        title_box.addWidget(self._title_lbl)
        title_box.addWidget(self._subtitle_lbl)
        lay.addLayout(title_box)
        lay.addStretch()

        # user badge
        if self.app_state.user:
            u = self.app_state.user
            name = u.get("first_name") or u.get("email", "")
            user_lbl = QLabel(f"👤  {name}")
            user_lbl.setStyleSheet(f"color:{t['accent_soft']}; font-size:12px; font-weight:600; border:none; background:transparent;")
            lay.addWidget(user_lbl)
            lay.addSpacing(12)

            logout_btn = QPushButton(f"⏻  {i18n.t('logout')}")
            logout_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            logout_btn.setStyleSheet(f"""
                QPushButton {{ background:transparent; border:1px solid {t['border_input']}; border-radius:8px;
                    color:{t['text_muted']}; font-size:11px; font-weight:600; padding:6px 12px; }}
                QPushButton:hover {{ background:#3a1c29; border-color:#4a2233; color:#f0728a; }}
            """)
            logout_btn.clicked.connect(self._logout)
            lay.addWidget(logout_btn)
            lay.addSpacing(12)
        else:
            guest_lbl = QLabel(f"👤  {i18n.t('guest')}")
            guest_lbl.setStyleSheet(f"color:{t['text_ghost']}; font-size:12px; border:none; background:transparent;")
            lay.addWidget(guest_lbl)

            login_btn = QPushButton(f"⏻  {i18n.t('login_link')}")
            login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            login_btn.setStyleSheet(f"""
                QPushButton {{ background:transparent; border:1px solid {t['border_input']}; border-radius:8px;
                    color:{t['accent_soft']}; font-size:11px; font-weight:600; padding:6px 12px; }}
                QPushButton:hover {{ background:{t['surface_soft']}; }}
            """)
            login_btn.clicked.connect(self._logout)
            lay.addSpacing(12)
            lay.addWidget(login_btn)
            lay.addSpacing(12)

        for sym, handler in (("—", self.showMinimized), ("□", self._toggle_max), ("✕", self.close)):
            b = QPushButton(sym)
            b.setFixedSize(34, 30)
            b.setStyleSheet(
                f"QPushButton{{background:transparent;border:none;color:{t['text_muted']};font-size:13px;}}"
                f"QPushButton:hover{{background:{t['surface_soft']};border-radius:4px;}}"
            )
            b.clicked.connect(handler)
            lay.addWidget(b)
        return bar

    def _toggle_max(self):
        self.showNormal() if self.isMaximized() else self.showMaximized()

    def _logout(self):
        """Signs the current user out (clears 'remember me'), closes the
        main window and re-opens the login screen."""
        from services import auth_service
        auth_service.remember_user(None)
        hotkey_service.unregister()
        self.close()
        launch_auth_flow()

    # ---------------------------------------------------------------- sidebar
    def _build_sidebar(self):
        t = theme_mod.current()
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"#sidebar{{background-color:{t['sidebar']};border-right:1px solid {t['border']};}}")
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(8)

        from ui.widgets import icon_pixmap
        from PyQt6.QtGui import QIcon
        from PyQt6.QtCore import QSize
        for key, icon_file, emoji, label_key in NAV_ITEMS:
            btn = QPushButton(f"   {i18n.t(label_key)}")
            pix = icon_pixmap(icon_file, size=18, radius=4)
            if not pix.isNull():
                btn.setIcon(QIcon(pix))
                btn.setIconSize(QSize(18, 18))
            else:
                btn.setText(f"  {emoji}   {i18n.t(label_key)}")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setMinimumHeight(40)
            btn.setStyleSheet(self._nav_btn_style(False))
            btn.clicked.connect(lambda checked, k=key: self._on_nav_clicked(k))
            lay.addWidget(btn)
            self.nav_buttons[key] = btn

        lay.addStretch()

        # STRATZ status indicator -- reflects whether a key is actually
        # saved (previously this always showed "Підключено" in green,
        # regardless of whether STRATZ was configured at all).
        connected = bool(db.get_setting("stratz_api_key"))
        status_card = QWidget()
        status_card.setStyleSheet(f"background-color:{t['surface_soft']};border:1px solid {t['border_soft']};border-radius:10px;")
        sl = QHBoxLayout(status_card)
        sl.setContentsMargins(12, 10, 12, 10)
        dot = QLabel(); dot.setFixedSize(8, 8)
        dot.setStyleSheet(f"background-color:{t['green'] if connected else t.get('red', '#ef6f7a')};border-radius:4px;")
        sl.addWidget(dot)
        status_lbl = QLabel(i18n.t("stratz_connected") if connected else i18n.t("stratz_disconnected"))
        status_lbl.setStyleSheet(f"color:{t['text_dim']};font-size:11px;font-weight:600;border:none;background:transparent;")
        sl.addWidget(status_lbl)
        lay.addWidget(status_card)

        ver_lbl = QLabel("v1.0.0")
        ver_lbl.setStyleSheet(f"color:{t['text_ghost']};font-size:10px;border:none;background:transparent;")
        lay.addWidget(ver_lbl)
        return sidebar

    def _nav_btn_style(self, active):
        t = theme_mod.current()
        if active:
            return (f"QPushButton{{text-align:left;padding:10px 12px;border-radius:8px;"
                    f"background:{t['accent']};color:#fff;font-size:13px;font-weight:700;"
                    f"border:1.5px solid {t['accent']};}}")
        return (f"QPushButton{{text-align:left;padding:10px 12px;border-radius:8px;"
                f"background:transparent;color:{t['text_muted']};font-size:13px;"
                f"border:1px solid {t['border_input']};}}"
                f"QPushButton:hover{{background:{t['surface_soft']};color:{t['text_bright']};"
                f"border-color:{t['accent_soft']};}}")

    def _on_nav_clicked(self, key):
        if key == "history":
            # Uncheck immediately -- this opens a transient overlay, not a
            # persistent page, so the nav button shouldn't stay highlighted
            # after the dialog closes.
            self.nav_buttons["history"].setChecked(self._current_key == "history")
            self._open_history_dialog()
        else:
            self.set_active_page(key)

    def _open_history_dialog(self, record_id=None):
        dlg = HistoryDialog(self.app_state, parent=self)
        dlg.setWindowModality(Qt.WindowModality.ApplicationModal)
        if record_id is not None:
            dlg.select_record(record_id)
        dlg.destroyed.connect(self._on_history_dialog_closed)
        dlg.show()
        self._history_dialog = dlg  # keep a reference alive while it's open

    def _on_history_dialog_closed(self):
        # Called from the dialog's `destroyed` signal, which Qt may fire
        # quite late (including during teardown); guard against `self`'s
        # own widgets already being gone at that point.
        try:
            self.pages["home"].refresh_history_panel()
        except (RuntimeError, KeyError, AttributeError):
            pass

    def set_active_page(self, key):
        index_map = {"home": 0, "history": 1, "stats": 2, "settings": 3, "about": 4}
        self._current_key = key
        for k, btn in self.nav_buttons.items():
            btn.setChecked(k == key)
            btn.setStyleSheet(self._nav_btn_style(k == key))
        self.stack.setCurrentIndex(index_map[key])
        self._animate_page_in(self.stack.currentWidget())
        if key == "history":
            self.pages["history"].refresh()
        if key == "home":
            self.pages["home"].refresh_history_panel()

    def _animate_page_in(self, widget):
        """Gentle fade-in whenever the visible page changes, instead of the
        page just snapping into view."""
        if widget is None:
            return
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._page_anim = anim  # keep a reference alive until it finishes

    def _open_history_item(self, record_id):
        self._open_history_dialog(record_id=record_id)

    def _open_stats_hero(self, hero_name):
        """Instead of popping up a separate info dialog, a clicked Top-5
        recommendation now takes the user straight to that hero's full
        card on the Статистика page."""
        self.set_active_page("stats")
        self.pages["stats"].select_hero(hero_name)

    # ---------------------------------------------------------------- hotkey
    def _register_hotkey(self):
        hk = db.get_setting("screenshot_hotkey", "F8") or "F8"
        ok = hotkey_service.register(hk, self._on_global_hotkey)
        # In-app fallback (works while this window has focus) -- always
        # installed too, since the system-wide hook may be unavailable
        # (no `keyboard` package, sandboxed/headless env, no OS permission).
        if self._qshortcut is not None:
            self._qshortcut.setEnabled(False)
            self._qshortcut.deleteLater()
            self._qshortcut = None
        try:
            self._qshortcut = QShortcut(QKeySequence(hk), self)
            self._qshortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            self._qshortcut.activated.connect(self._on_global_hotkey)
        except Exception:
            self._qshortcut = None
        return ok

    def _on_global_hotkey(self):
        # `keyboard`'s hook fires on a background thread; hop back onto the
        # GUI thread via a queued single-shot before touching any widgets.
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._trigger_capture)

    def _trigger_capture(self):
        # Triggered by the global hotkey while the app is very likely *not*
        # the foreground window (the whole point is capturing whatever is
        # behind it, e.g. the game). Don't switch pages or raise/activate
        # this window first -- that would yank focus away from the game
        # right before the screenshot is taken. The home page's capture
        # routine itself decides whether it still needs to get out of the
        # way (see HomePage.on_capture_clicked).
        self.pages["home"].on_capture_clicked(from_hotkey=True)
        if self._current_key != "home":
            self.set_active_page("home")

    # ---------------------------------------------------------------- settings hook
    def _apply_settings_changes(self):
        """Called by SettingsPage right after it saves, so the hotkey,
        theme and language changes take effect immediately. Deferred by one
        event-loop tick because this is invoked from inside a click handler
        on a widget that this very method is about to destroy."""
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, self._do_apply_settings_changes)

    def _do_apply_settings_changes(self):
        self._register_hotkey()
        app = QApplication.instance()
        app.setStyleSheet(generate_qss(theme_mod.current()))
        central = self.centralWidget()
        if central is not None:
            self.setCentralWidget(QWidget())  # detach before deleting
            central.deleteLater()
        self.nav_buttons = {}
        self._build_chrome()
        self._rebuild_pages()

    def closeEvent(self, event):
        hotkey_service.unregister()
        super().closeEvent(event)


# ═══════════════════════════════ ENTRY POINT ════════════════════════════════

_refs = {}  # keep top-level windows alive (avoids GC closing frameless windows)


def launch_auth_flow():
    app_state = AppState()
    auth_screen = AuthScreen()
    auth_screen.setWindowTitle(i18n.t("app_title"))
    w, h = _fit_geometry(1340, 860, 1020, 680)
    auth_screen.resize(w, h)
    auth_screen.setMinimumSize(1000, 640)
    auth_screen.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    screen = QGuiApplication.primaryScreen()
    if screen:
        avail = screen.availableGeometry()
        auth_screen.move(avail.center() - auth_screen.rect().center())

    def on_login(user: dict):
        app_state.user = user
        auth_screen.hide()
        main_win = MainWindow(app_state)
        _refs["main_win"] = main_win
        main_win.show()

    def on_guest():
        app_state.user = None
        auth_screen.hide()
        main_win = MainWindow(app_state)
        _refs["main_win"] = main_win
        main_win.show()

    auth_screen.login_succeeded.connect(on_login)
    auth_screen.guest_requested.connect(on_guest)
    auth_screen.show()
    _refs["auth_screen"] = auth_screen


def main():
    db.init_db()
    app = QApplication(sys.argv)
    app.setStyleSheet(generate_qss(theme_mod.current()))

    launch_auth_flow()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
