import os
import re

from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer

class AuthController(QObject):
    result_signal_to_ui = pyqtSignal(str)
    state_changed = pyqtSignal()
    forgot_password_state_changed = pyqtSignal()
    auth_successful = pyqtSignal()
    processing = pyqtSignal(bool)

    REGISTER = 0
    LOGIN = 1
    VERIFY = 2
    FORGOT_PASSWORD = 3
    FORGOT_PASSWORD_EMAIL = 0
    VERIFY_NEW_PASSWORD = 1

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.current_state = self.REGISTER
        self.forgot_password_state = self.FORGOT_PASSWORD_EMAIL
        self.worker = None
        self.current_email = None
    # covered
    def switch_to_login(self):
        self.current_state = self.LOGIN
        self.state_changed.emit()
    # covered
    def switch_to_register(self):
        self.current_state = self.REGISTER
        self.state_changed.emit()
    # covered
    def switch_to_forgot_password(self):
        self.current_state = self.FORGOT_PASSWORD
        self.forgot_password_state = self.FORGOT_PASSWORD_EMAIL
        self.state_changed.emit()
        self.forgot_password_state_changed.emit()

    # covered
    def login_user(self, email, password):
        if not self.validate_email(email):
            self.result_signal_to_ui.emit("Invalid email format")
            return False

        self.processing.emit(True)
        self.worker = AuthWorker(self.model, email, password, "login")
        self.worker.result_signal.connect(self.process_response)
        self.worker.start()
    # covered
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

    # covered
    def verify_code(self, email, code):
        if not code.strip():
            self.result_signal_to_ui.emit("Please enter the verification code")
            return False

        self.processing.emit(True)
        self.worker = AuthWorker(self.model, email, code, "verify_code")
        self.worker.result_signal.connect(self.process_response)
        self.worker.start()

    # covered
    def send_verification_code_for_reset(self, email):
        if not self.validate_email(email):
            self.result_signal_to_ui.emit("Invalid email format")
            return False

        self.current_email = email
        self.processing.emit(True)
        self.worker = AuthWorker(self.model, email, None, "send_code")
        self.worker.result_signal.connect(self.process_forgot_password_response)
        self.worker.start()

    def verify_and_update_password(self, email, code, new_password, repeat_password):
        if not code.strip():
            self.result_signal_to_ui.emit("Please enter the verification code")
            return False

        if not self.validate_passwords(new_password, repeat_password):
            return False

        self.processing.emit(True)
        self.worker = AuthWorker(self.model, email, code, "verify_code")
        self.worker.result_signal.connect(lambda action, status, response: self.process_verify_and_update_password(email, new_password))
        self.worker.start()

    # covered
    def resend_code(self, email):
        self.processing.emit(True)
        self.worker = AuthWorker(self.model, email, None, "send_code")
        self.worker.result_signal.connect(self.process_response)
        self.worker.start()

    def validate_email(self, email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None
    # covered
    def validate_passwords(self, password1, password2):
        if password1 != password2:
            self.result_signal_to_ui.emit("Passwords do not match")
            return False

        if not self.is_valid_password(password1):
            self.result_signal_to_ui.emit("Not a strong password")
            return False

        return True
    # covered
    def is_valid_password(self, password):
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
    # covered partly
    def process_response(self, action, status_code, response):
        self.processing.emit(False)

        if os.getenv("DEVELOP_MACHINE"):
            print(action, status_code, response)

        if action in ("register", "login"):
            if status_code in (200, 201):
                self.current_email = self.worker.email
                self.current_state = self.VERIFY
                self.state_changed.emit()
                self.worker = AuthWorker(self.model, self.current_email, None, "send_code")
                self.worker.result_signal.connect(self.process_response)
                self.worker.start()
            else:
                self.result_signal_to_ui.emit(str(response.get('message', response)))
        elif action == "send_code":
            if status_code in (200, 201):
                self.result_signal_to_ui.emit("Verification code sent successfully")
            else:
                self.result_signal_to_ui.emit(f"Failed to send verification code: {response.get('message', response)}")
        elif action == "verify_code":
            if status_code == 200:
                self.result_signal_to_ui.emit("Verification successful!")
                QTimer.singleShot(2000, lambda: self.auth_successful.emit())
            else:
                self.result_signal_to_ui.emit(f"Verification failed: {response.get('message', response)}")

    def process_forgot_password_response(self, action, status_code, response):
        self.processing.emit(False)

        if os.getenv("DEVELOP_MACHINE"):
            print(action, status_code, response)

        if action == "send_code":
            if status_code in (200, 201):
                self.result_signal_to_ui.emit("Verification code sent successfully")
                self.forgot_password_state = self.VERIFY_NEW_PASSWORD
                self.forgot_password_state_changed.emit()
            else:
                self.result_signal_to_ui.emit(f"Failed to send verification code: {response.get('message', response)}")

    def process_verify_and_update_password(self, email, new_password):
        self.processing.emit(False)

        if self.worker.status_code == 200:
            self.result_signal_to_ui.emit("Verification successful, updating password...")
            self.worker = AuthWorker(self.model, email, new_password, "change_password")
            self.worker.result_signal.connect(self.process_password_update_response)
            self.worker.start()
        else:
            self.result_signal_to_ui.emit(f"Verification failed: {self.worker.response.get('message', self.worker.response)}")

    def process_password_update_response(self, action, status_code, response):
        self.processing.emit(False)

        if status_code in (200, 201):
            self.result_signal_to_ui.emit("Password updated successfully!")
            QTimer.singleShot(2000, lambda: self.switch_to_login())
        else:
            self.result_signal_to_ui.emit(f"Failed to update password: {response.get('message', response)}")


class AuthWorker(QThread):
    result_signal = pyqtSignal(str, int, object)

    def __init__(self, model, email, data=None, action=""):
        super().__init__()
        self.model = model
        self.email = email
        self.data = data
        self.action = action
        self.status_code = None
        self.response = None

    def run(self):
        if self.action == "send_code":
            self.status_code, self.response = self.model.send_code(self.email)
        elif self.action == "verify_code":
            self.status_code, self.response = self.model.verify_code(self.email, self.data)
        elif self.action == "change_password":
            self.status_code, self.response = self.model.change_password(self.email, self.data)
        else:
            self.status_code, self.response = getattr(self.model, self.action)(self.email, self.data)
        self.result_signal.emit(self.action, self.status_code, self.response)