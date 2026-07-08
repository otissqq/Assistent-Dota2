"""
Builds the application-wide QSS from the active theme's colour tokens
(ui/theme.py). Uses string.Template ($token) instead of str.format() so the
literal { } braces used everywhere in QSS rule blocks don't need escaping.
"""
from string import Template

_TEMPLATE = Template("""
* {
    font-family: "Segoe UI", "Inter", sans-serif;
    color: $text;
}

QMainWindow, QWidget#root, QWidget#authScreen {
    background-color: $bg;
}

/* Generic container widgets must stay transparent, otherwise Qt paints
   every un-styled QWidget with the platform style's default (grey) panel
   background as soon as an application-wide stylesheet is active. */
QWidget {
    background-color: transparent;
}

/* ---------- Sidebar ---------- */
QWidget#sidebar {
    background-color: $sidebar;
    border-right: 1px solid $border;
}
QWidget#titlebar {
    background-color: $titlebar;
    border-bottom: 1px solid $border;
}

QPushButton#navBtn {
    text-align: left;
    padding: 10px 14px;
    border-radius: 8px;
    background: transparent;
    border: none;
    font-size: 14px;
    color: $text_muted;
}
QPushButton#navBtn:hover {
    background-color: $surface_soft;
    color: $text_bright;
}
QPushButton#navBtn[active="true"] {
    background-color: $accent;
    color: #ffffff;
    font-weight: 600;
}

QWidget#sidebarStatus {
    background-color: $surface_soft;
    border: 1px solid $border_soft;
    border-radius: 10px;
}

QLabel#appTitle { font-size: 16px; font-weight: 700; color: $text_bright; }
QLabel#appSubtitle { font-size: 11px; color: $text_faint; }

/* ---------- Cards ---------- */
QFrame.card {
    background-color: $surface;
    border: 1px solid $border_soft;
    border-radius: 16px;
}
QLabel.cardTitle { font-size: 15px; font-weight: 700; color: $text_bright; }
QLabel.cardSubtitle { font-size: 11px; color: $text_faint; }

/* ---------- Buttons ---------- */
QPushButton.primary {
    background-color: $accent;
    color: white;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 600;
    border: none;
}
QPushButton.primary:hover { background-color: $accent_hover; }
QPushButton.primary:pressed { background-color: $accent_press; }
QPushButton.primary:disabled { background-color: $border_input; color: $text_ghost; }

QPushButton.secondary {
    background-color: $surface_alt;
    color: $text;
    border-radius: 8px;
    padding: 10px 16px;
    border: 1px solid $border_input;
    font-weight: 500;
}
QPushButton.secondary:hover { background-color: $surface_soft; border-color: $accent; }

QPushButton.danger {
    background-color: #2a1620;
    color: #f0728a;
    border: 1px solid #4a2233;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton.danger:hover { background-color: #3a1c29; }

QPushButton.flat {
    background: transparent;
    border: none;
    color: $text_muted;
}
QPushButton.flat:hover { color: $text_bright; }

/* ---------- Inputs ---------- */
QLineEdit, QComboBox, QKeySequenceEdit {
    background-color: $input_bg;
    border: 1px solid $border_input;
    border-radius: 8px;
    padding: 10px 14px;
    color: $text;
    font-size: 13px;
}
QLineEdit:focus, QComboBox:focus, QKeySequenceEdit:focus { border: 1px solid $accent; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: $surface_soft;
    border: 1px solid $border_input;
    selection-background-color: $accent;
    color: $text;
    outline: none;
}

/* ---------- Misc ---------- */
QLabel.statGreen { color: $green; font-weight: 700; font-size: 18px; }
QLabel.statWhite { color: $text_bright; font-weight: 700; font-size: 18px; }
QLabel.statRed { color: $red; font-weight: 700; font-size: 18px; }
QLabel.small { color: $text_faint; font-size: 11px; }
QLabel.h1 { color: $text_bright; font-size: 22px; font-weight: 700; }
QLabel.bodyText { color: $text_dim; font-size: 13px; }
QLabel.linkPurple { color: $accent_soft; font-size: 12px; font-weight: 600; }

QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 0; }
QScrollBar::handle:vertical { background: $scrollbar; border-radius: 4px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: $scrollbar_h; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal { background: transparent; height: 8px; margin: 0; }
QScrollBar::handle:horizontal { background: $scrollbar; border-radius: 4px; min-width: 24px; }
QScrollBar::handle:horizontal:hover { background: $scrollbar_h; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }

QListWidget { background-color: transparent; border: none; outline: none; }
QListWidget::item {
    background-color: $surface;
    border: 1px solid $border_soft;
    border-radius: 12px;
    margin-bottom: 12px;
    padding: 4px;
}
QListWidget::item:selected {
    background-color: $surface_soft;
    border: 1px solid $accent;
}

QTabBar::tab {
    background: transparent;
    color: $text_faint;
    padding: 8px 4px;
    margin-right: 22px;
    border-bottom: 2px solid transparent;
    font-weight: 600;
    font-size: 13px;
}
QTabBar::tab:selected { color: $text_bright; border-bottom: 2px solid $accent; }
QTabWidget::pane { border: none; border-top: 1px solid $border_soft; top: -1px; }

QProgressBar { background-color: $surface_soft; border: none; border-radius: 4px; height: 8px; }
QProgressBar::chunk { background-color: $accent; border-radius: 4px; }

QMessageBox { background-color: $surface; }
QToolTip {
    background-color: $surface_soft;
    color: $text;
    border: 1px solid $border_input;
    padding: 4px 8px;
    border-radius: 6px;
}
""")


def generate_qss(theme_tokens: dict) -> str:
    return _TEMPLATE.safe_substitute(**theme_tokens)
