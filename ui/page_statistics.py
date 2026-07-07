from PIL.Image import item
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QFrame,
    QScrollArea, QMessageBox
)

from PyQt6.QtCore import Qt

from ui.widgets import make_card, card_title, small_label, body_label, pill, hero_pixmap, round_pixmap
from data.heroes_data import HEROES, ATTR_COLORS
import database as db
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
        self.render_detail(self.selected_hero)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(14)

        header = QVBoxLayout()
        title = QLabel("📊  Статистика героїв")
        title.setStyleSheet("font-size:20px; font-weight:700; color:#fff; border:none; background:transparent;")
        header.addWidget(title)
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
        detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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
            item.setSizeHint(QSize(w.sizeHint().width(), 70))
            item.setData(Qt.ItemDataRole.UserRole, h["name"])
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, w)
        total_pages = max(1, (len(self.heroes) + PAGE_SIZE - 1) // PAGE_SIZE)
        self.page_label.setText(f"{self.page + 1} / {total_pages}")

    def _row_widget(self, h):
        w = QWidget()
        w.setMinimumHeight(64)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(10)
        img = QLabel(); img.setFixedSize(44, 44)
        img.setPixmap(round_pixmap(hero_pixmap(h["name"], 44), 8))
        img.setStyleSheet("border: 1px solid #262b40; border-radius: 8px;")
        lay.addWidget(img)

        txt = QVBoxLayout(); txt.setSpacing(2)
        name_lbl = QLabel(h["name"])
        name_lbl.setStyleSheet("color:#fff; font-weight:700; font-size:13px; border:none; background:transparent;")
        txt.addWidget(name_lbl)
        sub_lbl = QLabel(f"{h['role']} · {h['attr']}")
        sub_lbl.setStyleSheet("color:#7c8096; font-size:11px; border:none; background:transparent;")
        txt.addWidget(sub_lbl)
        lay.addLayout(txt, 1)

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
        img.setPixmap(round_pixmap(hero_pixmap(h["name"], 140), 14))
        img.setStyleSheet(f"border: 2px solid {ATTR_COLORS.get(h['attr'], '#6c5ce7')}; border-radius: 14px;")
        header.addWidget(img)

        info = QVBoxLayout(); info.setSpacing(4)
        name_lbl = QLabel(h["name"])
        name_lbl.setStyleSheet("color:#fff; font-size:24px; font-weight:800; border:none; background:transparent;")
        info.addWidget(name_lbl)
        attr_lbl = QLabel(h["attr"])
        attr_lbl.setStyleSheet(f"color:{ATTR_COLORS.get(h['attr'],'#6c5ce7')}; font-weight:700; font-size:13px; border:none; background:transparent;")
        info.addWidget(attr_lbl)
        tag_row = QHBoxLayout()
        tag_row.addWidget(pill(h["role"]))
        tag_row.addWidget(pill(h["tag"]))
        tag_row.addStretch()
        info.addLayout(tag_row)
        diff_row = QHBoxLayout()
    
        diff_row.addStretch()
        info.addLayout(diff_row)
      
       
        
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

        
       

        desc_card = make_card()
        desc_lay = QVBoxLayout(desc_card)
        desc_lay.setContentsMargins(16, 14, 16, 14)
        desc_lay.addWidget(card_title("Опис"))
        desc_lay.addWidget(body_label(h["desc"], size=13))
        self.detail_layout.addWidget(desc_card)

        refresh_row = QHBoxLayout()
        refresh_btn = QPushButton("🔄  Оновити статистику")
        refresh_btn.setProperty("class", "primary")
        refresh_btn.setStyleSheet("""
            QPushButton { background-color: #6c5ce7; color: white; border-radius: 8px;
                padding: 10px 18px; font-weight: 700; border: none; }
            QPushButton:hover { background-color: #7b6cf0; }
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

    def _meta_field(self, label, value):
        box = QVBoxLayout(); box.setSpacing(4)
        box.addWidget(small_label(label))
        v = QLabel(value)
        v.setStyleSheet("color:#e7e9f3; font-weight:700; font-size:13px; border:none; background:transparent;")
        box.addWidget(v)
        return box

    def _on_refresh_stats(self):
        try:
            api_key = db.get_setting("stratz_api_key")

            heroes, used_live, msg = stratz_service.fetch_hero_stats(api_key)

            if not used_live:
                QMessageBox.warning(
                    self,
                    "STRATZ",
                    "STRATZ не повернув актуальні дані.\n\n"
                    f"{msg}\n\n"
                    "Список героїв не буде перезаписаний кешем."
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

            if self.heroes:
                self.selected_hero = self.heroes[0]
                self.render_detail(self.selected_hero)

            QMessageBox.information(self, "Оновлення статистики", msg)

        except Exception as e:
            QMessageBox.critical(
                self,
                "Помилка STRATZ",
                f"Не вдалося оновити статистику.\n\nПомилка:\n{e}"
            )