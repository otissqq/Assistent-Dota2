from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QLineEdit, QListWidget, QListWidgetItem, QScrollArea, QFrame, QMessageBox)
from PyQt6.QtCore import Qt

from ui.widgets import make_card, card_title, small_label, body_label, pill, hero_pixmap, hero_pixmap_full, round_pixmap, page_title
from data.heroes_data import HEROES, ATTR_COLORS
import database as db
from ui import theme
from services import stratz_service

PAGE_SIZE = 8


class StatisticsPage(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.all_heroes = list(HEROES)
        self.heroes = list(self.all_heroes)
        self.page = 0
        self.selected_hero = self.heroes[0] if self.heroes else None
        self._build_ui()
        self.refresh_list()
        if self.selected_hero:
            self.render_detail(self.selected_hero)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(18)

        header = QVBoxLayout()
        header.addWidget(page_title("Статистика героїв", "statistic_actual.png", "📊"))
        sub = small_label("Актуальна статистика героїв з STRATZ")
        header.addWidget(sub)
        outer.addLayout(header)

        body = QHBoxLayout()
        body.setSpacing(16)

        left = QVBoxLayout()
        left.setSpacing(10)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍  Пошук героя...")
        self.search_edit.textChanged.connect(self._on_search)
        left.addWidget(self.search_edit)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_select)
        left.addWidget(self.list_widget, 1)

        pager = QHBoxLayout()
        pager.addStretch()
        self.prev_btn = QPushButton("‹")
        self.prev_btn.clicked.connect(self.prev_page)
        self.page_label = QLabel("1")
        self.page_label.setStyleSheet("color:#fff; font-weight:700; padding: 0 10px; border:none; background:transparent;")
        self.next_btn = QPushButton("›")
        self.next_btn.clicked.connect(self.next_page)
        for b in (self.prev_btn, self.next_btn):
            b.setFixedSize(30, 30)
            b.setStyleSheet("QPushButton { background:#181c2c; border:1px solid #2a2f45; border-radius:6px; color:#fff; } QPushButton:hover{background:#20253a;}")
        pager.addWidget(self.prev_btn)
        pager.addWidget(self.page_label)
        pager.addWidget(self.next_btn)
        pager.addStretch()
        left.addLayout(pager)

        left_wrap = QWidget(); left_wrap.setLayout(left)
        left_wrap.setFixedWidth(420)

        self.detail_card = make_card()
        self.detail_layout = QVBoxLayout(self.detail_card)
        self.detail_layout.setContentsMargins(20, 18, 20, 18)
        self.detail_layout.setSpacing(12)
        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        detail_scroll.setWidget(self.detail_card)

        body.addWidget(left_wrap)
        body.addWidget(detail_scroll, 1)
        outer.addLayout(body, 1)

    # ---------------------------------------------------------------- list
    def _on_search(self, text):
        text = text.lower().strip()
        self.heroes = [h for h in self.all_heroes if text in h["name"].lower()]
        self.page = 0
        self.refresh_list()
        if self.heroes:
            self.selected_hero = self.heroes[0]
            self.render_detail(self.selected_hero)

    def refresh_list(self):
        self.list_widget.clear()
        start = self.page * PAGE_SIZE
        page_items = self.heroes[start:start + PAGE_SIZE]
        for h in page_items:
            item = QListWidgetItem()
            w = self._row_widget(h)
            from PyQt6.QtCore import QSize
            item.setSizeHint(QSize(w.sizeHint().width(), 72))
            item.setData(Qt.ItemDataRole.UserRole, h["name"])
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, w)
        total_pages = max(1, (len(self.heroes) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page_label.setText(f"{self.page + 1} / {total_pages}")

    def _row_widget(self, h):
        w = QWidget()
        w.setFixedHeight(72)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)
        img = QLabel(); img.setFixedSize(44, 44)
        img.setPixmap(round_pixmap(hero_pixmap_full(h["name"], 44), 8))
        img.setStyleSheet("border: 1px solid #262b40; border-radius: 8px; background: transparent;")
        lay.addWidget(img, 0, Qt.AlignmentFlag.AlignVCenter)

        txt = QVBoxLayout(); txt.setSpacing(2)
        name_lbl = QLabel(h["name"])
        name_lbl.setWordWrap(True)
        name_lbl.setStyleSheet("color:#fff; font-weight:700; font-size:13px; border:none; background:transparent;")
        txt.addWidget(name_lbl)
        sub_lbl = QLabel(f"{h['role']} · {h['attr']}")
        sub_lbl.setStyleSheet("color:#7c8096; font-size:11px; border:none; background:transparent;")
        txt.addWidget(sub_lbl)
        lay.addLayout(txt, 1)
        lay.setAlignment(txt, Qt.AlignmentFlag.AlignVCenter)

        stats = QVBoxLayout(); stats.setSpacing(2)
        win_lbl = QLabel(f"{h['win']}%")
        win_lbl.setStyleSheet("color:#5ee08a; font-weight:700; font-size:12px; border:none; background:transparent;")
        win_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        stats.addWidget(win_lbl)
        wr_lbl = QLabel("Win Rate")
        wr_lbl.setStyleSheet("color:#5a5f78; font-size:9px; border:none; background:transparent;")
        wr_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        stats.addWidget(wr_lbl)
        lay.addLayout(stats)
        lay.setAlignment(stats, Qt.AlignmentFlag.AlignVCenter)
        w.setLayout(lay)
        return w

    def _on_select(self, item):
        if item is None:
            return
        name = item.data(Qt.ItemDataRole.UserRole)
        hero = next((h for h in self.heroes if h["name"] == name), None)
        if hero is None:
            hero = next((h for h in self.all_heroes if h["name"] == name), None)
        if hero:
            self.selected_hero = hero
            self.render_detail(hero)

    def select_hero(self, name):
        """Jumps straight to a given hero's detail view -- used when the
        user clicks a hero elsewhere in the app (e.g. a Top-5 draft
        recommendation) instead of popping up a separate dialog."""
        hero = next((h for h in self.all_heroes if h["name"] == name), None)
        if not hero:
            return
        self.search_edit.blockSignals(True)
        self.search_edit.clear()
        self.search_edit.blockSignals(False)
        self.heroes = list(self.all_heroes)
        idx = self.heroes.index(hero)
        self.page = idx // PAGE_SIZE
        self.refresh_list()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == name:
                self.list_widget.setCurrentItem(item)
                break
        self.selected_hero = hero
        self.render_detail(hero)

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.refresh_list()

    def next_page(self):
        total_pages = max(1, (len(self.heroes) + PAGE_SIZE - 1) // PAGE_SIZE)
        if self.page < total_pages - 1:
            self.page += 1
            self.refresh_list()

    # ---------------------------------------------------------------- detail
    def _clear_detail(self):
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                self._clear_rec(item.layout())

    def _clear_rec(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                w = item.widget()
                w.setParent(None)
                w.deleteLater()
            elif item.layout():
                self._clear_rec(item.layout())

    def render_detail(self, h):
        self._clear_detail()

        header = QHBoxLayout()
        img = QLabel(); img.setFixedSize(140, 140)
        img.setPixmap(round_pixmap(hero_pixmap_full(h["name"], 140), 14))
        img.setStyleSheet(f"border: 2px solid {ATTR_COLORS.get(h['attr'], '#4F46E5')}; border-radius: 14px; background: transparent;")
        header.addWidget(img)

        info = QVBoxLayout(); info.setSpacing(4)
        name_lbl = QLabel(h["name"])
        name_lbl.setStyleSheet("color:#fff; font-size:24px; font-weight:800; border:none; background:transparent;")
        info.addWidget(name_lbl)
        attr_lbl = QLabel(h["attr"])
        attr_lbl.setStyleSheet(f"color:{ATTR_COLORS.get(h['attr'],'#4F46E5')}; font-weight:700; font-size:13px; border:none; background:transparent;")
        info.addWidget(attr_lbl)
        tag_row = QHBoxLayout()
        tag_row.addWidget(pill(h["role"]))
        tag_row.addWidget(pill(h["tag"]))
        tag_row.addStretch()
        info.addLayout(tag_row)
        diff_row = QHBoxLayout()
        diff_row.addWidget(small_label("Складність"))
        diff_row.addStretch()
        info.addLayout(diff_row)
        diamonds = "".join("◆" if i < h["difficulty"] else "◇" for i in range(5))
        diff_lbl = QLabel(diamonds)
        diff_lbl.setStyleSheet("color:#4F46E5; font-size:14px; letter-spacing:2px; border:none; background:transparent;")
        info.addWidget(diff_lbl)
        info.addStretch()
        header.addLayout(info, 1)
        self.detail_layout.addLayout(header)

        # stat tiles
        stat_row = QHBoxLayout(); stat_row.setSpacing(12)
        stat_row.addWidget(self._stat_tile(f"{h['win']}%", "Win Rate", "#5ee08a"))
        stat_row.addWidget(self._stat_tile(f"{h['pick']}%", "Pick Rate", "#ffffff"))
        stat_row.addWidget(self._stat_tile(f"{h['ban']}%", "Ban Rate", "#ef6f7a"))
        self.detail_layout.addLayout(stat_row)

        # role / attack row
        meta_card = make_card()
        meta_lay = QHBoxLayout(meta_card)
        meta_lay.setContentsMargins(16, 12, 16, 12)
        meta_lay.addLayout(self._meta_field("⚙ Основна роль", h["role"]))
        meta_lay.addLayout(self._meta_field("🗡 Атака", h["attack"]))
        self.detail_layout.addWidget(meta_card)

        meta_card2 = make_card()
        meta_lay2 = QHBoxLayout(meta_card2)
        meta_lay2.setContentsMargins(16, 12, 16, 12)
        meta_lay2.addLayout(self._meta_field("➕ Додаткові ролі", h["tag"]))
        meta_lay2.addLayout(self._meta_field("📈 Складність", ["Низька", "Низька", "Середня", "Середня", "Висока"][h["difficulty"] - 1]))
        self.detail_layout.addWidget(meta_card2)

        desc_card = make_card()
        desc_lay = QVBoxLayout(desc_card)
        desc_lay.setContentsMargins(20, 18, 20, 18)
        desc_lay.addWidget(card_title("Опис"))
        desc_lay.addWidget(body_label(h["desc"], size=13))
        self.detail_layout.addWidget(desc_card)

        abilities_card = make_card()
        ab_lay = QVBoxLayout(abilities_card)
        ab_lay.setContentsMargins(20, 18, 20, 18)
        ab_lay.setSpacing(12)
        ab_lay.addWidget(card_title("Основні здібності"))
        ab_row = QHBoxLayout(); ab_row.setSpacing(10)
        for glyph in self._ability_glyphs(h):
            ab_row.addWidget(self._ability_icon(glyph, ATTR_COLORS.get(h["attr"], "#4F46E5")))
        ab_row.addStretch()
        ab_lay.addLayout(ab_row)
        self.detail_layout.addWidget(abilities_card)

        refresh_row = QHBoxLayout()
        refresh_btn = QPushButton("🔄  Оновити статистику")
        refresh_btn.setProperty("class", "primary")
        refresh_btn.setStyleSheet("""
            QPushButton { background-color: #4F46E5; color: white; border-radius: 8px;
                padding: 10px 18px; font-weight: 700; border: none; }
            QPushButton:hover { background-color: #6366F1; }
        """)
        refresh_btn.clicked.connect(self._on_refresh_stats)
        refresh_row.addWidget(refresh_btn)
        refresh_row.addStretch()
        self.last_update_lbl = small_label(f"Останнє оновлення: {db.get_setting('last_stratz_sync') or '—'}")
        refresh_row.addWidget(self.last_update_lbl)
        self.detail_layout.addLayout(refresh_row)
        self.detail_layout.addStretch()

    def _stat_tile(self, value, label, color):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        v = QLabel(value)
        v.setStyleSheet(f"color:{color}; font-size:22px; font-weight:800; border:none; background:transparent;")
        lay.addWidget(v)
        l = QLabel(label)
        l.setStyleSheet("color:#7c8096; font-size:11px; border:none; background:transparent;")
        lay.addWidget(l)
        return card

    _ABILITY_GLYPH_POOL = ["⚡", "🔥", "❄", "🌪", "☄", "🌙", "⚔", "🌊", "♦", "✦", "🛡", "☠"]

    def _ability_glyphs(self, h):
        """Deterministic (but varied) set of 4 glyphs per hero, standing in
        for real ability icons (no per-ability art is shipped with the app).
        The 4th slot is always a shield, echoing the ultimate's usual
        gameplay weight."""
        seed = sum(ord(c) for c in h["name"])
        pool = self._ABILITY_GLYPH_POOL
        picks = []
        i = seed
        while len(picks) < 3:
            g = pool[i % len(pool)]
            if g not in picks:
                picks.append(g)
            i += 7
        picks.append("🛡")
        return picks

    def _ability_icon(self, glyph, accent):
        lbl = QLabel(glyph)
        lbl.setFixedSize(56, 56)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"""
            QLabel {{
                font-size: 22px;
                background-color: rgba(22, 27, 34, 0.9);
                border: 1px solid {accent};
                border-radius: 10px;
            }}
        """)
        return lbl

    def _meta_field(self, label, value):
        box = QVBoxLayout(); box.setSpacing(4)
        box.addWidget(small_label(label))
        v = QLabel(value)
        v.setStyleSheet("color:#e7e9f3; font-weight:700; font-size:13px; border:none; background:transparent;")
        box.addWidget(v)
        return box

    def _on_refresh_stats(self):
        api_key = db.get_setting("stratz_api_key")
        heroes, used_live, msg = stratz_service.fetch_hero_stats(api_key)

        if not used_live:
            QMessageBox.warning(
                self,
                "STRATZ",
                f"{msg}\n\nСписок героїв не буде перезаписаний кешем."
            )
            return

        ts = stratz_service.now_str()
        db.set_setting("last_stratz_sync", ts)
        if hasattr(self, "last_update_lbl"):
            self.last_update_lbl.setText(f"Останнє оновлення: {ts}")

        self.all_heroes = list(heroes)

        text = self.search_edit.text().lower().strip()
        if text:
            self.heroes = [h for h in self.all_heroes if text in h["name"].lower()]
        else:
            self.heroes = list(self.all_heroes)

        self.page = 0
        self.refresh_list()

        selected_name = self.selected_hero.get("name") if self.selected_hero else None
        selected = next((h for h in self.heroes if h["name"] == selected_name), None)
        if selected is None and self.heroes:
            selected = self.heroes[0]

        if selected:
            self.selected_hero = selected
            self.render_detail(selected)

        QMessageBox.information(self, "Оновлення статистики", msg)
