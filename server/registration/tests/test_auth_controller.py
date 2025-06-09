# server/registration/tests/test_auth_controller.py
import sys
import os
import importlib.util
import pytest

# корневая директория в sys path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# динамический импорт модуля auth из desktop-app/controllers
spec = importlib.util.spec_from_file_location(
    "auth", os.path.join(os.path.dirname(__file__), '../../..', 'desktop-app', 'controllers', 'auth.py')
)
auth_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth_module)
AuthController = auth_module.AuthController

from unittest.mock import Mock

@pytest.fixture
def auth_controller():
    model = Mock()
    controller = AuthController(model)
    return controller

def test_is_valid_password_valid(auth_controller):
    valid_password = "MyPass123!"
    assert auth_controller.is_valid_password(valid_password) == True

def test_is_valid_password_too_short(auth_controller):
    short_password = "MyPa1!"
    assert auth_controller.is_valid_password(short_password) == False

def test_validate_passwords_mismatch(auth_controller):
    password1 = "MyPass123!"
    password2 = "MyPass124!"
    auth_controller.result_signal_to_ui = Mock()
    assert auth_controller.validate_passwords(password1, password2) == False
    auth_controller.result_signal_to_ui.emit.assert_called_once_with("Passwords do not match")