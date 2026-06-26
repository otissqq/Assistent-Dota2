import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QLineEdit, QScrollArea, QWidget, QFrame, QComboBox,
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from core.database import DatabaseManager

class HeroCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, hero_data, parent=None):
        super().__init__(parent)
        self.hero_data = hero_data
        self.hero_name = hero_data.get('localized_name', '')
        self.setObjectName("heroCard")
        self.setFixedSize(100, 120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Placeholder для иконки
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(88, 66)
        self.icon_label.setStyleSheet("background-color: #2a2a2a; border-radius: 6px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Показываем первые буквы имени как placeholder
        initials = ''.join([w[0] for w in self.hero_name.split()[:2]]).upper()
        self.icon_label.setText(f"<span style='font-size:18px; color:#888;'>{initials}</span>")

        self.name_label = QLabel(self.hero_name)
        self.name_label.setObjectName("heroName")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)

        # Роль
        roles = hero_data.get('roles', [])
        role_text = roles[0] if roles else ""
        self.role_label = QLabel(role_text)
        self.role_label.setObjectName("heroRole")
        self.role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Winrate
        winrate = hero_data.get('winrate', 50)
        color = "#27ae60" if winrate >= 52 else "#f39c12" if winrate >= 48 else "#e74c3c"
        self.winrate_label = QLabel(f"{winrate:.1f}%")
        self.winrate_label.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
        self.winrate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.role_label)
        layout.addWidget(self.winrate_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.hero_name)
        super().mousePressEvent(event)

class HeroSelectorDialog(QDialog):
    hero_selected = pyqtSignal(str)

    def __init__(self, translator, parent=None, exclude_heroes=None):
        super().__init__(parent)
        self.translator = translator
        self.exclude = exclude_heroes or []
        self.setWindowTitle(translator.tr("select_hero"))
        self.setMinimumSize(900, 700)
        self.setMaximumSize(1200, 900)
        self.db = DatabaseManager()
        self._setup_ui()
        self._load_heroes()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Поиск
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(self.translator.tr("search_hero"))
        self.search_edit.setMinimumHeight(36)
        self.search_edit.textChanged.connect(self._filter_heroes)

        self.role_filter = QComboBox()
        self.role_filter.addItem(self.translator.tr("all_roles"), "")
        self.role_filter.addItem(self.translator.tr("carry"), "Carry")
        self.role_filter.addItem(self.translator.tr("mid"), "Nuker")
        self.role_filter.addItem(self.translator.tr("offlane"), "Initiator")
        self.role_filter.addItem(self.translator.tr("support"), "Support")
        self.role_filter.addItem(self.translator.tr("hard_support"), "Disabler")
        self.role_filter.setMinimumHeight(36)
        self.role_filter.currentIndexChanged.connect(self._filter_heroes)

        search_layout.addWidget(self.search_edit, 3)
        search_layout.addWidget(self.role_filter, 1)
        layout.addLayout(search_layout)

        # Счетчик
        self.count_label = QLabel("0 heroes")
        self.count_label.setObjectName("subtitle")
        layout.addWidget(self.count_label)

        # Скролл с героями
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)

        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll)

        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _load_heroes(self):
        self.all_heroes = self.db.get_cached_heroes()
        self._filter_heroes()

    def _filter_heroes(self):
        # Очищаем сетку
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        search = self.search_edit.text().lower()
        role = self.role_filter.currentData()

        filtered = []
        for h in self.all_heroes:
            name = h.get('localized_name', '').lower()
            name_ru = h.get('localized_name_ru', '').lower()
            if search and search not in name and search not in name_ru:
                continue
            if h.get('localized_name') in self.exclude:
                continue
            if role and role not in h.get('roles', []):
                continue
            filtered.append(h)

        self.count_label.setText(f"{len(filtered)} heroes")

        cols = 7
        for i, hero in enumerate(filtered):
            card = HeroCard(hero)
            card.clicked.connect(self._on_hero_clicked)
            self.grid_layout.addWidget(card, i // cols, i % cols)

    def _on_hero_clicked(self, hero_name):
        self.hero_selected.emit(hero_name)
        self.accept()
