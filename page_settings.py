from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QLineEdit, QComboBox, QFileDialog, QMessageBox, QScrollArea,
                              QCheckBox, QGridLayout, QKeySequenceEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence

from ui.widgets import make_card, card_title, small_label, ToggleRow, AnimatedButton, page_title
from ui import theme
import database as db
from services import stratz_service, gemini_service, hotkey_service


class SettingsPage(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.settings = db.get_all_settings()
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(18)

        outer.addWidget(page_title("Налаштування", "setting_icon.jpg", "⚙"))
        outer.addWidget(small_label("Налаштуйте програму під себе"))

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        content = QWidget()
        outer_c = QVBoxLayout(content)
        outer_c.setSpacing(16)

        top_row = QHBoxLayout(); top_row.setSpacing(16)
        top_row.addWidget(self._general_card(), 1)
        top_row.addWidget(self._screenshot_card(), 1)
        outer_c.addLayout(top_row)

        mid_row = QHBoxLayout(); mid_row.setSpacing(16)
        mid_row.addWidget(self._gemini_card(), 1)
        mid_row.addWidget(self._stratz_card(), 1)
        outer_c.addLayout(mid_row)

        outer_c.addWidget(self._data_card())

        save_row = QHBoxLayout()
        save_row.addStretch()
        save_btn = AnimatedButton("✓  Зберегти налаштування", radius=8)
        save_btn.setFixedHeight(44)
        save_row.addWidget(save_btn)
        save_btn.clicked.connect(self.on_save)
        outer_c.addLayout(save_row)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

    def _general_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)
        lay.addWidget(card_title("Загальні", "⇄"))

        lang_row = self._combo_row("Мова інтерфейсу", "Оберіть мову програми", ["Українська", "English"], self.settings.get("ui_language", "Українська"))
        self.lang_combo = lang_row[1]
        lay.addLayout(lang_row[0])

        current_theme_label = "Світла" if self.settings.get("theme") == "light" else "Темна"
        theme_row = self._combo_row("Тема оформлення", "Оберіть тему інтерфейсу", ["Темна", "Світла"], current_theme_label)
        self.theme_combo = theme_row[1]
        lay.addLayout(theme_row[0])

        self.auto_update_toggle = ToggleRow("Автоматичне оновлення статистики",
                                             "Регулярно оновлювати дані з STRATZ API",
                                             checked=self.settings.get("auto_update_stats") == "1")
        lay.addWidget(self.auto_update_toggle)

        self.autostart_toggle = ToggleRow("Запускати програму разом із Windows",
                                           "Автоматичний запуск при увімкненні ПК",
                                           checked=self.settings.get("start_with_windows") == "1")
        lay.addWidget(self.autostart_toggle)
        lay.addStretch()
        return card

    def _screenshot_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)
        lay.addWidget(card_title("Робота зі скриншотами", "create_screen.png"))

        hk_row = QHBoxLayout()
        hk_box = QVBoxLayout(); hk_box.setSpacing(2)
        hk_box.addWidget(self._field_label("Гаряча клавіша для скриншота"))
        hint = "Клацніть у поле та натисніть комбінацію клавіш"
        if not hotkey_service.available():
            hint += "  ⚠ працює лише поки вікно програми активне"
        else:
            hint += ("  •  Якщо Dota 2 запущена з правами адміністратора, "
                     "запустіть і цю програму від імені адміністратора — "
                     "інакше Windows не дозволить гарячій клавіші спрацювати поверх гри.")
        hk_box.addWidget(small_label(hint))
        hk_row.addLayout(hk_box)
        hk_row.addStretch()
        self.hotkey_edit = QKeySequenceEdit(QKeySequence(self.settings.get("screenshot_hotkey", "Print Screen")))
        self.hotkey_edit.setFixedWidth(150)
        self.hotkey_edit.setMaximumSequenceLength(1)
        hk_row.addWidget(self.hotkey_edit)
        clear_btn = QPushButton("✕")
        clear_btn.setFixedWidth(32)
        clear_btn.setStyleSheet(self._secondary_btn_style())
        clear_btn.clicked.connect(self.hotkey_edit.clear)
        hk_row.addWidget(clear_btn)
        lay.addLayout(hk_row)

        self.auto_open_toggle = ToggleRow("Автоматично відкривати скриншот",
                                           "Відкривати після створення скриншота",
                                           checked=self.settings.get("auto_open_screenshot") == "1")
        lay.addWidget(self.auto_open_toggle)

        folder_row = QHBoxLayout()
        folder_box = QVBoxLayout(); folder_box.setSpacing(2)
        folder_box.addWidget(self._field_label("Папка збереження скриншотів"))
        folder_box.addWidget(small_label("Виберіть папку для збереження зображень"))
        lay.addLayout(folder_box)
        folder_row2 = QHBoxLayout()
        from services.screenshot_service import _default_folder
        default_folder = self.settings.get("screenshot_folder") or _default_folder()
        self.folder_edit = QLineEdit(default_folder)
        folder_row2.addWidget(self.folder_edit, 1)
        browse_btn = QPushButton("📁  Змінити")
        browse_btn.setStyleSheet(self._secondary_btn_style())
        browse_btn.clicked.connect(self._browse_folder)
        folder_row2.addWidget(browse_btn)
        lay.addLayout(folder_row2)
        lay.addStretch()
        return card

    def _gemini_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)
        lay.addWidget(card_title("Gemini (Штучний інтелект)", "gemini_logo.webp"))

        lay.addWidget(self._field_label("API Key Gemini"))
        lay.addWidget(small_label("Введіть ваш API ключ для Gemini 3 Pro"))
        key_row = QHBoxLayout()
        self.gemini_key_edit = QLineEdit(self.settings.get("gemini_api_key", ""))
        self.gemini_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        key_row.addWidget(self.gemini_key_edit, 1)
        eye_btn = QPushButton("👁")
        eye_btn.setFixedWidth(36)
        eye_btn.setStyleSheet(self._secondary_btn_style())
        eye_btn.clicked.connect(lambda: self._toggle_echo(self.gemini_key_edit))
        key_row.addWidget(eye_btn)
        check_btn = QPushButton("Перевірити")
        check_btn.setStyleSheet(self._secondary_btn_style())
        check_btn.clicked.connect(self._check_gemini)
        key_row.addWidget(check_btn)
        lay.addLayout(key_row)

        lang_row = self._combo_row("Мова відповідей ШІ", "Оберіть мову для пояснень від ШІ", ["Українська", "English"], self.settings.get("ai_response_language", "Українська"))
        self.ai_lang_combo = lang_row[1]
        lay.addLayout(lang_row[0])

        status_row = QHBoxLayout()
        status_row.addWidget(small_label("Статус підключення"))
        status_row.addStretch()
        self.gemini_status = self._status_dot(bool(self.settings.get("gemini_api_key")))
        status_row.addWidget(self.gemini_status)
        lay.addLayout(status_row)
        lay.addStretch()
        return card

    def _stratz_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)
        lay.addWidget(card_title("STRATZ API", "stratz_logo.png"))

        lay.addWidget(self._field_label("API Key STRATZ"))
        key_row = QHBoxLayout()
        self.stratz_key_edit = QLineEdit(self.settings.get("stratz_api_key", ""))
        self.stratz_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        key_row.addWidget(self.stratz_key_edit, 1)
        eye_btn = QPushButton("👁")
        eye_btn.setFixedWidth(36)
        eye_btn.setStyleSheet(self._secondary_btn_style())
        eye_btn.clicked.connect(lambda: self._toggle_echo(self.stratz_key_edit))
        key_row.addWidget(eye_btn)
        check_btn = QPushButton("Перевірити")
        check_btn.setStyleSheet(self._secondary_btn_style())
        check_btn.clicked.connect(self._check_stratz)
        key_row.addWidget(check_btn)
        lay.addLayout(key_row)

        status_row = QHBoxLayout()
        status_row.addWidget(small_label("Статус підключення"))
        status_row.addStretch()
        self.stratz_status = self._status_dot(bool(self.settings.get("stratz_api_key")))
        status_row.addWidget(self.stratz_status)
        lay.addLayout(status_row)

        upd_row = QHBoxLayout()
        upd_row.addWidget(small_label("Останнє оновлення даних"))
        upd_row.addStretch()
        self.last_sync_lbl = QLabel(self.settings.get("last_stratz_sync") or "—")
        self.last_sync_lbl.setStyleSheet("color:#9d90f5; font-size:11px; font-weight:600; border:none; background:transparent;")
        upd_row.addWidget(self.last_sync_lbl)
        lay.addLayout(upd_row)
        lay.addStretch()
        return card

    def _data_card(self):
        card = make_card()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)
        lay.addWidget(card_title("Дані та історія", "🗄"))
        row = QHBoxLayout(); row.setSpacing(14)

        row.addLayout(self._data_action("🕘", "Очистити історію аналізів", "Видалити всі збережені аналізи з історії", "Очистити", self._clear_history, danger=True))
        row.addLayout(self._data_action("🧹", "Очистити кеш", "Видалить тимчасові файли та кеш даних", "Очистити", self._clear_cache, danger=True))
        row.addLayout(self._data_action("⬇", "Експортувати історію", "Зберегти історію аналізів у файл", "Експортувати", self._export_history, danger=False))
        lay.addLayout(row)
        return card

    def _data_action(self, icon, title, subtitle, btn_text, handler, danger):
        box = QVBoxLayout(); box.setSpacing(6)
        t = QLabel(f"{icon}  {title}")
        t.setStyleSheet("color:#e7e9f3; font-weight:700; font-size:12px; border:none; background:transparent;")
        box.addWidget(t)
        s = small_label(subtitle)
        s.setWordWrap(True)
        box.addWidget(s)
        btn = QPushButton(btn_text)
        if danger:
            btn.setStyleSheet("""
                QPushButton { background-color: #2a1620; color: #f0728a; border: 1px solid #4a2233;
                    border-radius: 8px; padding: 8px 14px; font-weight: 600; }
                QPushButton:hover { background-color: #3a1c29; }
            """)
        else:
            btn.setStyleSheet(self._secondary_btn_style())
        btn.clicked.connect(handler)
        box.addWidget(btn)
        return box

    # ---------------------------------------------------------------- helpers
    def _field_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#e7e9f3; font-size:13px; font-weight:600; border:none; background:transparent;")
        return lbl

    def _secondary_btn_style(self):
        return """
            QPushButton { background-color: #181c2c; color: #e7e9f3; border-radius: 8px;
                padding: 8px 14px; border: 1px solid #2a2f45; font-weight: 600; }
            QPushButton:hover { background-color: #20253a; border-color: #393f5c; }
        """

    def _combo_row(self, title, subtitle, options, current):
        row = QHBoxLayout()
        box = QVBoxLayout(); box.setSpacing(2)
        box.addWidget(self._field_label(title))
        box.addWidget(small_label(subtitle))
        row.addLayout(box)
        row.addStretch()
        combo = QComboBox()
        combo.addItems(options)
        if current in options:
            combo.setCurrentText(current)
        combo.setFixedWidth(160)
        row.addWidget(combo)
        return row, combo

    def _status_dot(self, connected):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        dot = QLabel(); dot.setFixedSize(8, 8)
        text = QLabel()
        lay.addWidget(dot)
        lay.addWidget(text)
        w._dot = dot
        w._text = text
        self._set_status_widget(w, connected)
        return w

    def _set_status_widget(self, w, connected):
        color = "#5ee08a" if connected else "#ef6f7a"
        w._dot.setStyleSheet(f"background-color:{color}; border-radius:4px;")
        w._text.setText("Підключено" if connected else "Не підключено")
        w._text.setStyleSheet(f"color:{color}; font-size:12px; font-weight:700; border:none; background:transparent;")

    def _toggle_echo(self, edit):
        edit.setEchoMode(QLineEdit.EchoMode.Normal if edit.echoMode() == QLineEdit.EchoMode.Password else QLineEdit.EchoMode.Password)

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Оберіть папку для скриншотів", self.folder_edit.text())
        if folder:
            self.folder_edit.setText(folder)

    def _check_gemini(self):
        key = self.gemini_key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "Gemini API", "Введіть API ключ перед перевіркою.")
            return

        ok, msg = gemini_service.test_connection(key)
        if ok:
            db.set_setting("gemini_api_key", key)
            self.settings = db.get_all_settings()
        self._set_status_widget(self.gemini_status, ok)
        QMessageBox.information(self, "Gemini API", msg)

    def _check_stratz(self):
        key = self.stratz_key_edit.text().strip()
        ok, msg = stratz_service.test_connection(key)
        if ok:
            # Persist immediately -- previously the key was only written to
            # the database when the "Зберегти налаштування" button at the
            # bottom of the page was pressed, so a successful test here
            # still left every other screen (e.g. Статистика героїв) using
            # cached/offline data until the user separately hit Save.
            ts = stratz_service.now_str()
            db.set_settings({"stratz_api_key": key, "last_stratz_sync": ts})
            self.settings = db.get_all_settings()
            self.last_sync_lbl.setText(ts)
        self._set_status_widget(self.stratz_status, ok)
        QMessageBox.information(self, "STRATZ API", msg)

    def _clear_history(self):
        confirm = QMessageBox.question(self, "Очистити історію", "Видалити всю історію аналізів?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            db.clear_history()
            QMessageBox.information(self, "Готово", "Історію аналізів очищено.")

    def _clear_cache(self):
        QMessageBox.information(self, "Готово", "Тимчасові файли та кеш очищено.")

    def _export_history(self):
        path, _ = QFileDialog.getSaveFileName(self, "Експортувати історію", "history_export.json", "JSON (*.json)")
        if path:
            count = db.export_history(path)
            QMessageBox.information(self, "Експорт завершено", f"Експортовано {count} записів у {path}")

    def on_save(self):
        hotkey_text = self.hotkey_edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText) or "F8"
        new_settings = {
            "ui_language": self.lang_combo.currentText(),
            "theme": "dark" if self.theme_combo.currentText() == "Темна" else "light",
            "auto_update_stats": "1" if self.auto_update_toggle.checkbox.isChecked() else "0",
            "start_with_windows": "1" if self.autostart_toggle.checkbox.isChecked() else "0",
            "screenshot_hotkey": hotkey_text,
            "auto_open_screenshot": "1" if self.auto_open_toggle.checkbox.isChecked() else "0",
            "screenshot_folder": self.folder_edit.text(),
            "gemini_api_key": self.gemini_key_edit.text(),
            "ai_response_language": self.ai_lang_combo.currentText(),
            "stratz_api_key": self.stratz_key_edit.text(),
        }
        db.set_settings(new_settings)
        self.settings = db.get_all_settings()
        QMessageBox.information(self, "Налаштування", "Налаштування успішно збережено та застосовано.")
        # Apply the hotkey / theme / language changes live, without needing
        # a restart. This rebuilds the whole page tree (including this very
        # widget), so it must run *after* we're done using `self`.
        if getattr(self.app_state, "on_settings_changed", None):
            self.app_state.on_settings_changed()
