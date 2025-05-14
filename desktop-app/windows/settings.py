from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(400, 300)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Settings go here"))
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)  # or self.reject

        layout.addWidget(close_button)
        self.setLayout(layout)
