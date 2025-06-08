# desktop-app/models/auth.py

import requests  # Used to communicate with FastAPI backend

# URL = "http://127.0.0.1:8000/"
URL = "https://umovie.gehrman.me/api"


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
                str(URL + "/user_registration"),
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
                str(URL + "/user_login"),
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
                str(URL + "/send-code/"),
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
                str(URL + "/check-code/"),
                json=data,
                headers=headers
            )
            return response.status_code, response.json()
        except requests.RequestException:
            return None, "Network error"
    
    def change_password(self, email, new_password):
        try:
            headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
            data = {
                "email": email,
                "password": new_password
            }
            response = requests.post(
                str(URL + "/user_change_password"),
                json=data,
                headers=headers
            )
            return response.status_code, response.json()
        except requests.RequestException:
            return None, "Network error"
