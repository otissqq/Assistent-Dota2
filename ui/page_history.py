import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QLineEdit, QComboBox, QListWidget, QListWidgetItem,
                              QTabWidget, QScrollArea, QFrame, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt, QSize

from ui.widgets import (make_card, card_title, small_label, body_label, pill,
                         hero_pixmap, round_pixmap, RadarChart)
import database as db


class HistoryPage(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.selected_id = None
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(14)

        header = QVBoxLayout()
        header.addWidget(QLabel("🕘  Історія аналізів", styleSheet="font-size:20px; font-weight:700; color:#fff; border:none; background:transparent;"))
        outer.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(16)

        # ---- LEFT: search + list ----
        left = QVBoxLayout()
        left.setSpacing(10)
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍  Пошук у історії...")
        self.search_edit.textChanged.connect(self.refresh)
        search_row.addWidget(self.search_edit, 1)
        self.side_filter = QComboBox()
        self.side_filter.addItems(["Усі сторони", "Radiant", "Dire"])
        self.side_filter.currentTextChanged.connect(self.refresh)
        search_row.addWidget(self.side_filter)
        left.addLayout(search_row)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_select)
        left.addWidget(self.list_widget, 1)

        left_wrap = QWidget(); left_wrap.setLayout(left)
        left_wrap.setFixedWidth(360)

        # ---- RIGHT: detail panel ----
        self.detail_card = make_card()
        self.detail_layout = QVBoxLayout(self.detail_card)
        self.detail_layout.setContentsMargins(18, 16, 18, 16)
        self.detail_layout.setSpacing(10)
        self._render_empty_detail()

        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        detail_scroll.setWidget(self.detail_card)

        body.addWidget(left_wrap)
        body.addWidget(detail_scroll, 1)
        outer.addLayout(body, 1)

    # ------------------------------------------------------------ LIST
    def refresh(self):
        self.list_widget.clear()
        records = db.list_analyses(self.search_edit.text(), self.side_filter.currentText())
        for r in records:
            item = QListWidgetItem()
            w = self._list_item_widget(r)
            item.setSizeHint(QSize(w.sizeHint().width(), w.sizeHint().height() + 14))
            item.setData(Qt.ItemDataRole.UserRole, r["id"])
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, w)
        if records and self.selected_id is None:
            self.selected_id = records[0]["id"]
            self._render_detail(records[0])
        elif not records:
            self.selected_id = None
            self._render_empty_detail()

    def _list_item_widget(self, r):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(4)
        top = QHBoxLayout()
        top.addWidget(small_label(r["created_at"]))
        top.addStretch()
        side_lbl = QLabel(("🌿 " if r["side"] == "Radiant" else "👹 ") + r["side"])
        side_lbl.setStyleSheet("font-size:11px; color:#aeb2c4; border:none; background:transparent;")
        top.addWidget(side_lbl)
        lay.addLayout(top)

        mid = QHBoxLayout()
        result_lbl = QLabel("Перемога" if r["result"] == "win" else "Поразка")
        result_lbl.setStyleSheet(f"color:{'#5ee08a' if r['result']=='win' else '#ef6f7a'}; font-weight:700; font-size:13px; border:none; background:transparent;")
        mid.addWidget(result_lbl)
        mid.addStretch()
        score_lbl = QLabel(f"{r['score_team']} - {r['score_enemy']}")
        score_lbl.setStyleSheet("color:#fff; font-weight:700; font-size:13px; border:none; background:transparent;")
        mid.addWidget(score_lbl)
        lay.addLayout(mid)

        heroes = json.loads(r["team_heroes"])
        row = QHBoxLayout(); row.setSpacing(4)
        for name in heroes[:6]:
            lbl = QLabel()
            lbl.setFixedSize(30, 30)
            lbl.setPixmap(round_pixmap(hero_pixmap(name, 30), 6))
            row.addWidget(lbl)
        row.addStretch()
        lay.addLayout(row)
        return w

    def _on_select(self, item):
        rid = item.data(Qt.ItemDataRole.UserRole)
        self.selected_id = rid
        rec = db.get_analysis(rid)
        if rec:
            self._render_detail(rec)

    # ------------------------------------------------------------ DETAIL
    def _clear_detail(self):
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                self._clear_layout_rec(item.layout())

    def _clear_layout_rec(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                self._clear_layout_rec(item.layout())

    def _render_empty_detail(self):
        self._clear_detail()
        self.detail_layout.addWidget(body_label("Оберіть запис зі списку зліва, щоб переглянути деталі аналізу.", size=13))
        self.detail_layout.addStretch()

    def _render_detail(self, r):
        self._clear_detail()

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.addWidget(small_label(r["created_at"]))
        result_row = QHBoxLayout()
        result_lbl = QLabel("Перемога" if r["result"] == "win" else "Поразка")
        result_lbl.setStyleSheet(f"font-size:18px; font-weight:800; color:{'#5ee08a' if r['result']=='win' else '#ef6f7a'}; border:none; background:transparent;")
        result_row.addWidget(result_lbl)
        side_lbl = QLabel(("🌿 " if r["side"] == "Radiant" else "👹 ") + r["side"])
        side_lbl.setStyleSheet("color:#aeb2c4; font-size:13px; border:none; background:transparent;")
        result_row.addWidget(side_lbl)
        result_row.addStretch()
        title_box.addLayout(result_row)
        header.addLayout(title_box)
        header.addStretch()
        del_btn = QPushButton("🗑  Видалити")
        del_btn.setStyleSheet("""
            QPushButton { background-color: #2a1620; color: #f0728a; border: 1px solid #4a2233;
                border-radius: 8px; padding: 8px 14px; font-weight: 600; }
            QPushButton:hover { background-color: #3a1c29; }
        """)
        del_btn.clicked.connect(lambda: self._delete(r["id"]))
        header.addWidget(del_btn)
        self.detail_layout.addLayout(header)

        tabs = QTabWidget()
        tabs.addTab(self._tab_overview(r), "Огляд")
        tabs.addTab(self._tab_recommendations(r), "Рекомендації")
        tabs.addTab(self._tab_ai(r), "Аналіз ШІ")
        tabs.addTab(self._tab_details(r), "Деталі")
        self.detail_layout.addWidget(tabs, 1)

    def _team_block(self, title, heroes):
        box = QVBoxLayout()
        box.setSpacing(8)
        box.addWidget(card_title(title))
        row = QHBoxLayout(); row.setSpacing(8)
        for name in heroes:
            col = QVBoxLayout(); col.setSpacing(2)
            lbl = QLabel()
            lbl.setFixedSize(48, 48)
            lbl.setPixmap(round_pixmap(hero_pixmap(name, 48), 8))
            lbl.setStyleSheet("border: 1px solid #262b40; border-radius: 8px;")
            col.addWidget(lbl)
            n = QLabel(name)
            n.setStyleSheet("font-size:9px; color:#9095ad; border:none; background:transparent;")
            n.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            n.setWordWrap(True)
            n.setFixedWidth(48)
            col.addWidget(n)
            row.addLayout(col)
        row.addStretch()
        box.addLayout(row)
        return box

    def _tab_overview(self, r):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(14)

        teams_row = QHBoxLayout()
        teams_row.addLayout(self._team_block(f"Ваша команда ({r['side']})", json.loads(r["team_heroes"])))
        teams_row.addLayout(self._team_block(f"Команда суперника", json.loads(r["enemy_heroes"])))
        lay.addLayout(teams_row)
        lay.addWidget(self._hline())

        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)

        reco_card = make_card()
        reco_lay = QVBoxLayout(reco_card)
        reco_lay.setContentsMargins(14, 12, 14, 12)
        reco_lay.addWidget(card_title("Рекомендації (ТОП-5)", "✨"))
        recs = json.loads(r["recommendations"])
        medal_colors = ["#f3c34c", "#c8ccdb", "#cd8b50", "#6c5ce7", "#6c5ce7"]
        for i, rec in enumerate(recs):
            row = QHBoxLayout(); row.setSpacing(8)
            num = QLabel(str(i + 1))
            num.setFixedSize(20, 20)
            num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num.setStyleSheet(f"background-color:{medal_colors[i]}; color:#0c0e16; border-radius:10px; font-weight:800; font-size:10px;")
            row.addWidget(num)
            img = QLabel(); img.setFixedSize(32, 32)
            img.setPixmap(round_pixmap(hero_pixmap(rec["name"], 32), 6))
            row.addWidget(img)
            txt = QVBoxLayout(); txt.setSpacing(0)
            name_lbl = QLabel(rec["name"])
            name_lbl.setStyleSheet("color:#fff; font-weight:700; font-size:12px; border:none; background:transparent;")
            txt.addWidget(name_lbl)
            txt.addWidget(pill(rec["role"]))
            row.addLayout(txt)
            row.addStretch()
            score = QLabel(f"⚡ {rec['score']}%")
            score.setStyleSheet("color:#9d90f5; font-weight:700; font-size:11px; border:none; background:transparent;")
            row.addWidget(score)
            reco_lay.addLayout(row)
        mid_row.addWidget(reco_card, 1)

        radar_card = make_card()
        radar_lay = QVBoxLayout(radar_card)
        radar_lay.setContentsMargins(14, 12, 14, 12)
        radar_lay.addWidget(card_title("Оцінка сил команд", "🎯"))
        radar = json.loads(r["radar"])
        chart = RadarChart(radar["axes"], radar["team"], radar["enemy"])
        radar_lay.addWidget(chart)
        legend = QHBoxLayout()
        legend.addWidget(self._legend_dot("#5ee08a", "Ваша команда"))
        legend.addWidget(self._legend_dot("#ef6f7a", "Суперник"))
        legend.addStretch()
        radar_lay.addLayout(legend)
        dur = QLabel(f"⚡ Тривалість аналізу: {r['duration_s']} секунди")
        dur.setStyleSheet("color:#7c8096; font-size:11px; border:none; background:transparent;")
        radar_lay.addWidget(dur)
        mid_row.addWidget(radar_card, 1)

        lay.addLayout(mid_row)

        concl = make_card()
        cl = QVBoxLayout(concl)
        cl.setContentsMargins(14, 12, 14, 12)
        cl.addWidget(card_title("Короткий висновок", "📝"))
        strengths = json.loads(r["strengths"])
        weaknesses = json.loads(r["weaknesses"])
        text = (f"{strengths[0] if strengths else ''}. "
                f"Команда має перевагу в командних бійках, але варто звернути увагу на "
                f"{weaknesses[0].lower() if weaknesses else 'слабкі місця складу'}.")
        cl.addWidget(body_label(text, size=12))
        lay.addWidget(concl)
        lay.addStretch()

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); scroll.setWidget(w)
        return scroll

    def _legend_dot(self, color, text):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        dot = QLabel(); dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color:{color}; border-radius:5px;")
        lay.addWidget(dot)
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#aeb2c4; font-size:11px; border:none; background:transparent;")
        lay.addWidget(lbl)
        return w

    def _tab_recommendations(self, r):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(8)
        recs = json.loads(r["recommendations"])
        for i, rec in enumerate(recs):
            row = make_card()
            row.setStyleSheet("QFrame { background-color: #0f1220; border: 1px solid #1f2436; border-radius: 10px; }")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(12, 10, 12, 10)
            img = QLabel(); img.setFixedSize(40, 40)
            img.setPixmap(round_pixmap(hero_pixmap(rec["name"], 40), 8))
            rl.addWidget(img)
            txt = QVBoxLayout()
            name_lbl = QLabel(f"{i+1}. {rec['name']}")
            name_lbl.setStyleSheet("color:#fff; font-weight:700; font-size:13px; border:none; background:transparent;")
            txt.addWidget(name_lbl)
            txt.addWidget(body_label(rec["explanation"], size=11, color="#9095ad"))
            rl.addLayout(txt, 1)
            score = QLabel(f"{rec['score']}%")
            score.setStyleSheet("color:#9d90f5; font-weight:800; font-size:14px; border:none; background:transparent;")
            rl.addWidget(score)
            lay.addWidget(row)
        lay.addStretch()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); scroll.setWidget(w)
        return scroll

    def _tab_ai(self, r):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.addWidget(card_title("Пояснення від ШІ", "💬"))
        lay.addWidget(body_label(r["ai_explanation"], size=13))
        lay.addWidget(pill("Згенеровано з використанням Gemini 3 Pro"), alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addStretch()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); scroll.setWidget(w)
        return scroll

    def _tab_details(self, r):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(10)
        grid = QGridLayout()
        fields = [
            ("Сторона", r["side"]), ("Результат", "Перемога" if r["result"] == "win" else "Поразка"),
            ("Рахунок", f"{r['score_team']} - {r['score_enemy']}"),
            ("Тривалість аналізу", f"{r['duration_s']} с"),
            ("Дата", r["created_at"]),
        ]
        for i, (k, v) in enumerate(fields):
            grid.addWidget(small_label(k), i, 0)
            vl = QLabel(str(v))
            vl.setStyleSheet("color:#e7e9f3; font-size:12px; font-weight:600; border:none; background:transparent;")
            grid.addWidget(vl, i, 1)
        lay.addLayout(grid)
        lay.addWidget(self._hline())
        lay.addWidget(card_title("Контрпіки проти вас", "⚠"))
        counters = json.loads(r["counters"])
        if counters:
            for c in counters:
                lay.addWidget(body_label(f"• {c['hero']} — {c['desc']}", size=12))
        else:
            lay.addWidget(small_label("Немає даних"))
        lay.addWidget(card_title("Синергії вашої команди", "🤝"))
        syns = json.loads(r["synergies"])
        if syns:
            for s in syns:
                lay.addWidget(body_label(f"• {' + '.join(s['pair'])} — {s['desc']}", size=12))
        else:
            lay.addWidget(small_label("Немає даних"))
        lay.addStretch()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff); scroll.setWidget(w)
        return scroll

    def _hline(self):
        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background-color:#1f2436; border:none;")
        return line

    def _delete(self, rid):
        confirm = QMessageBox.question(self, "Видалити запис", "Видалити цей запис історії?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            db.delete_analysis(rid)
            self.selected_id = None
            self.refresh()
