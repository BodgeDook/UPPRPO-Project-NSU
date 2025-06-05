# desktop-app/models/auth.py

import requests  # Used to communicate with FastAPI backend


class AuthModel:
    """
    Handles API communication for registration and login.
    """

    def register(self, email, password):
        try:
            response = requests.post(
                f"http://127.0.0.1:8000/user_registration?email={email}&password={password}"
            )
            return response.status_code, response.json()
        except requests.RequestException:
            return None, "Network error"

    def login(self, email, password):
        try:
            response = requests.post(
                f"http://127.0.0.1:8000/user_login?email={email}&password={password}"
            )
            return response.status_code, response.json()
        except requests.RequestException:
            return None, "Network error"
