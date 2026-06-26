import sys
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QGridLayout,
    QProgressBar, QTextEdit, QTabWidget, QListWidget, QMessageBox,
    QScrollArea, QSizePolicy, QGraphicsOpacityEffect, QGraphicsDropShadowEffect,
    QFileDialog, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer, QSize
from PyQt6.QtGui import QPixmap, QFont, QColor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from gui.styles import get_theme
from gui.hero_selector_dialog import HeroSelectorDialog
from gui.settings_dialog import SettingsDialog
from core.database import DatabaseManager
from core.draft_logic import DraftEngine
from core.gemini_api import GeminiAnalyzer
from core.hero_recognition import HeroRecognizer
from core.screenshot import ScreenCapture
from config.settings import load_settings, save_settings
from locales.translations import Translator

# ═══════════════════════════════════════════════════════════
# Рабочий поток для анализа
# ═══════════════════════════════════════════════════════════
class AnalysisWorker(QThread):
    finished = pyqtSignal(dict)
    progress = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, engine, radiant, dire, gemini, lang="uk"):
        super().__init__()
        self.engine = engine
        self.radiant = radiant
        self.dire = dire
        self.gemini = gemini
        self.lang = lang

    def run(self):
        try:
            self.progress.emit(25)
            result = self.engine.analyze_draft(self.radiant, self.dire)
            self.progress.emit(60)
            ai_text = self.gemini.generate_analysis(
                self.radiant, self.dire,
                result['radiant_strength'], result['dire_strength'],
                result['radiant_recommendations'],
                self.lang
            )
            self.progress.emit(90)
            result['ai_analysis'] = ai_text
            self.progress.emit(100)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# ═══════════════════════════════════════════════════════════
# Анимированный виджет прогресса
# ═══════════════════════════════════════════════════════════
class AnimatedProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_value = 0
        self._anim = QPropertyAnimation(self, b"value")
        self._anim.setDuration(800)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def setValueAnimated(self, value):
        self._target_value = value
        self._anim.stop()
        self._anim.setStartValue(self.value())
        self._anim.setEndValue(value)
        self._anim.start()

# ═══════════════════════════════════════════════════════════
# Карточка героя с кликом и правым кликом для удаления
# ═══════════════════════════════════════════════════════════
class HeroSlot(QFrame):
    clicked = pyqtSignal(int, str)
    hero_removed = pyqtSignal(int, str)

    def __init__(self, slot_index, team, translator, parent=None):
        super().__init__(parent)
        self.slot_index = slot_index
        self.team = team
        self.translator = translator
        self.hero_name = None
        self.hero_data = None
        self.setObjectName("heroCardEmpty")
        self.setFixedSize(100, 130)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6, 8, 6, 8)
        self.layout.setSpacing(4)

        # Иконка
        self.img_label = QLabel()
        self.img_label.setFixedSize(88, 66)
        self.img_label.setStyleSheet("background-color: #2a2a2a; border-radius: 6px;")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Placeholder текст
        self.placeholder_text = QLabel("+")
        self.placeholder_text.setStyleSheet("font-size: 24px; color: #555555;")
        self.placeholder_text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        img_container = QWidget()
        img_layout = QVBoxLayout(img_container)
        img_layout.setContentsMargins(0, 0, 0, 0)
        img_layout.addWidget(self.img_label)
        img_layout.addWidget(self.placeholder_text)

        self.name_label = QLabel(self.translator.tr("click_to_select"))
        self.name_label.setObjectName("heroName")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)

        self.role_label = QLabel("")
        self.role_label.setObjectName("heroRole")
        self.role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.layout.addWidget(img_container)
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.role_label)

    def set_hero(self, hero_data):
        self.hero_data = hero_data
        self.hero_name = hero_data.get('localized_name', '')
        self.setObjectName("heroCard")
        self.setStyleSheet("")

        initials = ''.join([w[0] for w in self.hero_name.split()[:2]]).upper()
        self.img_label.setText(f"<span style='font-size:20px; color:#aaa; font-weight:bold;'>{initials}</span>")
        self.img_label.setStyleSheet("background-color: #3a3a3a; border-radius: 6px;")
        self.placeholder_text.hide()

        self.name_label.setText(self.hero_name)

        roles = hero_data.get('roles', [])
        self.role_label.setText(roles[0] if roles else "")

        # Цвет рамки по команде
        border_color = "#27ae60" if self.team == "radiant" else "#c0392b"
        self.setStyleSheet(f"""
            HeroSlot {{ 
                background-color: #252525; 
                border: 2px solid {border_color}; 
                border-radius: 8px; 
            }}
            HeroSlot:hover {{ 
                border-color: #e74c3c; 
                background-color: #2d2d2d;
            }}
        """)

    def clear(self):
        self.hero_data = None
        self.hero_name = None
        self.setObjectName("heroCardEmpty")
        self.setStyleSheet("")
        self.img_label.setText("")
        self.img_label.setStyleSheet("background-color: #2a2a2a; border-radius: 6px;")
        self.placeholder_text.show()
        self.name_label.setText(self.translator.tr("click_to_select"))
        self.role_label.setText("")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton and self.hero_name:
            self.hero_removed.emit(self.slot_index, self.team)
            self.clear()
        elif event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.slot_index, self.team)
        super().mousePressEvent(event)

# ═══════════════════════════════════════════════════════════
# Панель ТОП-10 героев меты
# ═══════════════════════════════════════════════════════════
class MetaPanel(QFrame):
    hero_clicked = pyqtSignal(str)

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.setObjectName("panel")
        self.db = DatabaseManager()
        self._setup_ui()
        self._load_meta()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel(self.translator.tr("current_meta"))
        title.setObjectName("title")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        self.meta_grid = QGridLayout()
        self.meta_grid.setSpacing(8)
        layout.addLayout(self.meta_grid)
        layout.addStretch()

    def _load_meta(self):
        heroes = self.db.get_top_heroes(10)

        while self.meta_grid.count():
            item = self.meta_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, hero in enumerate(heroes):
            card = self._create_mini_card(hero)
            self.meta_grid.addWidget(card, i // 5, i % 5)

    def _create_mini_card(self, hero):
        card = QFrame()
        card.setObjectName("heroCard")
        card.setFixedSize(90, 70)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        name = QLabel(hero.get('localized_name', ''))
        name.setObjectName("heroName")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        winrate = hero.get('winrate', 50)
        color = "#27ae60" if winrate >= 53 else "#f39c12" if winrate >= 49 else "#e74c3c"
        rate_label = QLabel(f"{winrate:.1f}%")
        rate_label.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")
        rate_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(name)
        layout.addWidget(rate_label)

        def make_click(h):
            return lambda e: self.hero_clicked.emit(h.get('localized_name', ''))
        card.mousePressEvent = make_click(hero)

        return card

    def refresh(self):
        self._load_meta()

# ═══════════════════════════════════════════════════════════
# Страница анализа матча
# ═══════════════════════════════════════════════════════════
class MatchAnalysisPage(QWidget):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.settings = load_settings()
        self.engine = DraftEngine()
        self.gemini = GeminiAnalyzer(self.settings.get("gemini_model", "gemini-1.5-flash"))
        self.recognizer = HeroRecognizer(self.settings.get("confidence_threshold", 0.65))
        self.capture = ScreenCapture()
        self.db = DatabaseManager()
        self.current_result = None
        self.radiant_slots = []
        self.dire_slots = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # === ЛЕВАЯ ПАНЕЛЬ ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(16)

        # Radiant команда
        radiant_frame = QFrame()
        radiant_frame.setObjectName("panel")
        radiant_layout = QVBoxLayout(radiant_frame)
        radiant_layout.setContentsMargins(16, 16, 16, 16)

        radiant_header = QHBoxLayout()
        radiant_title = QLabel(self.translator.tr("radiant"))
        radiant_title.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 16px;")
        self.radiant_strength = QLabel("Сила: --")
        self.radiant_strength.setStyleSheet("color: #27ae60; font-weight: bold;")
        radiant_header.addWidget(radiant_title)
        radiant_header.addStretch()
        radiant_header.addWidget(self.radiant_strength)
        radiant_layout.addLayout(radiant_header)

        self.radiant_grid = QHBoxLayout()
        self.radiant_grid.setSpacing(10)
        for i in range(5):
            slot = HeroSlot(i, "radiant", self.translator)
            slot.clicked.connect(self._on_slot_clicked)
            slot.hero_removed.connect(self._on_hero_removed)
            self.radiant_slots.append(slot)
            self.radiant_grid.addWidget(slot)
        radiant_layout.addLayout(self.radiant_grid)
        left_layout.addWidget(radiant_frame)

        # Dire команда
        dire_frame = QFrame()
        dire_frame.setObjectName("panel")
        dire_layout = QVBoxLayout(dire_frame)
        dire_layout.setContentsMargins(16, 16, 16, 16)

        dire_header = QHBoxLayout()
        dire_title = QLabel(self.translator.tr("dire"))
        dire_title.setStyleSheet("color: #c0392b; font-weight: bold; font-size: 16px;")
        self.dire_strength = QLabel("Сила: --")
        self.dire_strength.setStyleSheet("color: #c0392b; font-weight: bold;")
        dire_header.addWidget(dire_title)
        dire_header.addStretch()
        dire_header.addWidget(self.dire_strength)
        dire_layout.addLayout(dire_header)

        self.dire_grid = QHBoxLayout()
        self.dire_grid.setSpacing(10)
        for i in range(5):
            slot = HeroSlot(i, "dire", self.translator)
            slot.clicked.connect(self._on_slot_clicked)
            slot.hero_removed.connect(self._on_hero_removed)
            self.dire_slots.append(slot)
            self.dire_grid.addWidget(slot)
        dire_layout.addLayout(self.dire_grid)
        left_layout.addWidget(dire_frame)

        # Кнопки управления
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setSpacing(10)

        self.btn_capture = QPushButton("📷 " + self.translator.tr("capture_screen"))
        self.btn_capture.setObjectName("secondaryButton")
        self.btn_capture.setMinimumHeight(40)
        self.btn_capture.clicked.connect(self.capture_screen)

        self.btn_analyze = QPushButton("⚡ " + self.translator.tr("analyze"))
        self.btn_analyze.setObjectName("primaryButton")
        self.btn_analyze.setMinimumHeight(40)
        self.btn_analyze.clicked.connect(self.run_analysis)

        self.btn_save = QPushButton("💾 " + self.translator.tr("save_analysis"))
        self.btn_save.setMinimumHeight(40)
        self.btn_save.clicked.connect(self.save_analysis)
        self.btn_save.setEnabled(False)

        self.btn_clear = QPushButton("🗑 " + self.translator.tr("clear_all"))
        self.btn_clear.setObjectName("dangerButton")
        self.btn_clear.setMinimumHeight(40)
        self.btn_clear.clicked.connect(self.clear_all)

        btn_layout.addWidget(self.btn_capture)
        btn_layout.addWidget(self.btn_analyze)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_clear)
        left_layout.addWidget(btn_frame)

        # Табы анализа
        self.tabs = QTabWidget()
        self.tab_general = QTextEdit()
        self.tab_general.setReadOnly(True)
        self.tab_general.setPlaceholderText("Натисніть 'Аналізувати' для отримання результатів...")
        self.tabs.addTab(self.tab_general, self.translator.tr("general_analysis"))

        self.tab_comparison = QTextEdit()
        self.tab_comparison.setReadOnly(True)
        self.tabs.addTab(self.tab_comparison, self.translator.tr("comparison"))

        self.tab_graphs = QTextEdit()
        self.tab_graphs.setReadOnly(True)
        self.tab_graphs.setPlaceholderText("Графіки будуть тут...")
        self.tabs.addTab(self.tab_graphs, self.translator.tr("graphs"))

        left_layout.addWidget(self.tabs, 1)

        main_layout.addWidget(left_widget, 3)

        # === ПРАВАЯ ПАНЕЛЬ ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(16)

        # Шанс на победу
        win_frame = QFrame()
        win_frame.setObjectName("panel")
        win_layout = QVBoxLayout(win_frame)
        win_layout.setContentsMargins(16, 16, 16, 16)

        win_title = QLabel(self.translator.tr("win_chance"))
        win_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        win_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        win_layout.addWidget(win_title)

        self.win_bar = AnimatedProgressBar()
        self.win_bar.setRange(0, 100)
        self.win_bar.setValue(50)
        self.win_bar.setTextVisible(True)
        self.win_bar.setFormat("Radiant %p%")
        self.win_bar.setMinimumHeight(28)
        win_layout.addWidget(self.win_bar)

        self.win_details = QLabel("50.0% | 50.0%")
        self.win_details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.win_details.setStyleSheet("color: #888; font-size: 12px;")
        win_layout.addWidget(self.win_details)

        right_layout.addWidget(win_frame)

        # Рекомендации
        rec_frame = QFrame()
        rec_frame.setObjectName("panel")
        rec_layout = QVBoxLayout(rec_frame)
        rec_layout.setContentsMargins(16, 16, 16, 16)

        rec_title = QLabel(self.translator.tr("recommended_counters"))
        rec_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        rec_layout.addWidget(rec_title)

        self.rec_list = QListWidget()
        self.rec_list.setMaximumHeight(200)
        rec_layout.addWidget(self.rec_list)

        right_layout.addWidget(rec_frame)

        # AI Анализ
        ai_frame = QFrame()
        ai_frame.setObjectName("panel")
        ai_layout = QVBoxLayout(ai_frame)
        ai_layout.setContentsMargins(16, 16, 16, 16)

        ai_title = QLabel(self.translator.tr("ai_analysis"))
        ai_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        ai_layout.addWidget(ai_title)

        self.ai_text = QTextEdit()
        self.ai_text.setReadOnly(True)
        self.ai_text.setPlaceholderText("AI аналіз з'явиться тут після аналізу...")
        ai_layout.addWidget(self.ai_text)

        right_layout.addWidget(ai_frame, 1)

        # Мета панель
        self.meta_panel = MetaPanel(self.translator)
        self.meta_panel.hero_clicked.connect(self._on_meta_hero_clicked)
        right_layout.addWidget(self.meta_panel)

        main_layout.addWidget(right_widget, 1)

    def _on_slot_clicked(self, slot_index, team):
        exclude = []
        for slot in self.radiant_slots + self.dire_slots:
            if slot.hero_name:
                exclude.append(slot.hero_name)

        dialog = HeroSelectorDialog(self.translator, self, exclude)
        dialog.hero_selected.connect(lambda name: self._set_hero(team, slot_index, name))
        dialog.exec()

    def _set_hero(self, team, slot_index, hero_name):
        hero = self.db.get_hero_by_name(hero_name)
        if hero:
            if team == "radiant":
                self.radiant_slots[slot_index].set_hero(hero)
            else:
                self.dire_slots[slot_index].set_hero(hero)

    def _on_hero_removed(self, slot_index, team):
        pass

    def _on_meta_hero_clicked(self, hero_name):
        for slot in self.radiant_slots:
            if not slot.hero_name:
                self._set_hero("radiant", slot.slot_index, hero_name)
                return
        for slot in self.dire_slots:
            if not slot.hero_name:
                self._set_hero("dire", slot.slot_index, hero_name)
                return

    def capture_screen(self):
        try:
            path = self.capture.capture_fullscreen()
            if self.recognizer.has_templates():
                heroes = self.recognizer.recognize_heroes(path)
                if heroes:
                    for i, name in enumerate(heroes[:5]):
                        if i < 5:
                            hero = self.db.get_hero_by_name(name)
                            if hero:
                                self.radiant_slots[i].set_hero(hero)
                    for i, name in enumerate(heroes[5:10]):
                        if i < 5:
                            hero = self.db.get_hero_by_name(name)
                            if hero:
                                self.dire_slots[i].set_hero(hero)

                    QMessageBox.information(self, self.translator.tr("success"), 
                        self.translator.tr("screenshot_recognized", len(heroes)))
                else:
                    QMessageBox.warning(self, self.translator.tr("warning"), 
                        "Не вдалося розпізнати героїв. Спробуйте додати шаблони портретів.")
            else:
                QMessageBox.information(self, self.translator.tr("info"), 
                    f"Скріншот збережено: {path}\nДодайте портрети героїв до assets/hero_portraits/ для автоматичного розпізнавання.")
        except Exception as e:
            QMessageBox.critical(self, self.translator.tr("error"), str(e))

    def run_analysis(self):
        radiant = [s.hero_name for s in self.radiant_slots if s.hero_name]
        dire = [s.hero_name for s in self.dire_slots if s.hero_name]

        if not radiant or not dire:
            QMessageBox.warning(self, self.translator.tr("warning"), self.translator.tr("no_heroes"))
            return

        self.btn_analyze.setEnabled(False)
        self.btn_analyze.setText("⏳ " + self.translator.tr("updating"))

        self.worker = AnalysisWorker(self.engine, radiant, dire, self.gemini, self.settings.get("language", "uk"))
        self.worker.finished.connect(self.on_analysis_done)
        self.worker.error.connect(self.on_analysis_error)
        self.worker.start()

    def on_analysis_done(self, result):
        self.current_result = result
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText("⚡ " + self.translator.tr("analyze"))
        self.btn_save.setEnabled(True)

        r = result['radiant_strength']
        d = result['dire_strength']

        self.radiant_strength.setText(f"{self.translator.tr('strength')}: {r:.1f}%")
        self.dire_strength.setText(f"{self.translator.tr('strength')}: {d:.1f}%")

        self.win_bar.setValueAnimated(int(r))
        self.win_bar.setFormat(f"Radiant {r:.1f}%")
        self.win_details.setText(f"Radiant {r:.1f}% | Dire {d:.1f}%")

        if r > d:
            self.win_bar.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; border-radius: 8px; }")
        else:
            self.win_bar.setStyleSheet("QProgressBar::chunk { background-color: #c0392b; border-radius: 8px; }")

        self.rec_list.clear()
        for rec in result['radiant_recommendations'][:5]:
            self.rec_list.addItem(f"{rec['name']} — {rec['score']:.1f}%")

        self.ai_text.setText(result.get('ai_analysis', 'Немає даних'))

        verdict = 'Radiant має перевагу' if r > d else 'Dire має перевагу'
        general = f"""<h3>{self.translator.tr('strong_sides')} Radiant</h3>
<ul><li>Командна сила: {r:.1f}%</li><li>Добре збалансований склад</li></ul>

<h3>{self.translator.tr('strong_sides')} Dire</h3>
<ul><li>Командна сила: {d:.1f}%</li><li>Потенціал для камбеку</li></ul>

<h3>{self.translator.tr('verdict')}</h3>
<p>{verdict}</p>

<h3>Рекомендовані контрпіки:</h3>
<ol>"""
        for rec in result['radiant_recommendations'][:5]:
            general += f"<li>{rec['name']} ({rec['score']:.1f}%)</li>"
        general += "</ol>"

        self.tab_general.setHtml(general)

        comparison = f"""<table style='width:100%; border-collapse: collapse;'>
<tr style='background-color: #c0392b; color: white;'>
<th style='padding: 10px;'>Параметр</th><th style='padding: 10px;'>Radiant</th><th style='padding: 10px;'>Dire</th></tr>
<tr><td style='padding: 8px; border-bottom: 1px solid #333;'>Сила команди</td>
<td style='padding: 8px; border-bottom: 1px solid #333; color: #27ae60;'>{r:.1f}%</td>
<td style='padding: 8px; border-bottom: 1px solid #333; color: #c0392b;'>{d:.1f}%</td></tr>
<tr><td style='padding: 8px; border-bottom: 1px solid #333;'>Кількість героїв</td>
<td style='padding: 8px; border-bottom: 1px solid #333;'>{len([s for s in self.radiant_slots if s.hero_name])}</td>
<td style='padding: 8px; border-bottom: 1px solid #333;'>{len([s for s in self.dire_slots if s.hero_name])}</td></tr>
</table>"""
        self.tab_comparison.setHtml(comparison)

        if self.settings.get("auto_save", True):
            self.save_analysis()

    def on_analysis_error(self, msg):
        self.btn_analyze.setEnabled(True)
        self.btn_analyze.setText("⚡ " + self.translator.tr("analyze"))
        QMessageBox.critical(self, self.translator.tr("error"), msg)

    def save_analysis(self):
        if not self.current_result:
            return
        radiant = [s.hero_name for s in self.radiant_slots if s.hero_name]
        dire = [s.hero_name for s in self.dire_slots if s.hero_name]
        self.db.save_analysis(
            radiant, dire,
            self.current_result['radiant_strength'],
            self.current_result['dire_strength'],
            self.current_result['radiant_recommendations'],
            self.current_result.get('ai_analysis', ''),
            "",
            "7.41d",
            "All Pick"
        )
        QMessageBox.information(self, self.translator.tr("success"), self.translator.tr("analysis_saved"))

    def clear_all(self):
        for slot in self.radiant_slots + self.dire_slots:
            slot.clear()
        self.current_result = None
        self.btn_save.setEnabled(False)
        self.radiant_strength.setText("Сила: --")
        self.dire_strength.setText("Сила: --")
        self.win_bar.setValue(50)
        self.win_details.setText("50.0% | 50.0%")
        self.rec_list.clear()
        self.ai_text.clear()
        self.tab_general.clear()
        self.tab_comparison.clear()

    def refresh_settings(self):
        self.settings = load_settings()
        self.gemini = GeminiAnalyzer(self.settings.get("gemini_model", "gemini-1.5-flash"))
        self.recognizer.set_threshold(self.settings.get("confidence_threshold", 0.65))
        self.translator = Translator(self.settings.get("language", "uk"))
        self.meta_panel.refresh()

# ═══════════════════════════════════════════════════════════
# Страница истории
# ═══════════════════════════════════════════════════════════
class HistoryPage(QWidget):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.db = DatabaseManager()
        self._setup_ui()
        self.load_history()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel(self.translator.tr("history"))
        title.setObjectName("title")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Дата", "Radiant", "Dire", "Сила", "Дії"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Оновити")
        self.refresh_btn.clicked.connect(self.load_history)
        self.clear_btn = QPushButton("🗑 Очистити історію")
        self.clear_btn.setObjectName("dangerButton")
        self.clear_btn.clicked.connect(self.clear_history)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.clear_btn)
        layout.addLayout(btn_layout)

    def load_history(self):
        self.table.setRowCount(0)
        history = self.db.get_history(50)

        for row_idx, row_data in enumerate(history):
            self.table.insertRow(row_idx)

            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_data.get('id', ''))))

            ts = row_data.get('timestamp', '')
            try:
                dt = datetime.fromisoformat(ts)
                ts = dt.strftime("%d.%m.%Y %H:%M")
            except:
                pass
            self.table.setItem(row_idx, 1, QTableWidgetItem(ts))

            radiant = json.loads(row_data.get('radiant_heroes', '[]'))
            dire = json.loads(row_data.get('dire_heroes', '[]'))

            self.table.setItem(row_idx, 2, QTableWidgetItem(", ".join(radiant)))
            self.table.setItem(row_idx, 3, QTableWidgetItem(", ".join(dire)))

            r_str = row_data.get('radiant_strength', 0)
            d_str = row_data.get('dire_strength', 0)
            self.table.setItem(row_idx, 4, QTableWidgetItem(f"R: {r_str:.1f}% | D: {d_str:.1f}%"))

            view_btn = QPushButton("👁 Переглянути")
            view_btn.clicked.connect(lambda checked, rid=row_data.get('id'): self.view_analysis(rid))
            self.table.setCellWidget(row_idx, 5, view_btn)

    def view_analysis(self, analysis_id):
        analysis = self.db.get_analysis_by_id(analysis_id)
        if analysis:
            msg = QMessageBox(self)
            msg.setWindowTitle(f"Аналіз #{analysis_id}")
            msg.setText(analysis.get('ai_analysis', 'Немає даних'))
            msg.setMinimumSize(600, 400)
            msg.exec()

    def clear_history(self):
        reply = QMessageBox.question(self, "Підтвердження", 
            "Ви впевнені, що хочете очистити всю історію?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for item in self.db.get_history(9999):
                self.db.delete_analysis(item['id'])
            self.load_history()

# ═══════════════════════════════════════════════════════════
# Страница базы героев
# ═══════════════════════════════════════════════════════════
class HeroDatabasePage(QWidget):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.db = DatabaseManager()
        self._setup_ui()
        self._load_heroes()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel(self.translator.tr("hero_database"))
        title.setObjectName("title")
        layout.addWidget(title)

        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(self.translator.tr("search_hero"))
        self.search_edit.textChanged.connect(self._filter_heroes)

        self.role_filter = QComboBox()
        self.role_filter.addItem(self.translator.tr("all_roles"), "")
        self.role_filter.addItem(self.translator.tr("carry"), "Carry")
        self.role_filter.addItem(self.translator.tr("mid"), "Nuker")
        self.role_filter.addItem(self.translator.tr("offlane"), "Initiator")
        self.role_filter.addItem(self.translator.tr("support"), "Support")
        self.role_filter.addItem(self.translator.tr("hard_support"), "Disabler")
        self.role_filter.currentIndexChanged.connect(self._filter_heroes)

        search_layout.addWidget(self.search_edit, 3)
        search_layout.addWidget(self.role_filter, 1)
        layout.addLayout(search_layout)

        self.hero_table = QTableWidget()
        self.hero_table.setColumnCount(6)
        self.hero_table.setHorizontalHeaderLabels([
            "Герой", "Роль", "Атрибут", "Тип атаки", "Вінрейт", "Пікрейт"
        ])
        self.hero_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.hero_table)

    def _load_heroes(self):
        self.all_heroes = self.db.get_cached_heroes()
        self._filter_heroes()

    def _filter_heroes(self):
        self.hero_table.setRowCount(0)
        search = self.search_edit.text().lower()
        role = self.role_filter.currentData()

        filtered = []
        for h in self.all_heroes:
            name = h.get('localized_name', '').lower()
            if search and search not in name:
                continue
            if role and role not in h.get('roles', []):
                continue
            filtered.append(h)

        for row_idx, hero in enumerate(filtered):
            self.hero_table.insertRow(row_idx)
            self.hero_table.setItem(row_idx, 0, QTableWidgetItem(hero.get('localized_name', '')))
            self.hero_table.setItem(row_idx, 1, QTableWidgetItem(", ".join(hero.get('roles', [])[:2])))
            self.hero_table.setItem(row_idx, 2, QTableWidgetItem(hero.get('primary_attr', '').upper()))
            self.hero_table.setItem(row_idx, 3, QTableWidgetItem(hero.get('attack_type', '')))

            winrate = hero.get('winrate', 50)
            win_item = QTableWidgetItem(f"{winrate:.1f}%")
            if winrate >= 53:
                win_item.setForeground(QColor("#27ae60"))
            elif winrate < 48:
                win_item.setForeground(QColor("#e74c3c"))
            self.hero_table.setItem(row_idx, 4, win_item)

            self.hero_table.setItem(row_idx, 5, QTableWidgetItem(f"{hero.get('pickrate', 0):.1f}%"))

# ═══════════════════════════════════════════════════════════
# Страница рекомендаций
# ═══════════════════════════════════════════════════════════
class RecommendationsPage(QWidget):
    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.db = DatabaseManager()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        title = QLabel(self.translator.tr("recommendations"))
        title.setObjectName("title")
        layout.addWidget(title)

        info = QLabel("Рекомендації формуються на основі аналізу драфту.\nПерейдіть до 'Аналіз матча' щоб отримати персоналізовані поради.")
        info.setStyleSheet("color: #888; padding: 20px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        layout.addStretch()

# ═══════════════════════════════════════════════════════════
# ГЛАВНОЕ ОКНО
# ═══════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.translator = Translator(self.settings.get("language", "uk"))
        self.setWindowTitle("Dota 2 Draft Assistant")
        self.setMinimumSize(1500, 950)
        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Сайдбар
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setSpacing(4)
        sb_layout.setContentsMargins(0, 16, 0, 16)

        # Логотип
        logo_frame = QFrame()
        logo_layout = QVBoxLayout(logo_frame)
        logo_layout.setContentsMargins(16, 8, 16, 16)

        logo_icon = QLabel("🎮")
        logo_icon.setStyleSheet("font-size: 32px;")
        logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_title = QLabel("DOTA 2")
        logo_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #c0392b;")
        logo_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_sub = QLabel("DRAFT ASSISTANT")
        logo_sub.setStyleSheet("font-size: 11px; color: #888; letter-spacing: 2px;")
        logo_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_layout.addWidget(logo_icon)
        logo_layout.addWidget(logo_title)
        logo_layout.addWidget(logo_sub)
        sb_layout.addWidget(logo_frame)

        # Разделитель
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2d2d2d;")
        sep.setFixedHeight(1)
        sb_layout.addWidget(sep)

        # Навигация
        self.stack = QStackedWidget()
        self.match_page = MatchAnalysisPage(self.translator)
        self.history_page = HistoryPage(self.translator)
        self.hero_db_page = HeroDatabasePage(self.translator)
        self.recommendations_page = RecommendationsPage(self.translator)
        self.settings_page = QWidget()

        self.stack.addWidget(self.match_page)
        self.stack.addWidget(self.history_page)
        self.stack.addWidget(self.hero_db_page)
        self.stack.addWidget(self.recommendations_page)
        self.stack.addWidget(self.settings_page)

        pages = [
            ("⚔ " + self.translator.tr("match_analysis"), 0),
            ("📜 " + self.translator.tr("history"), 1),
            ("👥 " + self.translator.tr("hero_database"), 2),
            ("💡 " + self.translator.tr("recommendations"), 3),
            ("⚙ " + self.translator.tr("settings"), 4),
        ]

        self.nav_buttons = []
        for text, idx in pages:
            btn = QPushButton(text)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setMinimumHeight(48)
            btn.clicked.connect(lambda checked, i=idx: self.switch_page(i))
            sb_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        sb_layout.addStretch()

        # Инфо внизу
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(16, 8, 16, 8)

        patch_label = QLabel("Patch 7.41d")
        patch_label.setStyleSheet("color: #666; font-size: 11px;")
        patch_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version_label = QLabel("v1.0.0")
        version_label.setStyleSheet("color: #444; font-size: 10px;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        info_layout.addWidget(patch_label)
        info_layout.addWidget(version_label)
        sb_layout.addWidget(info_frame)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack, 1)

        self.nav_buttons[0].setChecked(True)

    def switch_page(self, index):
        if index == 4:
            self._open_settings()
            return
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def _open_settings(self):
        dialog = SettingsDialog(self.translator, self)
        dialog.settings_applied.connect(self._on_settings_changed)
        dialog.exec()

    def _on_settings_changed(self, settings):
        self.settings = settings
        self.translator = Translator(settings.get("language", "uk"))
        self._apply_theme()
        self.match_page.refresh_settings()

    def _apply_theme(self):
        theme = self.settings.get("theme", "dark")
        if theme == "system":
            theme = "dark"

        stylesheet = get_theme(theme)
        QApplication.instance().setStyleSheet(stylesheet)

    def resizeEvent(self, event):
        super().resizeEvent(event)

# ═══════════════════════════════════════════════════════════
# ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    settings = load_settings()
    theme = settings.get("theme", "dark")
    if theme == "system":
        theme = "dark"
    app.setStyleSheet(get_theme(theme))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
