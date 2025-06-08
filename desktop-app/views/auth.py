# Final
import os

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
    QStackedWidget,
    QDialog,
)
from PyQt5.QtCore import Qt, QTimer

from controllers.auth import AuthController


class RegisterView(QWidget):
    def __init__(self, controller: AuthController, switch_callback):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Register Page"))

        self.label = QLabel("Enter your email:", self)
        self.email_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.repeat_password_input = QLineEdit(self)
        self.repeat_password_input.setEchoMode(QLineEdit.Password)
        self.reg_button = QPushButton("Register", self)
        self.reg_button.setDefault(True)
        self.reg_button.setAutoDefault(True)
        self.result_label = QLabel("", self)

        self.switch_button = QPushButton("Already have an account?")
        self.switch_button.clicked.connect(switch_callback)

        layout.addWidget(self.label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.repeat_password_input)
        layout.addWidget(self.reg_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.switch_button)

        self.reg_button.clicked.connect(self.register_helper)
        self.controller.result_signal_to_ui.connect(self.update_result)

    def register_helper(self):
        email = self.email_input.text()
        password1 = self.password_input.text()
        password2 = self.repeat_password_input.text()
        self.controller.register_user(email, password1, password2)

    def update_result(self, result):
        self.result_label.setText(result)


class LoginView(QWidget):
    def __init__(self, controller: AuthController, switch_callback):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Login Page"))

        self.label = QLabel("Enter your email:", self)
        self.email_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Login", self)
        self.login_button.setDefault(True)
        self.login_button.setAutoDefault(True)
        self.result_label = QLabel("", self)

        self.switch_button = QPushButton("Don't have an account?")
        self.switch_button.clicked.connect(switch_callback)

        layout.addWidget(self.label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.switch_button)

        self.setLayout(layout)

        self.login_button.clicked.connect(self.login_helper)
        self.controller.result_signal_to_ui.connect(self.update_result)

    def login_helper(self):
        email = self.email_input.text()
        password = self.password_input.text()
        self.controller.login_user(email, password)

    def update_result(self, result):
        self.result_label.setText(result)


class VerificationView(QWidget):
    def __init__(self, controller: AuthController):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Enter verification code:"))

        self.code_input = QLineEdit(self)
        self.verify_button = QPushButton("Verify", self)
        self.verify_button.setDefault(True)
        self.verify_button.setAutoDefault(True)
        self.resend_button = QPushButton("Resend Code", self)
        self.result_label = QLabel("", self)

        layout.addWidget(self.code_input)
        layout.addWidget(self.verify_button)
        layout.addWidget(self.resend_button)
        layout.addWidget(self.result_label)

        self.verify_button.clicked.connect(self.verify_helper)
        self.resend_button.clicked.connect(self.resend_helper)
        self.controller.result_signal_to_ui.connect(self.update_result)

    def verify_helper(self):
        code = self.code_input.text()
        email = self.controller.current_email
        self.controller.verify_code(email, code)

    def resend_helper(self):
        email = self.controller.current_email
        self.controller.resend_code(email)

    def update_result(self, result):
        self.result_label.setText(result)


class AuthView(QWidget):
    def __init__(self, controller: AuthController):
        super().__init__()
        self.controller = controller
        self.layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()

        self.register_view = RegisterView(self.controller, self.controller.switch_to_login)
        self.login_view = LoginView(self.controller, self.controller.switch_to_register)
        self.verification_view = VerificationView(self.controller)

        self.stacked_widget.addWidget(self.register_view)
        self.stacked_widget.addWidget(self.login_view)
        self.stacked_widget.addWidget(self.verification_view)

        self.layout.addWidget(self.stacked_widget)

        self.controller.state_changed.connect(self.update_view)
        self.controller.auth_successful.connect(self.handle_success)
        self.controller.processing.connect(self.set_processing_state)

        self.spinner_label = QLabel("Loading...", self)
        self.spinner_label.hide()
        self.layout.addWidget(self.spinner_label)

        self.is_processing = False

        self.update_view()

    def update_view(self):
        self.controller.result_signal_to_ui.emit("")
        if self.controller.current_state == self.controller.REGISTER:
            self.stacked_widget.setCurrentIndex(0)
        elif self.controller.current_state == self.controller.LOGIN:
            self.stacked_widget.setCurrentIndex(1)
        elif self.controller.current_state == self.controller.VERIFY:
            self.stacked_widget.setCurrentIndex(2)

    def handle_success(self):
        if os.getenv("DEVELOP_MACHINE"):
            print("Successfully authenticated!")
        self.controller.result_signal_to_ui.emit("Success!")
        # Close the dialog
        if self.parent() and isinstance(self.parent(), QDialog):
            QTimer.singleShot(2000, self.parent().accept)

    def set_processing_state(self, state: bool):
        self.is_processing = state
        self.register_view.reg_button.setEnabled(not state)
        self.login_view.login_button.setEnabled(not state)
        self.verification_view.verify_button.setEnabled(not state)
        self.verification_view.resend_button.setEnabled(not state)
        if state:
            self.spinner_label.show()
        else:
            self.spinner_label.hide()

    def closeEvent(self, event):
        if self.is_processing:
            event.ignore()
        else:
            event.accept()