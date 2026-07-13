import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QLineEdit, QComboBox, QListWidget, QListWidgetItem,
                              QTabWidget, QScrollArea, QFrame, QMessageBox, QGridLayout)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from ui.widgets import (make_card, card_title, small_label, body_label, pill,
                         hero_pixmap, hero_pixmap_full, round_pixmap, RadarChart,
                         load_pixmap, icon_label, page_title)
from ui import theme
import database as db

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _side_icon(filename, size=16):
    pix = load_pixmap(os.path.join(ASSETS_DIR, filename))
    if pix.isNull():
        return None
    pix = pix.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                      Qt.TransformationMode.SmoothTransformation)
    x = max(0, (pix.width() - size) // 2)
    y = max(0, (pix.height() - size) // 2)
    return QIcon(pix.copy(x, y, size, size))


def _side_icon_label(side, size=16):
    icon = _side_icon("radiant_logo.jpeg" if side == "Radiant" else "dire_logo.jpeg", size)
    lbl = QLabel()
    lbl.setFixedSize(size, size)
    if icon:
        lbl.setPixmap(icon.pixmap(size, size))
    lbl.setStyleSheet("border:none; background:transparent;")
    return lbl


def _side_label(side, size=13):
    """A small 'Radiant'/'Dire' label using the real faction logo image
    instead of an emoji glyph."""
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(5)
    icon = _side_icon("radiant_logo.jpeg" if side == "Radiant" else "dire_logo.jpeg", size)
    if icon:
        ic_lbl = QLabel()
        ic_lbl.setFixedSize(size, size)
        ic_lbl.setPixmap(icon.pixmap(size, size))
        lay.addWidget(ic_lbl)
    text = QLabel(side)
    text.setStyleSheet(f"font-size:11px; font-weight:700; color:{'#5ee08a' if side == 'Radiant' else '#ef6f7a'}; border:none; background:transparent;")
    lay.addWidget(text)
    return w


class HistoryPage(QWidget):
    def __init__(self, app_state, parent=None, show_header=True):
        super().__init__(parent)
        self.app_state = app_state
        self.selected_id = None
        self._show_header = show_header
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0) if not self._show_header else outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(18)

        if self._show_header:
            header = QVBoxLayout()
            header.addWidget(page_title("Історія аналізів", "history_icon.webp", "🕘"))
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
        detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
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
        top.addWidget(_side_label(r["side"]))
        lay.addLayout(top)


        heroes = json.loads(r["team_heroes"])
        row = QHBoxLayout(); row.setSpacing(6)
        row.setContentsMargins(0, 0, 0, 0)
        for name in heroes[:6]:
            lbl = QLabel()
            lbl.setFixedSize(38, 38)
            lbl.setPixmap(round_pixmap(hero_pixmap_full(name, 38), 8))
            lbl.setStyleSheet("border: 1px solid #262b40; border-radius: 8px; background: transparent;")
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
        title_lbl = QLabel("Аналіз драфту")
        title_lbl.setStyleSheet(
            "font-size:18px; font-weight:800; color:#ffffff; border:none; background:transparent;"
        )
        result_row.addWidget(title_lbl)
        result_row.addWidget(_side_label(r["side"], size=16))
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
        row = QHBoxLayout(); row.setSpacing(6)
        for name in heroes:
            col = QVBoxLayout(); col.setSpacing(2)
            lbl = QLabel()
            lbl.setFixedSize(44, 44)
            lbl.setPixmap(round_pixmap(hero_pixmap_full(name, 44), 8))
            lbl.setStyleSheet("border: 1px solid #262b40; border-radius: 8px; background: transparent;")
            col.addWidget(lbl)
            n = QLabel(name)
            n.setStyleSheet("font-size:9px; color:#9095ad; border:none; background:transparent;")
            n.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            n.setWordWrap(True)
            n.setFixedWidth(44)
            col.addWidget(n)
            row.addLayout(col)
        row.addStretch()
        row_holder = QWidget()
        row_holder.setLayout(row)
        # A horizontal scroll area means five hero portraits are never
        # squeezed/clipped by the panel, even when the History dialog is
        # narrower than the "team of five" content -- previously they
        # would just get cut off at the panel edge.
        scroll = QScrollArea()
        scroll.setWidget(row_holder)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(84)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        box.addWidget(scroll)
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
        reco_lay.addWidget(card_title("Рекомендації (ТОП-5)", "recomendation_default.png"))
        recs = json.loads(r["recommendations"])
        medal_colors = ["#f3c34c", "#c8ccdb", "#cd8b50", "#4F46E5", "#4F46E5"]
        for i, rec in enumerate(recs):
            row = QHBoxLayout(); row.setSpacing(8)
            num = QLabel(str(i + 1))
            num.setFixedSize(20, 20)
            num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num.setStyleSheet(f"background-color:{medal_colors[i]}; color:#0c0e16; border-radius:10px; font-weight:800; font-size:10px;")
            row.addWidget(num)
            img = QLabel(); img.setFixedSize(36, 36)
            img.setPixmap(round_pixmap(hero_pixmap_full(rec["name"], 36), 7))
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
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); scroll.setWidget(w)
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
            img = QLabel(); img.setFixedSize(44, 44)
            img.setPixmap(round_pixmap(hero_pixmap_full(rec["name"], 44), 9))
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
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); scroll.setWidget(w)
        return scroll

    def _tab_ai(self, r):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.addWidget(card_title("Пояснення від ШІ", "recomendation_ai.jpg"))
        lay.addWidget(body_label(r["ai_explanation"], size=13))
        lay.addWidget(pill("Згенеровано з використанням Gemini 3 Pro"), alignment=Qt.AlignmentFlag.AlignLeft)
        lay.addStretch()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); scroll.setWidget(w)
        return scroll

    def _detail_field_box(self, label, value, value_color=None, icon=None):
        box = QFrame()
        box.setStyleSheet(f"""
            QFrame {{ background-color:#0f1220; border:1px solid #1f2436; border-radius:10px; }}
        """)
        lay = QHBoxLayout(box)
        lay.setContentsMargins(14, 11, 14, 11)
        lay.setSpacing(10)
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#8a8fa8; font-size:12px; font-weight:600; border:none; background:transparent;")
        lay.addWidget(lbl)
        lay.addStretch()
        if icon is not None:
            lay.addWidget(icon)
        vl = QLabel(str(value))
        vl.setStyleSheet(f"color:{value_color or '#e7e9f3'}; font-size:13px; font-weight:800; border:none; background:transparent;")
        lay.addWidget(vl)
        return box

    def _tab_details(self, r):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 12, 0, 0)
        lay.setSpacing(10)

        side = r["side"]
        side_color = "#5ee08a" if side == "Radiant" else "#ef6f7a"
        is_win = r["result"] == "win"
        result_color = "#5ee08a" if is_win else "#ef6f7a"

        lay.addWidget(self._detail_field_box("Сторона", side, value_color=side_color, icon=_side_icon_label(side)))
        lay.addWidget(self._detail_field_box("Рахунок", f"{r['score_team']} - {r['score_enemy']}"))
        lay.addWidget(self._detail_field_box("Тривалість аналізу", f"{r['duration_s']} с"))
        lay.addWidget(self._detail_field_box("Дата", r["created_at"]))
        lay.addWidget(self._hline())
        lay.addWidget(card_title("Контрпіки проти вас", "counterpick.jpeg"))
        counters = json.loads(r["counters"])
        if counters:
            for c in counters:
                lay.addWidget(body_label(f"• {c['hero']} — {c['desc']}", size=12))
        else:
            lay.addWidget(small_label("Немає даних"))
        lay.addWidget(card_title("Синергії вашої команди", "synergi.jpg"))
        syns = json.loads(r["synergies"])
        if syns:
            for s in syns:
                lay.addWidget(body_label(f"• {' + '.join(s['pair'])} — {s['desc']}", size=12))
        else:
            lay.addWidget(small_label("Немає даних"))
        lay.addStretch()
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded); scroll.setWidget(w)
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


class HistoryDialog(QWidget):
    """
    "Історія аналізів" as a floating overlay on top of the app, instead of a
    permanent nav-bar page: a rounded, drop-shadowed card with its own
    title bar (icon + title + ✕ close) and a footer "Закрити" button,
    shown application-modal above whatever page the user was on.
    """
    def __init__(self, app_state, parent=None):
        super().__init__(parent, Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Історія аналізів")

        t = theme.current()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)

        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{ background: {t['bg']}; border: 1px solid #2a2f45; border-radius: 20px; }}
        """)
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect
        from PyQt6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 16)
        shadow.setColor(QColor(0, 0, 0, 180))
        card.setGraphicsEffect(shadow)
        outer.addWidget(card)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        # ---- title bar --------------------------------------------------
        bar = QWidget()
        bar.setStyleSheet("background: transparent; border-top-left-radius:20px; border-top-right-radius:20px;")
        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(22, 18, 16, 12)
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_icon = icon_label("history_icon.webp", size=22, radius=5, fallback_emoji="🕘", fallback_bg="transparent")
        title_row.addWidget(title_icon)
        title = QLabel("Історія аналізів")
        title.setStyleSheet(f"font-size:18px; font-weight:800; color:{t['text_bright']}; border:none; background:transparent;")
        title_row.addWidget(title)
        bar_lay.addLayout(title_row)
        bar_lay.addStretch()
        close_btn = QPushButton("✕")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton { background:transparent; border:none; color:#8a8fa8; font-size:14px; border-radius:6px; }
            QPushButton:hover { background:#20253a; color:#fff; }
        """)
        close_btn.clicked.connect(self.close)
        bar_lay.addWidget(close_btn)
        card_lay.addWidget(bar)

        line = QFrame(); line.setFixedHeight(1); line.setStyleSheet("background:#1f2436; border:none;")
        card_lay.addWidget(line)

        # ---- body: the existing history UI, header stripped since this
        # dialog already has its own title bar ---------------------------
        self.history_page = HistoryPage(app_state, show_header=False)
        card_lay.addWidget(self.history_page, 1)

        line2 = QFrame(); line2.setFixedHeight(1); line2.setStyleSheet("background:#1f2436; border:none;")
        card_lay.addWidget(line2)

        # ---- footer -------------------------------------------------
        footer = QWidget()
        footer_lay = QHBoxLayout(footer)
        footer_lay.setContentsMargins(22, 12, 22, 16)
        footer_lay.addStretch()
        close_footer_btn = QPushButton("Закрити")
        close_footer_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_footer_btn.setMinimumHeight(38)
        close_footer_btn.setStyleSheet(f"""
            QPushButton {{ background:{t['accent']}; color:#fff; border:none; border-radius:8px;
                padding:8px 22px; font-weight:700; font-size:13px; }}
            QPushButton:hover {{ background:{t['accent_hover']}; }}
        """)
        close_footer_btn.clicked.connect(self.close)
        footer_lay.addWidget(close_footer_btn)
        card_lay.addWidget(footer)

        self._size_to_parent(parent)

    def _size_to_parent(self, parent):
        if parent is not None:
            pw, ph = parent.width(), parent.height()
        else:
            pw, ph = 1340, 860
        w = max(900, min(1280, int(pw * 0.92)))
        h = max(600, min(860, int(ph * 0.9)))
        self.resize(w, h)
        if parent is not None:
            self.move(parent.geometry().center() - self.rect().center())

    def select_record(self, record_id):
        """Pre-selects and shows the given record's detail (used when
        opening the dialog from a 'view details' click elsewhere)."""
        rec = db.get_analysis(record_id)
        if rec:
            self.history_page.selected_id = record_id
            self.history_page._render_detail(rec)
