# desktop-app/controllers/auth.py

import os
import re
from enum import Enum

from PyQt5.QtCore import QObject, pyqtSignal, QThread


# Password Constant Levels:
# class PasswordLevel(Enum):
#     EASY = 1
#     MEDIUM = 2
#     HARD = 3


class AuthController(QObject):
    """
    Acts as the “controller” for authentication: validation, threading, and
    communicating with AuthModel. Emits signals to update the UI.
    """

    # Emitted whenever there's a message (e.g. “Invalid email format”, server errors, etc.)
    result_signal_to_ui = pyqtSignal(str)

    # Emitted when state switches (register <-> login), so the view can swap pages
    state_changed = pyqtSignal()

    # Emitted when login/register succeeds
    auth_successful = pyqtSignal()

    # Emitted True/False to tell the view to show/hide a “busy” spinner
    processing = pyqtSignal(bool)

    REGISTER = 0
    LOGIN = 1

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.current_state = self.REGISTER  # default to register
        self.worker = None

    def switch_to_login(self):
        self.current_state = self.LOGIN
        self.state_changed.emit()

    def switch_to_register(self):
        self.current_state = self.REGISTER
        self.state_changed.emit()

    def login_user(self, email, password):
        if not self.validate_email(email):
            self.result_signal_to_ui.emit("Invalid email format")
            return False

        self.processing.emit(True)
        self.worker = AuthWorker(self.model, email, password, "login")
        self.worker.result_signal.connect(self.process_response)
        self.worker.start()

    def register_user(self, email, password1, password2):
        if not self.validate_email(email):
            self.result_signal_to_ui.emit("Invalid email format")
            return False

        if not self.validate_passwords(password1, password2):
            return False

        self.processing.emit(True)
        self.worker = AuthWorker(self.model, email, password1, "register")
        self.worker.result_signal.connect(self.process_response)
        self.worker.start()

    def validate_email(self, email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    def validate_passwords(self, password1, password2):
        if password1 != password2:
            self.result_signal_to_ui.emit("Passwords do not match")
            return False

        if not self.is_valid_password(password1):
            self.result_signal_to_ui.emit("Not a strong password")
            return False

        return True

    def is_valid_password(self, password):
        """
        To check:

        Args:
            password (str): your_password

        Returns:
            bool: True, if valid else False
        """

        # Easy: >= 8 symbols
        if len(password) < 8:
            return False

        # Easy: if at least one letter is in lower case (a-z)
        if not re.search(r"[a-z]", password):
            return False

        # Easy: if at least one letter is in upper case (A-Z)
        if not re.search(r"[A-Z]", password):
            return False

        # Easy: if at least there's one letter (0-9)
        if not re.search(r"[0-9]", password):
            return False

        # Easy: if at least one special symbol (for instance, !@#$%^&*()_+-=[]{}|;:,.<>?)
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
            return False

        # Medium: no repeatable symbols
        # if level.value >= PasswordLevel.MEDIUM.value:
        # if two similar letters are next to each other:
        for i in range(len(password) - 1):
            if password[i] == password[i + 1]:
                return False

        # Hard: additional checks:
        # if level.value >= PasswordLevel.HARD.value:
        # Проверка на наличие "abc123"
        if "abc123" in password.lower():
            return False

        # check for the common phrases:
        common_phrases = [
            "password",
            "qwerty",
            "123456",
            "admin",
            "letmein",
            "welcome",
            "monkey",
            "dragon",
            "sunshine",
            "princess",
        ]

        password_lower = password.lower()
        for phrase in common_phrases:
            if phrase in password_lower:
                return False

        # If all the checks are okay:
        return True

    def process_response(self, status_code, response):
        self.processing.emit(False)

        if os.getenv("DEVELOP_MACHINE"):
            print(status_code, response)

        if status_code == 200:
            self.auth_successful.emit()
        elif status_code == 500:
            self.result_signal_to_ui.emit(str(response))
        else:
            self.result_signal_to_ui.emit(str(response))


class AuthWorker(QThread):
    """
    Worker Thread for API Calls (login/register) so the UI does not freeze.
    """
    result_signal = pyqtSignal(int, dict)

    def __init__(self, model, email, password, action):
        super().__init__()
        self.model = model
        self.email = email
        self.password = password
        self.action = action  # "register" or "login"

    def run(self):
        status_code, response = getattr(self.model, self.action)(self.email, self.password)
        self.result_signal.emit(status_code, response)
