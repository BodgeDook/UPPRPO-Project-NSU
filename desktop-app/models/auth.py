# desktop-app/models/auth.py

import requests  # Used to communicate with FastAPI backend


class AuthModel:
    """
    Handles API communication for registration and login.
    """

    def register(self, email, password):
        try:
            headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
            data = {
                "email": email,
                "password": password
            }
            response = requests.post(
                "http://127.0.0.1:8000/user_registration",
                json=data,
                headers=headers
            )
            return response.status_code, response.json()
        except requests.RequestException:
            return None, "Network error"
    
    def login(self, email, password):
        try:
            headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
            data = {
                "email": email,
                "password": password
            }
            response = requests.post(
                "http://127.0.0.1:8000/user_login",
                json=data,
                headers=headers
            )
            return response.status_code, response.json()
        except requests.RequestException:
            return None, "Network error"

    def send_code(self, email):
        try:
            headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
            data = {
                "email": email
            }
            response = requests.post(
                "http://127.0.0.1:8000/send-code/",
                json=data,
                headers=headers
            )
            return response.status_code, response.json()
        except requests.RequestException:
            return None, "Network error"
        
    def verify_code(self, email, user_code):
        try:
            headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
            data = {
                "email": email,
                "user_code": user_code
            }
            response = requests.post(
                "http://127.0.0.1:8000/check-code/",
                json=data,
                headers=headers
            )
            return response.status_code, response.json()
        except requests.RequestException:
            return None, "Network error"
    
    def logout(self, email):
        try:
            headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
            data = {
                "email": email
            }
            response = requests.post(
                "http://127.0.0.1:8000/user_login",
                json=data,
                headers=headers
            )
            return response.status_code, response.json()
        except requests.RequestException:
            return None, "Network error"
