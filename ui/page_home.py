import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QFileDialog, QScrollArea, QGridLayout, QFrame, QSizePolicy,
                              QListWidget, QListWidgetItem, QMessageBox, QStackedLayout, QInputDialog)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap, QIcon

from ui.widgets import (make_card, card_title, small_label, body_label, pill, HeroChip,
                         hero_pixmap, hero_pixmap_full, round_pixmap, AnimatedButton, load_pixmap,
                         icon_label)
import database as db
from services import vision_service, screenshot_service, analysis_engine, gemini_service
from data.heroes_data import HERO_BY_NAME

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _side_icon(filename, size=18):
    pix = load_pixmap(os.path.join(ASSETS_DIR, filename))
    if pix.isNull():
        return None
    pix = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                      Qt.TransformationMode.SmoothTransformation)
    x = max(0, (pix.width() - size) // 2)
    y = max(0, (pix.height() - size) // 2)
    return QIcon(pix.copy(x, y, size, size))


class HomePage(QWidget):
    def __init__(self, app_state, on_open_history_item=None, on_open_stats_hero=None, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.on_open_history_item = on_open_history_item
        self.on_open_stats_hero = on_open_stats_hero
        self.side = "Radiant"
        self.screenshot_path = None
        self.ally_heroes = []
        self.enemy_heroes = []
        self.last_analysis = None
        self._build_ui()
        self.refresh_history_panel()

    # ---------------------------------------------------------- UI BUILD
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(18)

        # ---- Top toolbar ----
        toolbar_card = make_card()
        toolbar_card.setStyleSheet(toolbar_card.styleSheet() + "QFrame{border-radius:16px;}")
        toolbar = QHBoxLayout(toolbar_card)
        toolbar.setContentsMargins(18, 16, 18, 16)
        toolbar.setSpacing(14)

        self.btn_upload = QPushButton("  Обрати файл")
        self.btn_upload.setProperty("class", "secondary")
        self.btn_upload.setStyleSheet(self._secondary_style())
        upload_icon = _side_icon("upload_screen.png", size=20)
        if upload_icon:
            self.btn_upload.setIcon(upload_icon)
            self.btn_upload.setIconSize(QSize(20, 20))
        else:
            self.btn_upload.setText("⬆  Обрати файл")
        self.btn_upload.clicked.connect(self._upload_from_file)
        self.btn_upload.setMinimumHeight(56)
        toolbar.addWidget(self.btn_upload)
        toolbar.setAlignment(self.btn_upload, Qt.AlignmentFlag.AlignBottom)

        self.btn_clipboard = QPushButton("  З буфера")
        self.btn_clipboard.setProperty("class", "secondary")
        self.btn_clipboard.setStyleSheet(self._secondary_style())
        self.btn_clipboard.clicked.connect(self._upload_from_clipboard)
        self.btn_clipboard.setMinimumHeight(56)
        toolbar.addWidget(self.btn_clipboard)
        toolbar.setAlignment(self.btn_clipboard, Qt.AlignmentFlag.AlignBottom)

        self.btn_capture = QPushButton("  Створити скриншот")
        self.btn_capture.setProperty("class", "secondary")
        self.btn_capture.setStyleSheet(self._secondary_style())
        capture_icon = _side_icon("create_screen.png", size=20)
        if capture_icon:
            self.btn_capture.setIcon(capture_icon)
            self.btn_capture.setIconSize(QSize(20, 20))
        else:
            self.btn_capture.setText("⧉  Створити скриншот")
        self.btn_capture.clicked.connect(lambda: self.on_capture_clicked(False))
        self.btn_capture.setMinimumHeight(56)
        toolbar.addWidget(self.btn_capture)
        toolbar.setAlignment(self.btn_capture, Qt.AlignmentFlag.AlignBottom)

        toolbar.addStretch()

        side_box = QVBoxLayout()
        side_label = small_label("Виберіть сторону")
        side_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        side_box.addWidget(side_label)
        side_row = QHBoxLayout()
        side_row.setSpacing(6)
        self.btn_radiant = QPushButton(" Radiant")
        self.btn_dire = QPushButton(" Dire")
        radiant_icon = _side_icon("radiant_logo.jpeg")
        dire_icon = _side_icon("dire_logo.jpeg")
        if radiant_icon:
            self.btn_radiant.setIcon(radiant_icon)
            self.btn_radiant.setIconSize(QSize(18, 18))
        else:
            self.btn_radiant.setText("🌿 Radiant")
        if dire_icon:
            self.btn_dire.setIcon(dire_icon)
            self.btn_dire.setIconSize(QSize(18, 18))
        else:
            self.btn_dire.setText("👹 Dire")
        self.btn_radiant.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dire.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_radiant.clicked.connect(lambda: self.set_side("Radiant"))
        self.btn_dire.clicked.connect(lambda: self.set_side("Dire"))
        side_row.addWidget(self.btn_radiant)
        side_row.addWidget(self.btn_dire)
        side_box.addLayout(side_row)
        toolbar.addLayout(side_box)
        toolbar.setAlignment(side_box, Qt.AlignmentFlag.AlignBottom)

        self.btn_analyze = AnimatedButton("✨  Почати аналіз\nАналіз займе до 5 секунд",
                                           radius=10, text_color="white",
                                           extra_css="QPushButton{text-align:left;padding:6px 22px;}")
        self.btn_analyze.setMinimumHeight(56)
        self.btn_analyze.setMinimumWidth(220)
        self.btn_analyze.clicked.connect(self.on_analyze_clicked)
        toolbar.addWidget(self.btn_analyze)
        toolbar.setAlignment(self.btn_analyze, Qt.AlignmentFlag.AlignBottom)

        outer.addWidget(toolbar_card)

        # ---- Main 3-column body ----
        body = QHBoxLayout()
        body.setSpacing(16)

        # LEFT column (recognized heroes + draft analysis)
        left_col = QVBoxLayout()
        left_col.setSpacing(16)
        left_col.addWidget(self._build_recognized_card())
        self.update_side_buttons()
        left_col.addWidget(self._build_draft_analysis_card())
        left_col.addStretch()
        left_wrap = QWidget(); left_wrap.setLayout(left_col)
        left_wrap.setFixedWidth(500)

        # MIDDLE column (recommendations + AI explanation)
        mid_col = QVBoxLayout()
        mid_col.setSpacing(16)
        mid_col.addWidget(self._build_meta_card())
        mid_col.addWidget(self._build_recommendations_card())
        mid_col.addWidget(self._build_ai_card())
        mid_wrap = QWidget(); mid_wrap.setLayout(mid_col)

        # RIGHT column (history) -- wider and taller so entries + hero
        # thumbnails have room to breathe instead of being squeezed
        right_wrap = self._build_history_panel()
        right_wrap.setFixedWidth(330)

        body.addWidget(left_wrap)
        body.addWidget(mid_wrap, 1)
        body.addWidget(right_wrap)
        body.setAlignment(left_wrap, Qt.AlignmentFlag.AlignTop)
        body.setAlignment(mid_wrap, Qt.AlignmentFlag.AlignTop)
        body.setAlignment(right_wrap, Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(self._wrap(body))
        outer.addWidget(scroll, 1)

    def _wrap(self, layout):
        w = QWidget()
        w.setLayout(layout)
        return w

    def _bullet_row(self, icon, text, icon_color, text_color):
        row = QHBoxLayout()
        row.setSpacing(10)
        row.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(icon)
        icon_lbl.setFixedWidth(16)
        icon_lbl.setStyleSheet(f"color:{icon_color}; font-weight:800; font-size:12px; border:none; background:transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        row.addWidget(icon_lbl, 0, Qt.AlignmentFlag.AlignTop)
        text_lbl = body_label(text, color=text_color, size=12)
        text_lbl.setStyleSheet(f"font-size:12px; color:{text_color}; border:none; background:transparent;")
        row.addWidget(text_lbl, 1, Qt.AlignmentFlag.AlignTop)
        holder = QWidget()
        holder.setLayout(row)
        return holder

    def _secondary_style(self):
        return """
            QPushButton { background-color: #181c2c; color: #e7e9f3; border-radius: 8px;
                padding: 10px 16px; border: 1px solid #2a2f45; font-weight: 600; }
            QPushButton:hover { background-color: #20253a; border-color: #393f5c; }
        """

    # ---------------------------------------------------------- CARD BUILDERS
    def _build_recognized_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)
        lay.addWidget(card_title("Розпізнані герої", "detect_heroes.webp"))

        ally_head = QHBoxLayout()
        self.ally_title = small_label("Ваша команда (Radiant)")
        ally_head.addWidget(self.ally_title)
        ally_head.addStretch()
        self.btn_add_ally = QPushButton("+ Додати героя")
        self.btn_add_ally.setStyleSheet(self._secondary_style())
        self.btn_add_ally.clicked.connect(lambda: self._manual_add_hero("ally"))
        ally_head.addWidget(self.btn_add_ally)
        lay.addLayout(ally_head)

        self.ally_row = QHBoxLayout()
        self.ally_row.setSpacing(10)
        ally_holder = QWidget(); ally_holder.setLayout(self.ally_row)
        lay.addWidget(ally_holder)

        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background-color:#1f2436; border:none;")
        lay.addWidget(line)

        enemy_head = QHBoxLayout()
        self.enemy_title = small_label("Команда суперника (Dire)")
        enemy_head.addWidget(self.enemy_title)
        enemy_head.addStretch()
        self.btn_add_enemy = QPushButton("+ Додати героя")
        self.btn_add_enemy.setStyleSheet(self._secondary_style())
        self.btn_add_enemy.clicked.connect(lambda: self._manual_add_hero("enemy"))
        enemy_head.addWidget(self.btn_add_enemy)
        lay.addLayout(enemy_head)

        self.enemy_row = QHBoxLayout()
        self.enemy_row.setSpacing(10)
        enemy_holder = QWidget(); enemy_holder.setLayout(self.enemy_row)
        lay.addWidget(enemy_holder)

        self._render_placeholder_heroes()
        return card

    def _render_placeholder_heroes(self):
        for row in (self.ally_row, self.enemy_row):
            while row.count():
                item = row.takeAt(0)
                if item.widget():
                    w = item.widget()
                    w.setParent(None)
                    w.deleteLater()
        if not self.ally_heroes:
            lbl = small_label("Завантажте скриншот, щоб розпізнати героїв")
            self.ally_row.addWidget(lbl)
        else:
            for name in self.ally_heroes:
                self.ally_row.addWidget(HeroChip(name, square=True, size=64))
        if self.enemy_heroes:
            for name in self.enemy_heroes:
                self.enemy_row.addWidget(HeroChip(name, square=True, size=64))
        else:
            self.enemy_row.addWidget(small_label("—"))


    def _manual_add_hero(self, team_type):
        all_names = sorted(HERO_BY_NAME.keys())
        name, ok = QInputDialog.getItem(self, "Додати героя вручну", "Оберіть героя:", all_names, 0, False)
        if not ok or not name:
            return
        if name in self.ally_heroes or name in self.enemy_heroes:
            QMessageBox.information(self, "Герой вже є", f"{name} вже доданий у драфт.")
            return
        target = self.ally_heroes if team_type == "ally" else self.enemy_heroes
        if len(target) >= 5:
            QMessageBox.warning(self, "Ліміт", "У команді вже 5 героїв.")
            return
        target.append(name)
        self._render_placeholder_heroes()

    def _build_draft_analysis_card(self):
        self.draft_card = make_card()
        lay = QVBoxLayout(self.draft_card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)
        lay.addWidget(card_title("Аналіз драфту", "analys_draft.png"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(22)
        grid.setVerticalSpacing(10)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        self.strengths_title = self._section_title("Сильні сторони", "#5ee08a")
        grid.addWidget(self.strengths_title, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.strengths_box = QVBoxLayout(); self.strengths_box.setSpacing(8)
        sw = QWidget(); sw.setLayout(self.strengths_box)
        grid.addWidget(sw, 1, 0, Qt.AlignmentFlag.AlignTop)

        self.weak_title = self._section_title("Проти вас добре", "#ef6f7a")
        grid.addWidget(self.weak_title, 0, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.weak_box = QVBoxLayout(); self.weak_box.setSpacing(8)
        ww = QWidget(); ww.setLayout(self.weak_box)
        grid.addWidget(ww, 1, 1, Qt.AlignmentFlag.AlignTop)

        self.weak2_title = self._section_title("Слабкі сторони", "#ef6f7a")
        grid.addWidget(self.weak2_title, 2, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.weak2_box = QVBoxLayout(); self.weak2_box.setSpacing(8)
        w2 = QWidget(); w2.setLayout(self.weak2_box)
        grid.addWidget(w2, 3, 0, Qt.AlignmentFlag.AlignTop)

        self.strategy_title = self._section_title("Рекомендація по стратегії", "#9d90f5")
        grid.addWidget(self.strategy_title, 2, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.strategy_box = QVBoxLayout(); self.strategy_box.setSpacing(8)
        sg = QWidget(); sg.setLayout(self.strategy_box)
        grid.addWidget(sg, 3, 1, Qt.AlignmentFlag.AlignTop)

        for r in (1, 3):
            grid.setRowStretch(r, 0)
        lay.addLayout(grid)

        # Synergies + counters -- stacked full-width panels (previously
        # squeezed side-by-side into ~200px columns, which made hero names
        # and descriptions overlap/clip). Full width gives the text room
        # to wrap legibly.
        lay.addWidget(self._divider())
        mini_col = QVBoxLayout()
        mini_col.setSpacing(14)
        mini_col.addWidget(self._build_synergy_panel())
        mini_col.addWidget(self._build_counter_panel())
        lay.addLayout(mini_col)

        self._set_empty_analysis()
        return self.draft_card

    def _build_synergy_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color:#0f1220; border:1px solid #1f2436; border-radius:12px; }")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)
        lay.addWidget(card_title("Синергії вашої команди", "synergi.jpg"))
        self.syn_box = QVBoxLayout(); self.syn_box.setSpacing(8)
        holder = QWidget(); holder.setLayout(self.syn_box)
        lay.addWidget(holder)
        return panel

    def _build_counter_panel(self):
        panel = QFrame()
        panel.setStyleSheet("QFrame { background-color:#0f1220; border:1px solid #1f2436; border-radius:12px; }")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(8)
        lay.addWidget(card_title("Контрпіки проти вас", "counterpick.jpeg"))
        self.counter_box = QVBoxLayout(); self.counter_box.setSpacing(8)
        holder = QWidget(); holder.setLayout(self.counter_box)
        lay.addWidget(holder)
        return panel

    def _section_title(self, text, color):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color:{color}; font-weight:700; font-size:12px; border:none; background:transparent; letter-spacing:0.3px; padding-bottom:2px;")
        return lbl

    def _divider(self):
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background-color:#1f2436; border:none;")
        return line

    def _set_empty_analysis(self):
        for box in (self.strengths_box, self.weak_box, self.weak2_box, self.strategy_box):
            self._clear_layout(box)
        self.strengths_box.addWidget(body_label("Запустіть аналіз, щоб побачити дані", size=12, color="#5a5f78"))
        self.weak_box.addWidget(body_label("—", size=12, color="#5a5f78"))
        self.weak2_box.addWidget(body_label("—", size=12, color="#5a5f78"))
        self.strategy_box.addWidget(body_label("—", size=12, color="#5a5f78"))
        self._clear_layout(self.syn_box)
        self._clear_layout(self.counter_box)
        self.syn_box.addWidget(small_label("Немає даних"))
        self.counter_box.addWidget(small_label("Немає даних"))

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _build_meta_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(8)
        lay.addWidget(card_title("ТОП-5 поточної мети (STRATZ)", "stratz_logo.png"))

        self.meta_box = QVBoxLayout()
        self.meta_box.setSpacing(8)
        holder = QWidget()
        holder.setLayout(self.meta_box)
        lay.addWidget(holder)

        self.meta_box.addWidget(small_label("Запустіть аналіз або оновіть статистику, щоб побачити ТОП-5 мети"))
        return card

    def _build_recommendations_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)
        lay.addWidget(card_title("Рекомендований пік для вас", "recomendation_default.png"))
        self.reco_box = QVBoxLayout()
        self.reco_box.setSpacing(8)
        holder = QWidget(); holder.setLayout(self.reco_box)
        lay.addWidget(holder)
        self.reco_box.addWidget(small_label("Запустіть аналіз, щоб отримати ТОП-5 героїв для вашого піку"))

        lay.addWidget(self._divider())
        lay.addWidget(card_title("Ймовірний пік суперника", "counterpick.jpeg"))
        self.enemy_prediction_box = QVBoxLayout()
        self.enemy_prediction_box.setSpacing(8)
        enemy_holder = QWidget(); enemy_holder.setLayout(self.enemy_prediction_box)
        lay.addWidget(enemy_holder)
        self.enemy_prediction_box.addWidget(small_label("Тут буде прогноз героїв, яких може взяти ворог"))
        return card

    def _build_ai_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(14)
        lay.addWidget(card_title("Пояснення від ШІ", "recomendation_ai.jpg"))
        self.ai_text = body_label("Запустіть аналіз, щоб отримати пояснення від штучного інтелекту.", size=13)
        self.ai_text.setStyleSheet("font-size:13px; color:#c4c7d6; border:none; background:transparent; line-height:160%;")
        lay.addWidget(self.ai_text)
        self.ai_badge_holder = QHBoxLayout()
        self.ai_badge_holder.setContentsMargins(0, 0, 0, 0)
        self.ai_badge = pill("✨ Згенеровано з використанням Gemini 3 Pro")
        self.ai_badge.hide()
        self.ai_badge_holder.addWidget(self.ai_badge, 0, Qt.AlignmentFlag.AlignLeft)
        self.ai_badge_holder.addStretch()
        lay.addLayout(self.ai_badge_holder)
        return card

    def _build_history_panel(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)
        header_row = QHBoxLayout()
        header_row.addWidget(card_title("Історія аналізів", "🕘"))
        header_row.addStretch()
        lay.addLayout(header_row)

        self.history_list = QListWidget()
        self.history_list.setSpacing(0)
        self.history_list.setMinimumHeight(640)
        self.history_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.history_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_list.setStyleSheet("QListWidget { border:none; background:transparent; }")
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        lay.addWidget(self.history_list)

        clear_btn = QPushButton("🗑  Очистити історію")
        clear_btn.setProperty("class", "danger")
        clear_btn.setStyleSheet("""
            QPushButton { background-color: #2a1620; color: #f0728a; border: 1px solid #4a2233;
                border-radius: 8px; padding: 8px 14px; font-weight: 600; }
            QPushButton:hover { background-color: #3a1c29; }
        """)
        clear_btn.clicked.connect(self.on_clear_history)
        lay.addWidget(clear_btn)
        return card

    # ---------------------------------------------------------- DATA / ACTIONS
    def update_side_buttons(self):
        active_style = """
            QPushButton { background-color: #1d3a2a; color: #5ee08a; border: 1.5px solid #5ee08a;
                border-radius: 8px; padding: 9px 16px; font-weight: 700; }
        """
        active_style_dire = """
            QPushButton { background-color: #3a1d22; color: #ef6f7a; border: 1.5px solid #ef6f7a;
                border-radius: 8px; padding: 9px 16px; font-weight: 700; }
        """
        # inactive state still carries a faint tint of the faction's own
        # colour (green for Radiant, red for Dire) instead of a neutral grey,
        # so each button visually reads as "its" side even when not selected
        inactive_style_radiant = """
            QPushButton { background-color: #16241c; color: #8fd3a8; border: 1px solid #2c5e42;
                border-radius: 8px; padding: 9px 16px; font-weight: 600; }
            QPushButton:hover { background-color: #1a2e22; }
        """
        inactive_style_dire = """
            QPushButton { background-color: #271619; color: #e39aa2; border: 1px solid #5e2c33;
                border-radius: 8px; padding: 9px 16px; font-weight: 600; }
            QPushButton:hover { background-color: #301b1f; }
        """
        self.btn_radiant.setStyleSheet(active_style if self.side == "Radiant" else inactive_style_radiant)
        self.btn_dire.setStyleSheet(active_style_dire if self.side == "Dire" else inactive_style_dire)
        ally_label = "Radiant" if self.side == "Radiant" else "Dire"
        enemy_label = "Dire" if self.side == "Radiant" else "Radiant"
        ally_color = "#5ee08a" if ally_label == "Radiant" else "#ef6f7a"
        enemy_color = "#5ee08a" if enemy_label == "Radiant" else "#ef6f7a"
        self.ally_title.setText(f"Ваша команда ({ally_label})")
        self.ally_title.setStyleSheet(f"font-size: 13px; color: {ally_color}; font-weight: 700; border: none; background: transparent;")
        self.enemy_title.setText(f"Команда суперника ({enemy_label})")
        self.enemy_title.setStyleSheet(f"font-size: 13px; color: {enemy_color}; font-weight: 700; border: none; background: transparent;")

    def set_side(self, side):
        self.side = side
        self.update_side_buttons()

    def on_upload_clicked(self):
        # Старий варіант відкривав QMenu, через що на деяких Windows/frameless
        # вікнах меню не показувалось. Тепер клік одразу відкриває вибір файлу.
        self._upload_from_file()

    def _upload_from_file(self):
        options = QFileDialog.Option.DontUseNativeDialog
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Завантажити скриншот драфту",
            os.path.expanduser("~"),
            "Зображення (*.png *.jpg *.jpeg *.bmp *.webp);;Усі файли (*.*)",
            options=options,
        )
        if not path:
            return
        if not os.path.exists(path):
            QMessageBox.warning(self, "Файл", "Файл не знайдено.")
            return
        self._process_screenshot(path)

    def _upload_from_clipboard(self):
        from PyQt6.QtWidgets import QApplication
        import tempfile, time

        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        # 1) Якщо в буфері саме зображення (Print Screen / Win+Shift+S)
        image = clipboard.image()
        if not image.isNull():
            tmp_dir = tempfile.gettempdir()
            path = os.path.join(tmp_dir, f"clipboard_draft_{int(time.time())}.png")
            if not image.save(path, "PNG"):
                QMessageBox.warning(self, "Буфер обміну", "Не вдалося зберегти зображення з буфера.")
                return
            self._process_screenshot(path)
            return

        # 2) Якщо в буфер скопійований файл-картинка
        if mime and mime.hasUrls():
            for url in mime.urls():
                local = url.toLocalFile()
                if local and os.path.exists(local) and local.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".webp")):
                    self._process_screenshot(local)
                    return

        QMessageBox.information(
            self,
            "Буфер обміну",
            "У буфері немає зображення. Скопіюйте скриншот через Print Screen або Win+Shift+S і натисніть «З буфера».",
        )

    def on_capture_clicked(self, from_hotkey=False):
        folder = db.get_setting("screenshot_folder")
        win = self.window()

        if from_hotkey:
            # The global hotkey fires while this app is (almost certainly)
            # already in the background -- e.g. the user is tabbed into
            # Dota 2. There's nothing to get out of the way, and forcing
            # a minimize/restore here would yank focus away from the game
            # right as the shot is taken. Just capture directly.
            self._do_capture(folder, restore_window=False)
            return

        try:
            # Get the app out of the way before grabbing the screen -- a
            # plain hide() is instant (no taskbar minimize animation, no
            # visible "closing"), unlike showMinimized().
            win.setEnabled(False)
            win.hide()
            QTimer.singleShot(200, lambda: self._do_capture(folder, restore_window=True))
        except Exception as e:
            win.setEnabled(True)
            win.show()
            QMessageBox.warning(self, "Помилка", str(e))

    def _do_capture(self, folder, restore_window):
        win = self.window()
        try:
            path = screenshot_service.capture_fullscreen(folder)
            self._maybe_open_screenshot(path)
            self._process_screenshot(path)
        except Exception as e:
            if restore_window:
                win.setEnabled(True)
                win.show()
                win.activateWindow()
            QMessageBox.warning(self, "Помилка створення скриншота", str(e))
            return
        if restore_window:
            win.setEnabled(True)
            win.show()
            win.activateWindow()

    def _maybe_open_screenshot(self, path):
        """Opens the freshly captured screenshot in the OS's default image
        viewer right away, if "Автоматично відкривати скриншот" is on.
        Previously this setting was saved but never actually acted on
        anywhere, so a screenshot was silently written to disk with no
        visible confirmation that anything had happened."""
        if db.get_setting("auto_open_screenshot") != "1":
            return
        try:
            from PyQt6.QtCore import QUrl
            from PyQt6.QtGui import QDesktopServices
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        except Exception:
            pass

    def _process_screenshot(self, path):
        try:
            self.screenshot_path = path
            result = vision_service.recognize_draft(path, side=self.side)
            self.ally_heroes = list(result.get("ally_heroes", []))
            self.enemy_heroes = list(result.get("enemy_heroes", []))
            self._render_placeholder_heroes()

            found = len(self.ally_heroes) + len(self.enemy_heroes)
            if found == 0:
                QMessageBox.information(
                    self,
                    "Скриншот завантажено",
                    "Скриншот відкрився, але герої не розпізнані. Перевірте debug_cv/last_detection.png або додайте героїв вручну.",
                )
        except Exception as e:
            QMessageBox.warning(self, "Помилка обробки скриншота", str(e))

    def on_analyze_clicked(self):
        if not self.ally_heroes and not self.enemy_heroes:
            QMessageBox.warning(
                self,
                "Аналіз неможливий",
                "Спочатку завантажте скриншот або додайте героїв вручну.\n\n"
                "Програма більше не підставляє героїв автоматично."
            )
            return

        ai_key = db.get_setting("gemini_api_key")
        ai_lang = db.get_setting("ai_response_language", "Українська")

        analysis = analysis_engine.run_full_analysis(self.ally_heroes, self.enemy_heroes, side=self.side)
        assistant_data, used_live = gemini_service.generate_match_assistant(ai_key, analysis, ai_lang)

        analysis["ally_recommendations"] = assistant_data.get("ally_recommendations", analysis.get("ally_recommendations", []))
        analysis["recommendations"] = analysis["ally_recommendations"]
        analysis["enemy_predictions"] = assistant_data.get("enemy_predictions", analysis.get("enemy_predictions", []))
        analysis["strengths"] = assistant_data.get("strengths", analysis.get("strengths", []))
        analysis["weaknesses"] = assistant_data.get("weaknesses", analysis.get("weaknesses", []))
        analysis["strategy"] = assistant_data.get("strategy", analysis.get("strategy", []))
        analysis["synergies"] = assistant_data.get("synergies", analysis.get("synergies", []))
        analysis["counters"] = assistant_data.get("counters", analysis.get("counters", []))
        analysis["ai_text"] = assistant_data.get("explanation", "")
        analysis["used_live_ai"] = used_live

        self.last_analysis = analysis
        self._render_analysis(analysis)
        self._save_to_history(analysis)
        self.refresh_history_panel()

    def _render_analysis(self, a):
        # team strength badges on chips already shown; render draft analysis card
        self._clear_layout(self.strengths_box)
        self._clear_layout(self.weak_box)
        self._clear_layout(self.weak2_box)
        self._clear_layout(self.strategy_box)
        for s in a["strengths"]:
            self.strengths_box.addWidget(self._bullet_row("✓", s, "#5ee08a", "#bfead0"))
        for w in a["weaknesses"][:2]:
            self.weak_box.addWidget(self._bullet_row("•", w, "#ef6f7a", "#f3b9c0"))
        for w in a["weaknesses"]:
            self.weak2_box.addWidget(self._bullet_row("✗", w, "#ef6f7a", "#f3b9c0"))
        for t in a["strategy"]:
            self.strategy_box.addWidget(self._bullet_row("•", t, "#9d90f5", "#cfc8f7"))

        self._clear_layout(self.syn_box)
        if a["synergies"]:
            for s in a["synergies"]:
                self.syn_box.addWidget(self._synergy_widget(s))
            self.syn_box.addStretch()
        else:
            self.syn_box.addWidget(small_label("Синергій не знайдено"))

        self._clear_layout(self.counter_box)
        if a["counters"]:
            for c in a["counters"]:
                self.counter_box.addWidget(self._counter_widget(c))
            self.counter_box.addStretch()
        else:
            self.counter_box.addWidget(small_label("Контрпіків не знайдено"))

        # TOP-5 current meta from STRATZ/local stats
        medal_colors = ["#f3c34c", "#c8ccdb", "#cd8b50", "#4F46E5", "#4F46E5"]
        if hasattr(self, "meta_box"):
            self._clear_layout(self.meta_box)
            meta_recs = a.get("meta_recommendations", [])
            if meta_recs:
                for i, rec in enumerate(meta_recs):
                    self.meta_box.addWidget(self._reco_row(i + 1, rec, medal_colors[i] if i < len(medal_colors) else "#4F46E5"))
            else:
                self.meta_box.addWidget(small_label("ТОП-5 мети ще не сформовано"))

        # recommendations for user's next pick
        self._clear_layout(self.reco_box)
        for i, rec in enumerate(a.get("ally_recommendations", a.get("recommendations", []))):
            self.reco_box.addWidget(self._reco_row(i + 1, rec, medal_colors[i] if i < len(medal_colors) else "#4F46E5"))

        # predicted enemy picks / dangerous enemy picks
        self._clear_layout(self.enemy_prediction_box)
        enemy_predictions = a.get("enemy_predictions", [])
        if enemy_predictions:
            for i, rec in enumerate(enemy_predictions):
                self.enemy_prediction_box.addWidget(self._prediction_row(i + 1, rec))
        else:
            self.enemy_prediction_box.addWidget(small_label("Прогноз піків суперника не сформовано"))

        # AI explanation
        self.ai_text.setText(a.get("ai_text", ""))
        self.ai_badge.setText("✨ Аналіз конкретного матчу через Gemini" if a.get("used_live_ai") else "✨ Локальний аналіз без Gemini")
        self.ai_badge.show()

    _MINI_CARD_WIDTH = 92

    def _synergy_widget(self, syn):
        """Compact table-row style: overlapping hero icons on the left,
        pair name + short description stacked on the right."""
        wrap = QWidget()
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        icons_row = QHBoxLayout(); icons_row.setSpacing(-10)
        for name in syn["pair"]:
            lbl = QLabel()
            lbl.setFixedSize(30, 30)
            lbl.setPixmap(round_pixmap(hero_pixmap(name, 30), 7))
            lbl.setStyleSheet("border: 2px solid #0f1220; border-radius: 7px;")
            icons_row.addWidget(lbl)
        icons_w = QWidget(); icons_w.setLayout(icons_row)
        icons_w.setFixedWidth(30 + max(0, (len(syn["pair"]) - 1)) * 20)
        row.addWidget(icons_w, 0, Qt.AlignmentFlag.AlignTop)
        text_box = QVBoxLayout(); text_box.setSpacing(2)
        name_lbl = body_label(" + ".join(syn["pair"]), size=11, color="#c4c7d6", weight=600)
        name_lbl.setWordWrap(True)
        text_box.addWidget(name_lbl)
        desc_lbl = small_label(syn["desc"])
        desc_lbl.setWordWrap(True)
        text_box.addWidget(desc_lbl)
        row.addLayout(text_box, 1)
        return wrap

    def _counter_widget(self, c):
        """Same compact 'table-row' layout as _synergy_widget: portrait on
        the left, hero name + description stacked to the right with word
        wrap -- avoids the old 92px-wide column where the name and
        description text overlapped and got clipped."""
        wrap = QWidget()
        row = QHBoxLayout(wrap)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        lbl = QLabel()
        lbl.setFixedSize(36, 36)
        lbl.setPixmap(round_pixmap(hero_pixmap(c["hero"], 36), 8))
        lbl.setStyleSheet("border: 1px solid #262b40; border-radius: 8px;")
        row.addWidget(lbl, 0, Qt.AlignmentFlag.AlignTop)
        text_box = QVBoxLayout(); text_box.setSpacing(2)
        name_lbl = body_label(c["hero"], size=11, color="#c4c7d6", weight=600)
        name_lbl.setWordWrap(True)
        text_box.addWidget(name_lbl)
        desc_lbl = small_label(c["desc"])
        desc_lbl.setWordWrap(True)
        text_box.addWidget(desc_lbl)
        row.addLayout(text_box, 1)
        return wrap

    def _reco_row(self, rank, rec, medal_color):
        row = make_card()
        row.setStyleSheet("""
            QFrame { background-color: #0f1220; border: 1px solid #1f2436; border-radius: 10px; }
            QFrame:hover { border: 1px solid #4F46E5; background-color: #12162a; }
        """)
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.mousePressEvent = lambda e, r=rec: self._show_recommendation_details(r)
        lay = QHBoxLayout(row)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(10)

        num = QLabel(str(rank))
        num.setFixedSize(22, 22)
        num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        num.setStyleSheet(f"background-color: {medal_color}; color: #0c0e16; border-radius: 11px; font-weight: 800; font-size: 11px;")
        lay.addWidget(num)

        img = QLabel()
        img.setFixedSize(40, 40)
        img.setPixmap(round_pixmap(hero_pixmap(rec["name"], 40), 8))
        img.setStyleSheet("border: 1px solid #262b40; border-radius: 8px;")
        lay.addWidget(img)

        text_box = QVBoxLayout(); text_box.setSpacing(2)
        name_row = QHBoxLayout(); name_row.setSpacing(8)
        name_lbl = QLabel(rec["name"])
        name_lbl.setStyleSheet("font-weight:700; color:#fff; font-size:13px; border:none; background:transparent;")
        name_row.addWidget(name_lbl)
        name_row.addWidget(pill(rec["role"], bg="#1c2238", fg="#8ea3f0"))
        name_row.addStretch()
        score_lbl = QLabel(f"⚡ {rec['score']}%")
        score_lbl.setStyleSheet("color:#9d90f5; font-weight:700; font-size:12px; border:none; background:transparent;")
        name_row.addWidget(score_lbl)
        text_box.addLayout(name_row)
        text_box.addWidget(body_label(rec["explanation"], size=11, color="#9095ad"))
        lay.addLayout(text_box, 1)

        arrow = QLabel("›")
        arrow.setStyleSheet("color:#5a5f78; font-size:18px; border:none; background:transparent;")
        lay.addWidget(arrow)
        return row

    def _prediction_row(self, rank, rec):
        row = self._reco_row(rank, rec, "#ef6f7a")
        row.setToolTip("Цей герой не доданий у драфт. Це лише прогноз можливого піку суперника.")
        return row

    def _show_recommendation_details(self, rec):
        """Clicking a Top-5 recommendation now jumps straight to that
        hero's full card on the Статистика page, instead of popping up a
        separate info dialog that had no connection to the rest of the
        app."""
        if self.on_open_stats_hero:
            self.on_open_stats_hero(rec["name"])
            return
        hero = HERO_BY_NAME.get(rec["name"], {})
        lines = [
            f"Роль: {rec['role']}",
            f"Оцінка відповідності: {rec['score']}%",
        ]
        if hero.get("win") is not None:
            lines.append(f"Загальний Win Rate: {hero['win']}%")
        lines.append("")
        lines.append(rec["explanation"])
        QMessageBox.information(self, rec["name"], "\n".join(lines))

    def _save_to_history(self, a):
        import time
        record = {
            "created_at": time.strftime("%d.%m.%Y %H:%M"),
            "side": a["side"],
            "result": a["result"],
            "score_team": a["team_score"],
            "score_enemy": a["enemy_score"],
            "team_heroes": a["team_heroes"],
            "enemy_heroes": a["enemy_heroes"],
            "recommendations": a.get("ally_recommendations", a.get("recommendations", [])),
            "enemy_predictions": a.get("enemy_predictions", []),
            "strengths": a["strengths"],
            "weaknesses": a["weaknesses"],
            "synergies": a["synergies"],
            "counters": a["counters"],
            "ai_explanation": a.get("ai_text", ""),
            "radar": a["radar"],
            "duration_s": a["duration_s"],
        }
        db.save_analysis(record)

    def refresh_history_panel(self):
        self.history_list.clear()
        records = db.list_analyses()[:20]
        for r in records:
            import json
            item = QListWidgetItem()
            widget = self._history_item_widget(r)
            item.setSizeHint(widget.sizeHint() + QSize(0, 12))
            item.setData(Qt.ItemDataRole.UserRole, r["id"])
            self.history_list.addItem(item)
            self.history_list.setItemWidget(item, widget)

    def _history_item_widget(self, r):
        import json
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)
        top = QHBoxLayout()
        top.addWidget(small_label(r["created_at"]))
        top.addStretch()
        top.addWidget(small_label(r.get("side", "")))
        lay.addLayout(top)

        info_lbl = QLabel("Аналіз драфту")
        info_lbl.setStyleSheet("color:#fff; font-weight:700; font-size:13px; border:none; background:transparent;")
        lay.addWidget(info_lbl)

        heroes = json.loads(r["team_heroes"])
        row = QHBoxLayout(); row.setSpacing(6)
        row.setContentsMargins(0, 0, 0, 0)
        for name in heroes[:6]:
            lbl = QLabel()
            lbl.setFixedSize(40, 40)
            lbl.setPixmap(round_pixmap(hero_pixmap_full(name, 40), 9))
            lbl.setStyleSheet("border: 1px solid #262b40; border-radius: 9px; background: transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(lbl)
        row.addStretch()
        lay.addLayout(row)
        return w

    def _on_history_item_clicked(self, item):
        rid = item.data(Qt.ItemDataRole.UserRole)
        if self.on_open_history_item:
            self.on_open_history_item(rid)

    def on_clear_history(self):
        confirm = QMessageBox.question(self, "Очистити історію",
                                        "Видалити всю історію аналізів? Цю дію неможливо скасувати.",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            db.clear_history()
            self.refresh_history_panel()