DARK_THEME = """
QMainWindow, QWidget { 
    background-color: #1a1a1a; 
    color: #e0e0e0; 
    font-family: 'Segoe UI', sans-serif; 
    font-size: 13px; 
}
QPushButton { 
    background-color: #2d2d2d; 
    border: 1px solid #3a3a3a; 
    border-radius: 6px; 
    padding: 8px 16px; 
    color: #ffffff; 
}
QPushButton:hover { 
    background-color: #3a3a3a; 
    border-color: #555555; 
}
QPushButton:pressed { 
    background-color: #555555; 
}
QPushButton#primaryButton { 
    background-color: #c0392b; 
    border: none; 
    font-weight: bold;
}
QPushButton#primaryButton:hover { 
    background-color: #e74c3c; 
}
QPushButton#primaryButton:pressed { 
    background-color: #a93226; 
}
QPushButton#secondaryButton {
    background-color: #27ae60;
    border: none;
    font-weight: bold;
}
QPushButton#secondaryButton:hover {
    background-color: #2ecc71;
}
QPushButton#dangerButton {
    background-color: #e74c3c;
    border: none;
}
QPushButton#dangerButton:hover {
    background-color: #c0392b;
}
QPushButton#navButton {
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 14px 16px;
    color: #aaaaaa;
    font-size: 14px;
    border-radius: 0px;
}
QPushButton#navButton:hover {
    color: #ffffff;
    background-color: #252525;
}
QPushButton#navButton:checked {
    background-color: #c0392b;
    color: #ffffff;
    border-left: 4px solid #e74c3c;
}
QLineEdit, QComboBox, QTextEdit { 
    background-color: #252525; 
    border: 1px solid #3a3a3a; 
    border-radius: 6px; 
    padding: 8px; 
    color: #ffffff; 
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border-color: #c0392b;
}
QListWidget, QTableWidget { 
    background-color: #1e1e1e; 
    border: 1px solid #2d2d2d; 
    outline: none; 
    border-radius: 6px;
}
QListWidget::item, QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #2d2d2d;
}
QListWidget::item:selected, QTableWidget::item:selected { 
    background-color: #c0392b; 
    color: white;
}
QListWidget::item:hover {
    background-color: #2d2d2d;
}
QTabWidget::pane { 
    border: 1px solid #2d2d2d; 
    background-color: #1a1a1a; 
    border-radius: 6px;
}
QTabBar::tab { 
    background-color: #252525; 
    padding: 10px 20px; 
    margin-right: 2px; 
    border-top-left-radius: 6px; 
    border-top-right-radius: 6px; 
    color: #aaaaaa;
}
QTabBar::tab:hover {
    color: #ffffff;
    background-color: #2d2d2d;
}
QTabBar::tab:selected { 
    background-color: #c0392b; 
    color: #ffffff;
}
QLabel#title { 
    font-size: 20px; 
    font-weight: bold; 
    color: #ffffff; 
}
QLabel#subtitle {
    font-size: 14px;
    color: #888888;
}
QLabel#heroName { 
    font-size: 11px; 
    color: #cccccc; 
    font-weight: 500;
}
QLabel#heroRole {
    font-size: 9px;
    color: #888888;
}
QProgressBar { 
    border: 1px solid #3a3a3a; 
    border-radius: 8px; 
    text-align: center; 
    color: white; 
    background-color: #252525;
    height: 24px;
}
QProgressBar::chunk { 
    background-color: #27ae60; 
    border-radius: 8px; 
}
QProgressBar#direBar::chunk { 
    background-color: #c0392b; 
}
QProgressBar#neutralBar::chunk {
    background-color: #f39c12;
}
QFrame#heroCard { 
    background-color: #252525; 
    border: 1px solid #3a3a3a; 
    border-radius: 8px; 
}
QFrame#heroCard:hover { 
    border-color: #c0392b; 
    background-color: #2d2d2d;
}
QFrame#heroCardEmpty {
    background-color: #1e1e1e;
    border: 2px dashed #3a3a3a;
    border-radius: 8px;
}
QFrame#heroCardEmpty:hover {
    border-color: #c0392b;
    background-color: #252525;
}
QFrame#panel {
    background-color: #1e1e1e;
    border: 1px solid #2d2d2d;
    border-radius: 10px;
}
QFrame#sidebar {
    background-color: #111111;
    border-right: 1px solid #2d2d2d;
}
QScrollBar:vertical { 
    background-color: #1a1a1a; 
    width: 10px; 
    border-radius: 5px;
}
QScrollBar::handle:vertical { 
    background-color: #3a3a3a; 
    border-radius: 5px; 
}
QScrollBar::handle:vertical:hover {
    background-color: #555555;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #252525;
    color: #ffffff;
    border: 1px solid #3a3a3a;
    selection-background-color: #c0392b;
}
QSlider::groove:horizontal {
    background-color: #3a3a3a;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background-color: #c0392b;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -5px 0;
}
QSlider::sub-page:horizontal {
    background-color: #c0392b;
    border-radius: 3px;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #3a3a3a;
    background-color: #252525;
}
QCheckBox::indicator:checked {
    background-color: #27ae60;
    border-color: #27ae60;
}
QSpinBox, QDoubleSpinBox {
    background-color: #252525;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 6px;
    color: #ffffff;
}
"""

LIGHT_THEME = """
QMainWindow, QWidget { 
    background-color: #f5f5f5; 
    color: #333333; 
    font-family: 'Segoe UI', sans-serif; 
    font-size: 13px; 
}
QPushButton { 
    background-color: #ffffff; 
    border: 1px solid #cccccc; 
    border-radius: 6px; 
    padding: 8px 16px; 
    color: #333333; 
}
QPushButton:hover { 
    background-color: #f0f0f0; 
    border-color: #999999; 
}
QPushButton:pressed { 
    background-color: #e0e0e0; 
}
QPushButton#primaryButton { 
    background-color: #c0392b; 
    border: none; 
    color: #ffffff;
    font-weight: bold;
}
QPushButton#primaryButton:hover { 
    background-color: #e74c3c; 
}
QPushButton#secondaryButton {
    background-color: #27ae60;
    border: none;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#secondaryButton:hover {
    background-color: #2ecc71;
}
QPushButton#navButton {
    background-color: transparent;
    border: none;
    text-align: left;
    padding: 14px 16px;
    color: #666666;
    font-size: 14px;
    border-radius: 0px;
}
QPushButton#navButton:hover {
    color: #333333;
    background-color: #e8e8e8;
}
QPushButton#navButton:checked {
    background-color: #c0392b;
    color: #ffffff;
    border-left: 4px solid #e74c3c;
}
QLineEdit, QComboBox, QTextEdit { 
    background-color: #ffffff; 
    border: 1px solid #cccccc; 
    border-radius: 6px; 
    padding: 8px; 
    color: #333333; 
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
    border-color: #c0392b;
}
QListWidget, QTableWidget { 
    background-color: #ffffff; 
    border: 1px solid #cccccc; 
    outline: none; 
    border-radius: 6px;
}
QListWidget::item, QTableWidget::item {
    padding: 8px;
    border-bottom: 1px solid #eeeeee;
}
QListWidget::item:selected, QTableWidget::item:selected { 
    background-color: #c0392b; 
    color: white;
}
QListWidget::item:hover {
    background-color: #f0f0f0;
}
QTabWidget::pane { 
    border: 1px solid #cccccc; 
    background-color: #f5f5f5; 
    border-radius: 6px;
}
QTabBar::tab { 
    background-color: #e0e0e0; 
    padding: 10px 20px; 
    margin-right: 2px; 
    border-top-left-radius: 6px; 
    border-top-right-radius: 6px; 
    color: #666666;
}
QTabBar::tab:hover {
    color: #333333;
    background-color: #d0d0d0;
}
QTabBar::tab:selected { 
    background-color: #c0392b; 
    color: #ffffff;
}
QLabel#title { 
    font-size: 20px; 
    font-weight: bold; 
    color: #333333; 
}
QLabel#subtitle {
    font-size: 14px;
    color: #666666;
}
QLabel#heroName { 
    font-size: 11px; 
    color: #333333; 
    font-weight: 500;
}
QLabel#heroRole {
    font-size: 9px;
    color: #888888;
}
QProgressBar { 
    border: 1px solid #cccccc; 
    border-radius: 8px; 
    text-align: center; 
    color: #333333; 
    background-color: #ffffff;
    height: 24px;
}
QProgressBar::chunk { 
    background-color: #27ae60; 
    border-radius: 8px; 
}
QProgressBar#direBar::chunk { 
    background-color: #c0392b; 
}
QFrame#heroCard { 
    background-color: #ffffff; 
    border: 1px solid #cccccc; 
    border-radius: 8px; 
}
QFrame#heroCard:hover { 
    border-color: #c0392b; 
    background-color: #f8f8f8;
}
QFrame#heroCardEmpty {
    background-color: #f0f0f0;
    border: 2px dashed #cccccc;
    border-radius: 8px;
}
QFrame#heroCardEmpty:hover {
    border-color: #c0392b;
    background-color: #f8f8f8;
}
QFrame#panel {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 10px;
}
QFrame#sidebar {
    background-color: #e8e8e8;
    border-right: 1px solid #cccccc;
}
QScrollBar:vertical { 
    background-color: #f5f5f5; 
    width: 10px; 
    border-radius: 5px;
}
QScrollBar::handle:vertical { 
    background-color: #cccccc; 
    border-radius: 5px; 
}
QScrollBar::handle:vertical:hover {
    background-color: #999999;
}
QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #cccccc;
    selection-background-color: #c0392b;
}
QSlider::groove:horizontal {
    background-color: #cccccc;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background-color: #c0392b;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -5px 0;
}
QSlider::sub-page:horizontal {
    background-color: #c0392b;
    border-radius: 3px;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #cccccc;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #27ae60;
    border-color: #27ae60;
}
QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 6px;
    padding: 6px;
    color: #333333;
}
"""

def get_theme(theme_name):
    if theme_name == "light":
        return LIGHT_THEME
    return DARK_THEME
