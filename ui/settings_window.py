import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, 
                             QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QStackedWidget)
from PyQt5.QtCore import Qt

from .styles import apply_welcome_window_style, apply_button_style, apply_label_style, apply_title_style, apply_disabled_button_style, theme_manager
from .settings_manager import settings_manager

from .auth_window import PasswordLevel
import re

class SettingsWindow(QWidget):
    def __init__(self, initial_section="appearance"):
        super().__init__()
        self.initUI(initial_section)
        theme_manager.theme_changed.connect(self.update_theme)

    def initUI(self, initial_section):
        self.setWindowTitle('uMovie - Settings')
        self.setGeometry(300, 300, 800, 600)
        apply_welcome_window_style(self)

        main_layout = QHBoxLayout()

        sidebar = QWidget()
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setAlignment(Qt.AlignTop)

        title_label = QLabel("Settings")
        apply_title_style(title_label)
        sidebar_layout.addWidget(title_label)

        self.sections = {
            "appearance": {"button": QPushButton("Appearance"), "index": 0},
            "account": {"button": QPushButton("Account"), "index": 1},
            "features": {"button": QPushButton("Purchased Features"), "index": 2}
        }

        for section, info in self.sections.items():
            apply_button_style(info["button"])
            info["button"].clicked.connect(lambda checked, s=section: self.switch_section(s))
            sidebar_layout.addWidget(info["button"])

        sidebar.setLayout(sidebar_layout)
        sidebar.setFixedWidth(200)
        main_layout.addWidget(sidebar)

        self.stacked_widget = QStackedWidget()

        self.appearance_view = AppearanceView()
        self.account_view = AccountView()
        self.features_view = FeaturesView()

        self.stacked_widget.addWidget(self.appearance_view)
        self.stacked_widget.addWidget(self.account_view)
        self.stacked_widget.addWidget(self.features_view)

        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        self.switch_section(initial_section)

    def switch_section(self, section):
        if section in self.sections:
            self.stacked_widget.setCurrentIndex(self.sections[section]["index"])
            for s, info in self.sections.items():
                if s == section:
                    apply_button_style(info["button"])
                else:
                    apply_disabled_button_style(info["button"])

    def update_theme(self, theme):
        apply_welcome_window_style(self)
        
        current_index = self.stacked_widget.currentIndex()
        for section, info in self.sections.items():
            if info["index"] == current_index:
                apply_button_style(info["button"])  # Active button
            else:
                apply_disabled_button_style(info["button"])  # Inactive button
        
        for widget in self.findChildren(QPushButton):
            if widget not in [info["button"] for info in self.sections.values()]:
                apply_button_style(widget)
        for widget in self.findChildren(QLabel):
            if widget.text() == "Settings":
                apply_title_style(widget)
            else:
                apply_label_style(widget)
        
        self.update()

class AppearanceView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("Theme Settings")
        apply_label_style(label)
        layout.addWidget(label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Light", "Dark"])
        current_theme = theme_manager.get_theme()
        self.theme_combo.setCurrentText(current_theme.capitalize())  # Current theme installing
        layout.addWidget(self.theme_combo)

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_theme)
        apply_button_style(apply_btn)
        layout.addWidget(apply_btn)

        self.setLayout(layout)

    def apply_theme(self):
        theme = self.theme_combo.currentText().lower()
        theme_manager.set_theme(theme)
        print(f"Applying {theme} theme...")

class AccountView(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("Change Password")
        apply_label_style(label)
        layout.addWidget(label)

        self.old_password = QLineEdit()
        self.old_password.setPlaceholderText("Old Password")
        self.old_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.old_password)

        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("New Password")
        self.new_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.new_password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Confirm New Password")
        self.confirm_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.confirm_password)

        self.result_label = QLabel("")
        apply_label_style(self.result_label)
        layout.addWidget(self.result_label)

        change_btn = QPushButton("Change Password")
        change_btn.clicked.connect(self.change_password)
        apply_button_style(change_btn)
        layout.addWidget(change_btn)

        self.setLayout(layout)

    def change_password(self):
        old_password = self.old_password.text()
        new_password = self.new_password.text()
        confirm_password = self.confirm_password.text()

        if not self.validate_passwords(new_password, confirm_password):
            return

        self.result_label.setText("Password change requested (not implemented yet).")
        print(f"Changing password from {old_password} to {new_password}")

    def validate_passwords(self, password1, password2):
        if password1 != password2:
            self.result_label.setText("Passwords do not match")
            return False

        if not self.is_valid_password(password1):
            self.result_label.setText("Not a strong password")
            return False
        
        return True

    def is_valid_password(self, password, level=PasswordLevel.EASY):
        if len(password) < 8:
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[0-9]", password):
            return False
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
            return False
        if level.value >= PasswordLevel.MEDIUM.value:
            for i in range(len(password) - 1):
                if password[i] == password[i + 1]:
                    return False
        if level.value >= PasswordLevel.HARD.value:
            if "abc123" in password.lower():
                return False
            common_phrases = [
                "password", "qwerty", "123456", "admin", "letmein",
                "welcome", "monkey", "dragon", "sunshine", "princess"
            ]
            password_lower = password.lower()
            for phrase in common_phrases:
                if phrase in password_lower:
                    return False
        return True

class FeaturesView(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        label = QLabel("Purchased Features")
        apply_label_style(label)
        layout.addWidget(label)

        features_table = QTableWidget(3, 2)
        features_table.setHorizontalHeaderLabels(["Feature", "Status"])
        features_table.setFixedSize(400, 150)
        features_table.setEditTriggers(QTableWidget.NoEditTriggers)

        features_data = [
            ("Background Removal", "Active"),
            ("Advanced Filters", "Inactive"),
            ("4K Export", "Inactive")
        ]

        for row, (feature, status) in enumerate(features_data):
            features_table.setItem(row, 0, QTableWidgetItem(feature))
            features_table.setItem(row, 1, QTableWidgetItem(status))

        features_table.resizeColumnsToContents()
        layout.addWidget(features_table)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SettingsWindow("account")
    window.show()
    sys.exit(app.exec_())