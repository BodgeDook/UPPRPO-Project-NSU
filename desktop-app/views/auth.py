# desktop-app/view/auth.py

import os

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QStackedWidget,
)
from PyQt5.QtCore import Qt, QTimer

from controllers.auth import AuthController  # noqa: E402


class RegisterView(QWidget):
    """
    “Register” page: collects email + two passwords, calls controller.register_user().
    """

    def __init__(self, controller: AuthController, switch_callback):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Register Page"))

        # UI Elements
        self.label = QLabel("Enter your email:", self)
        self.email_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.repeat_password_input = QLineEdit(self)
        self.reg_button = QPushButton("Register", self)
        self.reg_button.setDefault(True)
        self.reg_button.setAutoDefault(True)
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

        # 🎯 Connect UI to Controller
        self.reg_button.clicked.connect(self.register_helper)
        self.controller.result_signal_to_ui.connect(self.update_result)

    def register_helper(self):
        email = self.email_input.text()
        password1 = self.password_input.text()
        password2 = self.repeat_password_input.text()
        self.controller.register_user(email, password1, password2)

    def update_result(self, result):
        self.result_label.setText(result)  # Update UI with backend response


class LoginView(QWidget):
    """
    “Login” page: collects email + password, calls controller.login_user().
    """

    def __init__(self, controller: AuthController, switch_callback):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Login Page"))

        # UI Elements
        self.label = QLabel("Enter your email:", self)
        self.email_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.login_button = QPushButton("Login", self)
        self.login_button.setDefault(True)
        self.login_button.setAutoDefault(True)
        self.result_label = QLabel("", self)

        self.switch_button = QPushButton("Don't have an account?")
        self.switch_button.clicked.connect(switch_callback)

        # Layout
        layout.addWidget(self.label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.switch_button)

        self.setLayout(layout)

        # 🎯 Connect UI to Controller
        self.login_button.clicked.connect(self.login_helper)
        self.controller.result_signal_to_ui.connect(self.update_result)

    def login_helper(self):
        email = self.email_input.text()
        password = self.password_input.text()
        self.controller.login_user(email, password)

    def update_result(self, result):
        self.result_label.setText(result)  # Update UI with backend response


class AuthView(QWidget):
    """
    Container for both RegisterView and LoginView. Uses QStackedWidget to swap between them.
    Listens for controller.state_changed and controller.auth_successful.
    """

    def __init__(self, controller: AuthController):
        super().__init__()
        self.controller = controller
        self.layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()

        # Instantiate the two pages, passing the same controller
        self.register_view = RegisterView(self.controller, self.controller.switch_to_login)
        self.login_view = LoginView(self.controller, self.controller.switch_to_register)

        self.stacked_widget.addWidget(self.register_view)
        self.stacked_widget.addWidget(self.login_view)

        self.layout.addWidget(self.stacked_widget)

        # Connect controller signals to update this view
        self.controller.state_changed.connect(self.update_view)
        self.controller.auth_successful.connect(self.handle_success)
        self.controller.processing.connect(self.set_processing_state)

        # Spinner/Loading indicator (could be replaced with a QMovie)
        self.spinner_label = QLabel("Loading...", self)
        self.spinner_label.hide()
        self.layout.addWidget(self.spinner_label)

        self.is_processing = False

        # Initialize to the correct page
        self.update_view()

    def update_view(self):
        # Clear any previous message
        self.controller.result_signal_to_ui.emit("")
        # Swap pages based on controller.current_state
        self.stacked_widget.setCurrentIndex(self.controller.current_state)

    def handle_success(self):
        if os.getenv("DEVELOP_MACHINE"):
            print("Successfully logged/registered!")
        self.controller.result_signal_to_ui.emit("Success!")
        # Close this window after a short delay
        QTimer.singleShot(2000, self.close)

    def set_processing_state(self, state: bool):
        self.is_processing = state
        if state:
            self.spinner_label.show()
        else:
            self.spinner_label.hide()

    def closeEvent(self, event):
        # Prevent closing if a request is still in flight
        if self.is_processing:
            event.ignore()
        else:
            event.accept()
