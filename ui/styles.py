from PyQt5.QtCore import QObject, pyqtSignal
from .settings_manager import settings_manager

class ThemeManager(QObject):
    theme_changed = pyqtSignal(str)
    _current_theme = settings_manager.get_setting("theme", "light")  # download the theme from the json file

    def set_theme(self, theme):
        if theme != self._current_theme:
            self._current_theme = theme
            settings_manager.set_setting("theme", theme)  # Saving the the theme into a json file
            self.theme_changed.emit(theme)

    def get_theme(self):
        return self._current_theme

theme_manager = ThemeManager()

def apply_welcome_window_style(widget):
    theme = theme_manager.get_theme()
    if theme == "light":
        widget.setStyleSheet("""
            QWidget, QWidget * {
                background-color: #e6f3fa !important;
                color: #000000;
            }
        """)
    elif theme == "dark":
        widget.setStyleSheet("""
            QWidget, QWidget * {
                background-color: #4682b4 !important;
                color: #ffffff;
            }
        """)
    widget.update()  # Force update to ensure style applies

def apply_window_style(widget):
    theme = theme_manager.get_theme()
    if theme == "light":
        widget.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                color: #000000;
            }
        """)
    elif theme == "dark":
        widget.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: #ffffff;
            }
        """)

def apply_button_style(widget):
    theme = theme_manager.get_theme()
    if theme == "light":
        widget.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
    elif theme == "dark":
        widget.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                border: 1px solid #555555;
                padding: 5px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)

def apply_disabled_button_style(widget):
    theme = theme_manager.get_theme()
    if theme == "light":
        widget.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #dddddd;
                padding: 5px;
                color: #888888;
            }
        """)
    elif theme == "dark":
        widget.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                border: 1px solid #444444;
                padding: 5px;
                color: #aaaaaa;
            }
        """)

def apply_label_style(widget):
    theme = theme_manager.get_theme()
    if theme == "light":
        widget.setStyleSheet("""
            QLabel {
                color: #000000;
            }
        """)
    elif theme == "dark":
        widget.setStyleSheet("""
            QLabel {
                color: #ffffff;
            }
        """)

def apply_title_style(widget):
    theme = theme_manager.get_theme()
    if theme == "light":
        widget.setStyleSheet("""
            QLabel {
                color: #000000;
                font-size: 24px;
                font-weight: bold;
            }
        """)
    elif theme == "dark":
        widget.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }
        """)

def apply_link_style(widget):
    theme = theme_manager.get_theme()
    if theme == "light":
        widget.setStyleSheet("""
            QPushButton {
                color: #0066cc;
                background: none;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #003399;
            }
        """)
    elif theme == "dark":
        widget.setStyleSheet("""
            QPushButton {
                color: #66b3ff;
                background: none;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #99ccff;
            }
        """)