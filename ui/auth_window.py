import sys

import re
import requests  # Used to communicate with FastAPI backend

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, QVBoxLayout, QWidget, QStackedWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread


# 📌 MODEL: Handles API communication
class AuthModel(QObject):
    # def login(self, email, password)
    # def register(self, email, password)
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

# VIEWMODEL: Handles validation + calls the model
class AuthViewModel(QObject):
    result_signal = pyqtSignal(str)  # Signal to update the UI with the result
    state_changed = pyqtSignal()

    REGISTER = 0
    LOGIN = 1

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.current_state = self.REGISTER  # Default to register
        self.worker = None


    def switch_to_login(self):
        self.current_state = self.LOGIN
        self.state_changed.emit()

    def switch_to_register(self):
        self.current_state = self.REGISTER
        self.state_changed.emit()

    def validate_email(self, email):
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
class RegisterView(QWidget):
    def __init__(self, view_model, switch_callback):
        super().__init__()
        self.view_model = view_model  # Assign the view model
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Register Page"))

        # UI Elements
        self.label = QLabel("Enter your email:", self)
        self.email_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.repeat_password_input = QLineEdit(self)
        self.reg_button = QPushButton("Register", self)
        self.reg_button.setDefault(True)      # Makes it the default button
        self.reg_button.setAutoDefault(True)  # Allows Enter key activation
        # self.email_input.setFocus()            # Ensure it gets keyboard focus on launch
        self.result_label = QLabel("", self)

        self.switch_button = QPushButton("Already have an account?")
        self.switch_button.clicked.connect(switch_callback)

        # Layout
        layout.addWidget(self.label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.repeat_password_input)
        layout.addWidget(self.reg_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.switch_button)

        self.setLayout(layout)  # Directly set the layout
        layout.addWidget(self.switch_button)

        # 🎯 Connect UI to ViewModel
        self.reg_button.clicked.connect(self.check_email)
        self.view_model.result_signal.connect(self.update_result)

    def check_email(self):
        email = self.email_input.text()
        self.view_model.validate_email(email)

    def update_result(self, result):
        self.result_label.setText(result)  # Update UI with backend response


class LoginView(QWidget):
    def __init__(self, view_model, switch_callback):
        super().__init__()
        self.view_model = view_model  # Assign the view model
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Login Page"))


        # UI Elements
        self.label = QLabel("Enter your email:", self)
        self.email_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.check_button = QPushButton("Login", self)
        self.check_button.setDefault(True)      # Makes it the default button
        self.check_button.setAutoDefault(True)  # Allows Enter key activation
        # self.email_input.setFocus()            # Ensure it gets keyboard focus on launch

        self.result_label = QLabel("", self)

        self.switch_button = QPushButton("Don't have an account?")
        self.switch_button.clicked.connect(switch_callback)


        # Layout
        layout.addWidget(self.label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.check_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.switch_button)

        self.setLayout(layout)  # Directly set the layout

        # 🎯 Connect UI to ViewModel
        self.check_button.clicked.connect(self.check_email)
        self.view_model.result_signal.connect(self.update_result)

    def check_email(self):
        email = self.email_input.text()
        self.view_model.validate_email(email)

    def update_result(self, result):
        self.result_label.setText(result)  # Update UI with backend response


class AuthView(QWidget):
    def __init__(self, view_model):
        super().__init__()
        self.view_model = view_model # Reference to ViewModel
        self.layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()
        
        self.register_view = RegisterView(self.view_model, self.view_model.switch_to_login)
        self.login_view = LoginView(self.view_model, self.view_model.switch_to_register)
        
        self.stacked_widget.addWidget(self.register_view)
        self.stacked_widget.addWidget(self.login_view)

        self.layout.addWidget(self.stacked_widget)
        
        self.view_model.state_changed.connect(self.update_view)
        self.update_view()  # Set initial state

    def update_view(self):
        self.stacked_widget.setCurrentIndex(self.view_model.current_state)


if __name__ == "__main__":
    # QApplication.setAttribute(Qt.AA_MacUseFullKeyboardNavigation, True)
    app = QApplication(sys.argv)

    model = AuthModel()
    view_model = AuthViewModel(model)
    window = AuthView(view_model)

    window.show()
    sys.exit(app.exec_())