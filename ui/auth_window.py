import sys
import os

import re
import requests  # Used to communicate with FastAPI backend

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, QVBoxLayout, QWidget, QStackedWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QThread


# 📌 MODEL: Handles API communication
class AuthModel(QObject):
    def register(self, email, password):
        try:
            response = requests.post(f"http://127.0.0.1:8000/user_registration?email={email}&password={password}")
            return response.status_code, response.json()
            # if response.status_code == 200:
            #     return response.json() # ["message"]  # Expected: "Email exists" or "Email does not exist"
            # elif response.status_code == 500:
            #     return response.json()["detail"]
            # else:
            #     return "Server error"
        except requests.RequestException:
            return None, "Network error"
    
    def login(self, email, password):
        try:
            response = requests.post(f"http://127.0.0.1:8000/user_login?email={email}&password={password}")
            return response.status_code, response.json()
        except requests.RequestException:
            return None, "Network error"

# VIEWMODEL: Handles validation + calls the model
class AuthViewModel(QObject):
    result_signal_to_ui = pyqtSignal(str) # Signal to update the UI with the result;
    state_changed = pyqtSignal()    # Signal to indicate a change in state — currently not used;
    auth_successful = pyqtSignal()  # Signal to indicate successful login;
    processing = pyqtSignal(bool)   # Emit True when waiting for response, False when done;


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

    def login_user(self, email, password):
        if not self.validate_email(email):
            self.result_signal_to_ui.emit("Invalid email format")
            return False
        
        self.processing.emit(True)
        self.worker = AuthWorker(self.model, email, password, "login")
        self.worker.result_signal.connect(self.proceess_response)
        self.worker.start()

    def register_user(self, email, password1, password2):
        if not self.validate_email(email):
            self.result_signal_to_ui.emit("Invalid email format")
            return False

        if not self.validate_passwords(password1, password2):
            return False

        self.processing.emit(True)
        self.worker = AuthWorker(self.model, email, password1, "register")
        self.worker.result_signal.connect(self.proceess_response)
        self.worker.start()

    def validate_email(self, email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None # regex validation
    
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
        if password is
            >7 char
            has at least one {A, a, 1, !}
            no repeating char
            etc
        """
        return 1
    
    def proceess_response(self, status_code, response):
        self.processing.emit(False)

        if os.getenv("DEVELOP_MACHINE"):
            print(status_code, response)
        
        if status_code == 200:
            self.auth_successful.emit()
        else:
            """
            add response filters (instead of outputting the raw responce from the server, output a "filtered" responce)
            example (note: not the actual responce from the server):
                response - a json file with a message "user provided invalid email"
                filtered_response = "Invalid email or password"
                seld.result_signal_to_ui.emit(filtered_response)
            """
            self.result_signal_to_ui.emit(str(response))


# 🏃‍♂️ Worker Thread for API Call (Prevents UI Freezing)
class AuthWorker(QThread):
    result_signal = pyqtSignal(int, dict)

    def __init__(self, model, email, password, action):
        super().__init__()
        self.model = model
        self.email = email
        self.password = password
        self.action = action # "register" or "login"
    
    def run(self):
        status_code, response = getattr(self.model, self.action)(self.email, self.password)
        self.result_signal.emit(status_code, response)


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
        self.reg_button.clicked.connect(self.register_helper)
        self.view_model.result_signal_to_ui.connect(self.update_result)

    def register_helper(self):
        email = self.email_input.text()
        password1 = self.password_input.text()
        password2 = self.repeat_password_input.text()
        self.view_model.register_user(email, password1, password2)

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
        self.login_button = QPushButton("Login", self)
        self.login_button.setDefault(True)      # Makes it the default button
        self.login_button.setAutoDefault(True)  # Allows Enter key activation
        # self.email_input.setFocus()            # Ensure it gets keyboard focus on launch

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

        self.setLayout(layout)  # Directly set the layout

        # 🎯 Connect UI to ViewModel
        self.login_button.clicked.connect(self.login_helper)
        self.view_model.result_signal_to_ui.connect(self.update_result)

    def login_helper(self):
        email = self.email_input.text()
        password = self.password_input.text()
        self.view_model.login_user(email, password)

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

        # Connect the remaining signals
        self.view_model.auth_successful.connect(self.handle_success)
        self.view_model.processing.connect(self.set_processing_state)
        self.is_processing = False

        # Example spinner label (could be a QMovie or similar)
        self.spinner_label = QLabel("Loading...", self)
        self.spinner_label.hide()
        # Add spinner_label to your layout as needed

    def update_view(self):
        view_model.result_signal_to_ui.emit("")
        self.stacked_widget.setCurrentIndex(self.view_model.current_state)
    
    def handle_success(self):
        self.close()  # Closes the window on successful login

    def set_processing_state(self, state):
        self.is_processing = state
        if state:
            # Disable the UI elements that could trigger closure or further action
            self.spinner_label.show()
        else:
            self.spinner_label.hide()

    # Prevent closing the window while processing
    def closeEvent(self, event):
        if self.is_processing:
            event.ignore()  # Disables closing when waiting for a server response
        else:
            event.accept()


if __name__ == "__main__":
    if os.getenv("DEVELOP_MACHINE"):
        print("Running on the development machine.")

    # QApplication.setAttribute(Qt.AA_MacUseFullKeyboardNavigation, True)
    app = QApplication(sys.argv)

    model = AuthModel()
    view_model = AuthViewModel(model)
    window = AuthView(view_model)

    window.show()
    sys.exit(app.exec_())