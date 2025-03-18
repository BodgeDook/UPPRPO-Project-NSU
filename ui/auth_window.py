import sys

import re
import requests  # Used to communicate with FastAPI backend

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread


# 📌 MODEL: Handles API communication
class AuthModel(QObject):
    def check_email(self, email):
        """Sends email to FastAPI backend and returns the response."""
        try:
            response = requests.get(f"http://127.0.0.1:8000/check_email/{email}")
            if response.status_code == 200:
                return response.json()["message"]  # Expected: "Email exists" or "Email does not exist"
            else:
                return "Server error"
        except requests.RequestException:
            return "Network error"

# ⚡ VIEWMODEL: Handles validation + calls the model
class AuthViewModel(QObject):
    result_signal = pyqtSignal(str)  # Signal to update the UI with the result

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.worker = None

    def validate_and_check_email(self, email):
        """Validates the email and calls the model."""
        if not self.is_valid_email(email):
            self.result_signal.emit("Invalid email format")
            return
        
        # Call API in a separate thread to prevent UI freezing
        self.worker = EmailCheckerWorker(self.model, email)
        self.worker.result_signal.connect(self.result_signal.emit)
        self.worker.start()

    def is_valid_email(self, email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None # regex validation

# 🏃‍♂️ Worker Thread for API Call (Prevents UI Freezing)
class EmailCheckerWorker(QThread):
    result_signal = pyqtSignal(str)

    def __init__(self, model, email):
        super().__init__()
        self.model = model
        self.email = email

    def run(self):
        result = self.model.check_email(self.email)
        self.result_signal.emit(result)
    

# VIEW: Handles UI interaction
class AuthWindow(QWidget):
    def __init__(self, view_model):
        super().__init__()

        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 400, 200)

        self.view_model = view_model  # Reference to ViewModel

        # UI Elements
        self.label = QLabel("Enter your email:", self)
        self.email_input = QLineEdit(self)
        self.check_button = QPushButton("Check", self)
        self.check_button.setDefault(True)      # Makes it the default button
        self.check_button.setAutoDefault(True)  # Allows Enter key activation
        # self.email_input.setFocus()            # Ensure it gets keyboard focus on launch

        self.result_label = QLabel("", self)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.check_button)
        layout.addWidget(self.result_label)

        self.setLayout(layout)  # Directly set the layout (no need for setCentralWidget)

        # 🎯 Connect UI to ViewModel
        self.check_button.clicked.connect(self.check_email)
        self.view_model.result_signal.connect(self.update_result)

    def check_email(self):
        email = self.email_input.text()
        self.view_model.validate_and_check_email(email)

    def update_result(self, result):
        self.result_label.setText(result)  # Update UI with backend response


if __name__ == "__main__":
    # QApplication.setAttribute(Qt.AA_MacUseFullKeyboardNavigation, True)
    app = QApplication(sys.argv)

    model = AuthModel()
    view_model = AuthViewModel(model)
    window = AuthWindow(view_model)

    window.show()
    sys.exit(app.exec_())