import sys
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QCheckBox, QSlider, QSpinBox, QDoubleSpinBox, QFrame, QGridLayout,
    QDialogButtonBox, QWidget, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtSignal

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
from config.settings import load_settings, save_settings, DEFAULT_SETTINGS

class SettingsDialog(QDialog):
    settings_applied = pyqtSignal(dict)

    def __init__(self, translator, parent=None):
        super().__init__(parent)
        self.translator = translator
        self.settings = load_settings()
        self.setWindowTitle(translator.tr("settings_title"))
        self.setMinimumSize(500, 600)
        self._setup_ui()
        self._load_values()
        self._animate_open()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Заголовок
        title = QLabel(self.translator.tr("settings_title"))
        title.setObjectName("title")
        layout.addWidget(title)

        # Язык
        lang_frame = self._create_setting_frame(
            self.translator.tr("language"),
            QComboBox()
        )
        self.lang_combo = lang_frame[1]
        self.lang_combo.addItem("Українська", "uk")
        self.lang_combo.addItem("Русский", "ru")
        self.lang_combo.addItem("English", "en")
        layout.addWidget(lang_frame[0])

        # Тема
        theme_frame = self._create_setting_frame(
            self.translator.tr("theme"),
            QComboBox()
        )
        self.theme_combo = theme_frame[1]
        self.theme_combo.addItem(self.translator.tr("theme_dark"), "dark")
        self.theme_combo.addItem(self.translator.tr("theme_light"), "light")
        self.theme_combo.addItem(self.translator.tr("theme_system"), "system")
        layout.addWidget(theme_frame[0])

        # Режим драфта
        draft_frame = self._create_setting_frame(
            self.translator.tr("draft_mode"),
            QComboBox()
        )
        self.draft_combo = draft_frame[1]
        self.draft_combo.addItem(self.translator.tr("draft_both"), "both")
        self.draft_combo.addItem(self.translator.tr("draft_radiant"), "radiant_only")
        self.draft_combo.addItem(self.translator.tr("draft_dire"), "dire_only")
        layout.addWidget(draft_frame[0])

        # Порог CV
        cv_frame = self._create_setting_frame(
            self.translator.tr("confidence_threshold"),
            QDoubleSpinBox()
        )
        self.cv_spin = cv_frame[1]
        self.cv_spin.setRange(0.3, 0.95)
        self.cv_spin.setSingleStep(0.05)
        self.cv_spin.setDecimals(2)
        layout.addWidget(cv_frame[0])

        # Топ героев
        top_frame = self._create_setting_frame(
            self.translator.tr("top_heroes_count"),
            QSpinBox()
        )
        self.top_spin = top_frame[1]
        self.top_spin.setRange(5, 20)
        layout.addWidget(top_frame[0])

        # Чекбоксы
        self.anim_check = QCheckBox(self.translator.tr("show_animations"))
        layout.addWidget(self.anim_check)

        self.sound_check = QCheckBox(self.translator.tr("sound_effects"))
        layout.addWidget(self.sound_check)

        self.autosave_check = QCheckBox(self.translator.tr("auto_save"))
        layout.addWidget(self.autosave_check)

        self.autocap_check = QCheckBox(self.translator.tr("auto_capture_mode"))
        layout.addWidget(self.autocap_check)

        layout.addStretch()

        # Кнопки
        btn_layout = QHBoxLayout()

        self.reset_btn = QPushButton(self.translator.tr("reset_defaults"))
        self.reset_btn.clicked.connect(self._reset_defaults)

        self.apply_btn = QPushButton(self.translator.tr("apply"))
        self.apply_btn.setObjectName("primaryButton")
        self.apply_btn.clicked.connect(self._apply_settings)

        self.cancel_btn = QPushButton(self.translator.tr("cancel"))
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.apply_btn)
        layout.addLayout(btn_layout)

    def _create_setting_frame(self, label_text, widget):
        frame = QFrame()
        frame.setObjectName("panel")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)

        label = QLabel(label_text)
        label.setStyleSheet("font-weight: 500;")
        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(widget)

        return frame, widget

    def _load_values(self):
        self.lang_combo.setCurrentIndex(
            self.lang_combo.findData(self.settings.get("language", "uk"))
        )
        self.theme_combo.setCurrentIndex(
            self.theme_combo.findData(self.settings.get("theme", "dark"))
        )
        self.draft_combo.setCurrentIndex(
            self.draft_combo.findData(self.settings.get("draft_mode", "both"))
        )
        self.cv_spin.setValue(self.settings.get("confidence_threshold", 0.65))
        self.top_spin.setValue(self.settings.get("top_heroes_count", 10))
        self.anim_check.setChecked(self.settings.get("show_animations", True))
        self.sound_check.setChecked(self.settings.get("sound_effects", True))
        self.autosave_check.setChecked(self.settings.get("auto_save", True))
        self.autocap_check.setChecked(self.settings.get("auto_capture", False))

    def _apply_settings(self):
        self.settings = {
            "language": self.lang_combo.currentData(),
            "theme": self.theme_combo.currentData(),
            "draft_mode": self.draft_combo.currentData(),
            "confidence_threshold": self.cv_spin.value(),
            "top_heroes_count": self.top_spin.value(),
            "show_animations": self.anim_check.isChecked(),
            "sound_effects": self.sound_check.isChecked(),
            "auto_save": self.autosave_check.isChecked(),
            "auto_capture": self.autocap_check.isChecked(),
        }
        save_settings(self.settings)
        self.settings_applied.emit(self.settings)
        self.accept()

    def _reset_defaults(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self._load_values()

    def _animate_open(self):
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim.start()
