import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QFileDialog, QScrollArea, QGridLayout, QFrame, QSizePolicy,
                              QListWidget, QListWidgetItem, QMessageBox, QStackedLayout)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QPixmap

from ui.widgets import make_card, card_title, small_label, body_label, pill, HeroChip, hero_pixmap, round_pixmap
import database as db
from services import vision_service, screenshot_service, analysis_engine, gemini_service
from data.heroes_data import HERO_BY_NAME


class HomePage(QWidget):
    def __init__(self, app_state, on_open_history_item=None, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.on_open_history_item = on_open_history_item
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
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(16)

        # ---- Top toolbar ----
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.btn_upload = QPushButton("⬆  Завантажити скриншот")
        self.btn_upload.setProperty("class", "secondary")
        self.btn_upload.setStyleSheet(self._secondary_style())
        self.btn_upload.clicked.connect(self.on_upload_clicked)
        toolbar.addWidget(self.btn_upload)

        self.btn_capture = QPushButton("⧉  Створити скриншот")
        self.btn_capture.setProperty("class", "secondary")
        self.btn_capture.setStyleSheet(self._secondary_style())
        self.btn_capture.clicked.connect(self.on_capture_clicked)
        toolbar.addWidget(self.btn_capture)

        toolbar.addStretch()

        side_box = QVBoxLayout()
        side_label = small_label("Виберіть сторону")
        side_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        side_box.addWidget(side_label)
        side_row = QHBoxLayout()
        side_row.setSpacing(6)
        self.btn_radiant = QPushButton("🌿 Radiant")
        self.btn_dire = QPushButton("👹 Dire")
        self.btn_radiant.clicked.connect(lambda: self.set_side("Radiant"))
        self.btn_dire.clicked.connect(lambda: self.set_side("Dire"))
        side_row.addWidget(self.btn_radiant)
        side_row.addWidget(self.btn_dire)
        side_box.addLayout(side_row)
        toolbar.addLayout(side_box)

        self.btn_analyze = QPushButton("✨  Почати аналіз\nАналіз займе до 5 секунд")
        self.btn_analyze.setProperty("class", "primary")
        self.btn_analyze.setMinimumHeight(48)
        self.btn_analyze.setStyleSheet("""
            QPushButton { background-color: #6c5ce7; color: white; border-radius: 10px;
                font-weight: 700; font-size: 13px; padding: 6px 22px; border: none; text-align: left;}
            QPushButton:hover { background-color: #7b6cf0; }
        """)
        self.btn_analyze.clicked.connect(self.on_analyze_clicked)
        toolbar.addWidget(self.btn_analyze)

        outer.addLayout(toolbar)

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
        left_wrap.setFixedWidth(420)

        # MIDDLE column (recommendations + AI explanation)
        mid_col = QVBoxLayout()
        mid_col.setSpacing(16)
        mid_col.addWidget(self._build_recommendations_card())
        mid_col.addWidget(self._build_ai_card())
        mid_wrap = QWidget(); mid_wrap.setLayout(mid_col)

        # RIGHT column (history)
        right_wrap = self._build_history_panel()
        right_wrap.setFixedWidth(300)

        body.addWidget(left_wrap)
        body.addWidget(mid_wrap, 1)
        body.addWidget(right_wrap)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._wrap(body))
        outer.addWidget(scroll, 1)

    def _wrap(self, layout):
        w = QWidget()
        w.setLayout(layout)
        return w

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
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)
        lay.addWidget(card_title("Розпізнані герої", "🧩"))

        self.ally_title = small_label("Ваша команда (Radiant)")
        lay.addWidget(self.ally_title)
        self.ally_row = QHBoxLayout()
        self.ally_row.setSpacing(10)
        ally_holder = QWidget(); ally_holder.setLayout(self.ally_row)
        lay.addWidget(ally_holder)

        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background-color:#1f2436; border:none;")
        lay.addWidget(line)

        self.enemy_title = small_label("Команда суперника (Dire)")
        lay.addWidget(self.enemy_title)
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
                self.ally_row.addWidget(HeroChip(name, size=56))
        if self.enemy_heroes:
            for name in self.enemy_heroes:
                self.enemy_row.addWidget(HeroChip(name, size=56))
        else:
            self.enemy_row.addWidget(small_label("—"))

    def _build_draft_analysis_card(self):
        self.draft_card = make_card()
        lay = QVBoxLayout(self.draft_card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)
        lay.addWidget(card_title("Аналіз драфту", "🛡"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(4)

        self.strengths_title = QLabel("Сильні сторони")
        self.strengths_title.setStyleSheet("color:#5ee08a; font-weight:700; font-size:12px; border:none; background:transparent;")
        self.weak_title = QLabel("Проти вас добре")
        self.weak_title.setStyleSheet("color:#ef6f7a; font-weight:700; font-size:12px; border:none; background:transparent;")
        grid.addWidget(self.strengths_title, 0, 0)
        grid.addWidget(self.weak_title, 0, 1)

        self.strengths_box = QVBoxLayout(); self.strengths_box.setSpacing(4)
        self.weak_box = QVBoxLayout(); self.weak_box.setSpacing(4)
        sw = QWidget(); sw.setLayout(self.strengths_box)
        ww = QWidget(); ww.setLayout(self.weak_box)
        grid.addWidget(sw, 1, 0)
        grid.addWidget(ww, 1, 1)

        self.weak2_title = QLabel("Слабкі сторони")
        self.weak2_title.setStyleSheet("color:#ef6f7a; font-weight:700; font-size:12px; border:none; background:transparent;")
        self.strategy_title = QLabel("Рекомендація по стратегії")
        self.strategy_title.setStyleSheet("color:#9d90f5; font-weight:700; font-size:12px; border:none; background:transparent;")
        grid.addWidget(self.weak2_title, 2, 0)
        grid.addWidget(self.strategy_title, 2, 1)

        self.weak2_box = QVBoxLayout(); self.weak2_box.setSpacing(4)
        self.strategy_box = QVBoxLayout(); self.strategy_box.setSpacing(4)
        w2 = QWidget(); w2.setLayout(self.weak2_box)
        sg = QWidget(); sg.setLayout(self.strategy_box)
        grid.addWidget(w2, 3, 0)
        grid.addWidget(sg, 3, 1)

        lay.addLayout(grid)

        # Synergies
        lay.addWidget(self._divider())
        self.syn_label = card_title("Синергії вашої команди", "🤝")
        lay.addWidget(self.syn_label)
        self.syn_box = QHBoxLayout(); self.syn_box.setSpacing(14)
        synw = QWidget(); synw.setLayout(self.syn_box)
        lay.addWidget(synw)

        self.counter_label = card_title("Контрпіки проти вас", "⚠")
        lay.addWidget(self.counter_label)
        self.counter_box = QHBoxLayout(); self.counter_box.setSpacing(14)
        counterw = QWidget(); counterw.setLayout(self.counter_box)
        lay.addWidget(counterw)

        self._set_empty_analysis()
        return self.draft_card

    def _divider(self):
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background-color:#1f2436; border:none;")
        return line

    def _set_empty_analysis(self):
        for box in (self.strengths_box, self.weak_box, self.weak2_box, self.strategy_box):
            self._clear_layout(box)
        self.strengths_box.addWidget(body_label("—", size=12))
        self.weak_box.addWidget(body_label("—", size=12))
        self.weak2_box.addWidget(body_label("—", size=12))
        self.strategy_box.addWidget(body_label("—", size=12))
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

    def _build_recommendations_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)
        lay.addWidget(card_title("Рекомендації (ТОП-5)", "✨"))
        self.reco_box = QVBoxLayout()
        self.reco_box.setSpacing(8)
        holder = QWidget(); holder.setLayout(self.reco_box)
        lay.addWidget(holder)
        self.reco_box.addWidget(small_label("Запустіть аналіз, щоб отримати рекомендації"))
        return card

    def _build_ai_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)
        lay.addWidget(card_title("Пояснення від ШІ", "💬"))
        self.ai_text = body_label("Запустіть аналіз, щоб отримати пояснення від штучного інтелекту.", size=13)
        lay.addWidget(self.ai_text)
        self.ai_badge_holder = QHBoxLayout()
        self.ai_badge = pill("Згенеровано з використанням Gemini 3 Pro")
        self.ai_badge.hide()
        self.ai_badge_holder.addWidget(self.ai_badge)
        self.ai_badge_holder.addStretch()
        lay.addLayout(self.ai_badge_holder)
        return card

    def _build_history_panel(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)
        header_row = QHBoxLayout()
        header_row.addWidget(card_title("Історія аналізів", "🕘"))
        header_row.addStretch()
        lay.addLayout(header_row)

        self.history_list = QListWidget()
        self.history_list.setSpacing(0)
        self.history_list.itemClicked.connect(self._on_history_item_clicked)
        lay.addWidget(self.history_list, 1)

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
            QPushButton { background-color: #1d3a2a; color: #5ee08a; border: 1px solid #2c5e42;
                border-radius: 8px; padding: 9px 16px; font-weight: 700; }
        """
        active_style_dire = """
            QPushButton { background-color: #3a1d22; color: #ef6f7a; border: 1px solid #5e2c33;
                border-radius: 8px; padding: 9px 16px; font-weight: 700; }
        """
        inactive_style = """
            QPushButton { background-color: #181c2c; color: #aeb2c4; border: 1px solid #2a2f45;
                border-radius: 8px; padding: 9px 16px; font-weight: 600; }
            QPushButton:hover { background-color: #20253a; }
        """
        self.btn_radiant.setStyleSheet(active_style if self.side == "Radiant" else inactive_style)
        self.btn_dire.setStyleSheet(active_style_dire if self.side == "Dire" else inactive_style)
        ally_label = "Radiant" if self.side == "Radiant" else "Dire"
        enemy_label = "Dire" if self.side == "Radiant" else "Radiant"
        self.ally_title.setText(f"Ваша команда ({ally_label})")
        self.enemy_title.setText(f"Команда суперника ({enemy_label})")

    def set_side(self, side):
        self.side = side
        self.update_side_buttons()

    def on_upload_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "Завантажити скриншот драфту", "",
                                               "Images (*.png *.jpg *.jpeg)")
        if path:
            self._process_screenshot(path)

    def on_capture_clicked(self):
        folder = db.get_setting("screenshot_folder")
        try:
            self.window().setEnabled(False)
            QTimer.singleShot(300, lambda: self._do_capture(folder))
        except Exception as e:
            self.window().setEnabled(True)
            QMessageBox.warning(self, "Помилка", str(e))

    def _do_capture(self, folder):
        try:
            path = screenshot_service.capture_fullscreen(folder)
            self._process_screenshot(path)
        except Exception as e:
            QMessageBox.warning(self, "Помилка створення скриншота", str(e))
        finally:
            self.window().setEnabled(True)

    def _process_screenshot(self, path):
        self.screenshot_path = path
        result = vision_service.recognize_draft(path, side=self.side)
        self.ally_heroes = result["ally_heroes"]
        self.enemy_heroes = result["enemy_heroes"]
        self._render_placeholder_heroes()

    def on_analyze_clicked(self):
        if not self.ally_heroes or not self.enemy_heroes:
            # auto-fill with sample draft so the button always works, like a real demo
            result = vision_service.recognize_draft("__no_file__", side=self.side)
            self.ally_heroes = result["ally_heroes"]
            self.enemy_heroes = result["enemy_heroes"]
            self._render_placeholder_heroes()

        analysis = analysis_engine.run_full_analysis(self.ally_heroes, self.enemy_heroes, side=self.side)
        ai_key = db.get_setting("gemini_api_key")
        ai_lang = db.get_setting("ai_response_language", "Українська")
        ai_text, used_live = gemini_service.generate_explanation(ai_key, analysis, ai_lang)
        analysis["ai_text"] = ai_text
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
            self.strengths_box.addWidget(body_label(f"✓ {s}", color="#bfead0", size=12))
        for w in a["weaknesses"][:2]:
            self.weak_box.addWidget(body_label(f"• {w}", color="#f3b9c0", size=12))
        for w in a["weaknesses"]:
            self.weak2_box.addWidget(body_label(f"✗ {w}", color="#f3b9c0", size=12))
        for t in a["strategy"]:
            self.strategy_box.addWidget(body_label(f"• {t}", color="#cfc8f7", size=12))

        self._clear_layout(self.syn_box)
        if a["synergies"]:
            for s in a["synergies"]:
                self.syn_box.addLayout(self._synergy_widget(s))
        else:
            self.syn_box.addWidget(small_label("Синергій не знайдено"))

        self._clear_layout(self.counter_box)
        if a["counters"]:
            for c in a["counters"]:
                self.counter_box.addLayout(self._counter_widget(c))
        else:
            self.counter_box.addWidget(small_label("Контрпіків не знайдено"))

        # recommendations
        self._clear_layout(self.reco_box)
        medal_colors = ["#f3c34c", "#c8ccdb", "#cd8b50", "#6c5ce7", "#6c5ce7"]
        for i, rec in enumerate(a["recommendations"]):
            self.reco_box.addWidget(self._reco_row(i + 1, rec, medal_colors[i] if i < len(medal_colors) else "#6c5ce7"))

        # AI
        self.ai_text.setText(a.get("ai_text", ""))
        self.ai_badge.show()

    def _synergy_widget(self, syn):
        box = QVBoxLayout(); box.setSpacing(4)
        row = QHBoxLayout(); row.setSpacing(-10)
        for name in syn["pair"]:
            lbl = QLabel()
            lbl.setFixedSize(40, 40)
            lbl.setPixmap(round_pixmap(hero_pixmap(name, 40), 8))
            lbl.setStyleSheet("border: 2px solid #131625; border-radius: 8px;")
            row.addWidget(lbl)
        rw = QWidget(); rw.setLayout(row)
        box.addWidget(rw)
        box.addWidget(body_label(" + ".join(syn["pair"]), size=11, color="#c4c7d6"))
        box.addWidget(small_label(syn["desc"]))
        return box

    def _counter_widget(self, c):
        box = QVBoxLayout(); box.setSpacing(4)
        lbl = QLabel()
        lbl.setFixedSize(40, 40)
        lbl.setPixmap(round_pixmap(hero_pixmap(c["hero"], 40), 8))
        lbl.setStyleSheet("border: 1px solid #262b40; border-radius: 8px;")
        box.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignLeft)
        box.addWidget(body_label(c["hero"], size=11, color="#c4c7d6"))
        box.addWidget(small_label(c["desc"]))
        return box

    def _reco_row(self, rank, rec, medal_color):
        row = make_card()
        row.setStyleSheet("QFrame { background-color: #0f1220; border: 1px solid #1f2436; border-radius: 10px; }")
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
            "recommendations": a["recommendations"],
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
        records = db.list_analyses()[:6]
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
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)
        top = QHBoxLayout()
        top.addWidget(small_label(r["created_at"]))
        top.addStretch()
        result_lbl = QLabel("Перемога" if r["result"] == "win" else "Поразка")
        result_lbl.setStyleSheet(f"color:{'#5ee08a' if r['result']=='win' else '#ef6f7a'}; font-weight:700; font-size:11px; border:none; background:transparent;")
        top.addWidget(result_lbl)
        score_lbl = QLabel(f"{r['score_team']} - {r['score_enemy']}")
        score_lbl.setStyleSheet("color:#fff; font-weight:700; font-size:11px; border:none; background:transparent;")
        top.addWidget(score_lbl)
        lay.addLayout(top)

        heroes = json.loads(r["team_heroes"])
        row = QHBoxLayout(); row.setSpacing(4)
        for name in heroes[:6]:
            lbl = QLabel()
            lbl.setFixedSize(28, 28)
            lbl.setPixmap(round_pixmap(hero_pixmap(name, 28), 6))
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
