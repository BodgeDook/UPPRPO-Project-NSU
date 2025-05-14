from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QDialog
)
from PyQt5.QtCore import pyqtSignal

class RegisterView(QWidget):
    # user clicked “Register” with these fields
    register_requested = pyqtSignal(str, str, str)
    switch_to_login    = pyqtSignal()

    def __init__(self):
        super().__init__()
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
        self.reg_button.clicked.connect(self._on_register)
        # self.email_input.setFocus()            # Ensure it gets keyboard focus on launch
        self.result_label = QLabel("", self)

        self.switch_button = QPushButton("Already have an account?")
        self.switch_button.clicked.connect(self.switch_to_login.emit)
        self.switch_button.clicked.connect(self.switch_to_login.emit)

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


    # def register_helper(self):
    #     email = self.email_input.text()
    #     password1 = self.password_input.text()
    #     password2 = self.repeat_password_input.text()
    #     self.view_model.register_user(email, password1, password2)

    def _on_register(self):
        self.register_requested.emit(
            self.email_input.text(),
            self.password_input.text(),
            self.repeat_password_input.text()
        )

    def show_message(self, text: str):
        self.result_label.setText(text) # Update UI with backend response


class LoginView(QWidget):
    login_requested = pyqtSignal(str, str)
    switch_to_register = pyqtSignal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Login Page"))


        # UI Elements
        self.label = QLabel("Enter your email:", self)
        self.email_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.login_button = QPushButton("Login", self)
        self.login_button.setDefault(True)      # Makes it the default button
        self.login_button.setAutoDefault(True)  # Allows Enter key activation
        self.login_button.clicked.connect(self._on_login)
        # self.email_input.setFocus()            # Ensure it gets keyboard focus on launch

        self.result_label = QLabel("", self)
        self.switch_button = QPushButton("Don't have an account?")
        self.switch_button.clicked.connect(self.switch_to_register.emit)

        # Layout
        layout.addWidget(self.label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.switch_button)

        self.setLayout(layout)  # Directly set the layout


    def _on_login(self):
        self.login_requested.emit(
            self.email_input.text(),
            self.password_input.text()
        )

    # def login_helper(self):
    #     email = self.email_input.text()
    #     password = self.password_input.text()
    #     self.view_model.login_user(email, password)


    def show_message(self, text: str):
        self.result_label.setText(text)  # Update UI with backend response


# class AuthDialog(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Login")
#         self.resize(300, 200)

#         layout = QVBoxLayout()
#         self.username = QLineEdit()
#         self.username.setPlaceholderText("Username")
#         self.password = QLineEdit()
#         self.password.setPlaceholderText("Password")
#         self.password.setEchoMode(QLineEdit.Password)

#         login_button = QPushButton("Login")
#         login_button.clicked.connect(self._login)

#         layout.addWidget(QLabel("Please login"))
#         layout.addWidget(self.username)
#         layout.addWidget(self.password)
#         layout.addWidget(login_button)
#         self.setLayout(layout)

#     def _login(self):
#         # Replace with actual logic
#         print(f"Logging in: {self.username.text()}")
#         self.accept()

class AuthDialog(QDialog):
    """
    Container that swaps between RegisterView and LoginView.
    Emits accepted() when auth succeeds.
    """
    def __init__(self):
        super().__init__()
        self.stack = QStackedWidget(self)
        self.register_view = RegisterView()
        self.login_view    = LoginView()
        self.stack.addWidget(self.register_view)
        self.stack.addWidget(self.login_view)

        layout = QVBoxLayout(self)
        layout.addWidget(self.stack)

        # Switching pages:
        self.register_view.switch_to_login.connect(
            lambda: self.stack.setCurrentWidget(self.login_view))
        self.login_view.switch_to_register.connect(
            lambda: self.stack.setCurrentWidget(self.register_view))

