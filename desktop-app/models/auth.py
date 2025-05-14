import os
import requests
from PyQt5.QtCore import QThread, pyqtSignal, QObject


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


class AuthWorker(QThread):
    result = pyqtSignal(int, str)

    def __init__(self, model, email, password, action):
        super().__init__()
        self.model = model
        self.email = email
        self.password = password
        self.action = action # "register" or "login"
    
    def run(self):
        status_code, response = getattr(self.model, self.action)(self.email, self.password)
        self.result.emit(status_code, response)
