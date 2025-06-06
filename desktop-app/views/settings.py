# from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

# class SettingsDialog(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Settings")
#         self.resize(400, 300)

#         layout = QVBoxLayout()
#         layout.addWidget(QLabel("Settings go here"))
#         close_button = QPushButton("Close")
#         close_button.clicked.connect(self.accept)  # or self.reject

#         layout.addWidget(close_button)
#         self.setLayout(layout)

# desktop-app/view/settings.py
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QLabel

class SettingsDialog(QDialog):
    settings_saved = pyqtSignal(dict)  # e.g. { "autosave_interval": 10, "theme": "dark", ... }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("uMovie Settings")
        self.resize(400, 300)

        layout = QVBoxLayout()
        form = QFormLayout()

        self.autosave_field = QLineEdit()
        self.theme_field = QLineEdit()
        # … add other settings fields as needed …

        form.addRow("Auto-save interval (sec):", self.autosave_field)
        form.addRow("Theme (light/dark):", self.theme_field)

        btn_save = QPushButton("Save")
        btn_cancel = QPushButton("Cancel")
        self.feedback = QLabel("")

        layout.addLayout(form)
        layout.addWidget(btn_save)
        layout.addWidget(btn_cancel)
        layout.addWidget(self.feedback)
        self.setLayout(layout)

        btn_save.clicked.connect(self._on_save)
        btn_cancel.clicked.connect(self.reject)

    def _on_save(self):
        try:
            interval = int(self.autosave_field.text())
        except ValueError:
            self.feedback.setText("Auto-save must be an integer.")
            return

        new_settings = {
            "autosave_interval": interval,
            "theme": self.theme_field.text()
        }
        self.settings_saved.emit(new_settings)
        self.accept()
