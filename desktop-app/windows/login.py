from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.resize(300, 200)

        layout = QVBoxLayout()
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self._login)

        layout.addWidget(QLabel("Please login"))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(login_button)
        self.setLayout(layout)

    def _login(self):
        # Replace with actual logic
        print(f"Logging in: {self.username.text()}")
        self.accept()
