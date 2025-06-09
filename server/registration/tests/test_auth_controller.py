# server/registration/tests/test_auth_controller.py
import sys
import os
import importlib.util
import pytest
from unittest.mock import Mock

# корневая директория в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# динамический импорт модуля auth из desktop-app/controllers
spec = importlib.util.spec_from_file_location(
    "auth", os.path.join(os.path.dirname(__file__), '../../..', 'desktop-app', 'controllers', 'auth.py')
)
auth_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth_module)
AuthController = auth_module.AuthController

@pytest.fixture
def auth_controller():
    model = Mock()
    controller = AuthController(model)
    controller.result_signal_to_ui = Mock()
    controller.state_changed = Mock()
    controller.forgot_password_state_changed = Mock()
    controller.auth_successful = Mock()
    controller.processing = Mock()
    return controller

def test_login_state(auth_controller):
    default_state = auth_controller.current_state
    auth_controller.switch_to_login()
    assert auth_controller.current_state == auth_controller.LOGIN
    auth_controller.state_changed.emit.assert_called_once()
    assert auth_controller.current_state != default_state

def test_register_state(auth_controller):
    auth_controller.switch_to_login()
    assert auth_controller.current_state != auth_controller.REGISTER
    auth_controller.switch_to_register()
    assert auth_controller.current_state == auth_controller.REGISTER

def test_forgot_password_state(auth_controller):
    default_state = auth_controller.current_state
    auth_controller.switch_to_forgot_password()
    assert auth_controller.current_state == auth_controller.FORGOT_PASSWORD
    assert auth_controller.forgot_password_state == auth_controller.FORGOT_PASSWORD_EMAIL
    assert auth_controller.current_state != default_state
    auth_controller.state_changed.emit.assert_called_once()
    auth_controller.forgot_password_state_changed.emit.assert_called_once()

def test_login_logic(auth_controller):
    auth_controller.validate_email = Mock(return_value=True)

    default_login_user = auth_controller.login_user

    def mocked_login_user(email, password):
        auth_controller.processing.emit(True)
        auth_controller.worker = Mock()
        auth_controller.worker.email = email
        auth_controller.worker.data= password
        auth_controller.worker.action = "login"
        auth_controller.worker.start = Mock()
    
    auth_controller.login_user = mocked_login_user
    auth_controller.login_user("test@gmail.com", "MyPass123!")
    auth_controller.processing.emit.assert_called_once_with(True)

    assert auth_controller.worker is not None
    assert auth_controller.worker.email == "test@gmail.com"
    assert auth_controller.worker.action == "login"
    assert auth_controller.worker.data == "MyPass123!"

    auth_controller.worker.start.assert_not_called()
    auth_controller.login_user = default_login_user

def test_register_logic(auth_controller):
    auth_controller.validate_email = Mock(return_value=True)
    auth_controller.validate_passwords = Mock(return_value=True)

    default_register_user = auth_controller.register_user

    def mocked_register_user(email, password1, password2):
        auth_controller.processing.emit(True)
        auth_controller.worker = Mock()
        auth_controller.worker.email = email
        auth_controller.worker.data = password1
        auth_controller.worker.action = "register"
        auth_controller.worker.start = Mock()

    auth_controller.register_user = mocked_register_user
    auth_controller.register_user("test@gmail.com", "MyPass123!", "MyPass123!")
    auth_controller.processing.emit.assert_called_once_with(True)   

    assert auth_controller.worker is not None
    assert auth_controller.worker.email == "test@gmail.com"
    assert auth_controller.worker.action == "register"
    assert auth_controller.worker.data == "MyPass123!"

    auth_controller.worker.start.assert_not_called()
    auth_controller.register_user = default_register_user


def test_is_invalid_password_invalid(auth_controller):

    short_invalid_password = "MyPas1!"
    assert auth_controller.is_valid_password(short_invalid_password) == False
    lower_invalid_password = "mypass123!"
    assert auth_controller.is_valid_password(lower_invalid_password) == False
    upper_invalid_password = "MYPASS123!"
    assert auth_controller.is_valid_password(upper_invalid_password) == False
    no_digit_invalid_password = "MyPasss!"
    assert auth_controller.is_valid_password(no_digit_invalid_password) == False
    no_special_invalid_password = "MyPass123"
    assert auth_controller.is_valid_password(no_special_invalid_password) == False

def test_is_valid_password_valid(auth_controller):
    valid_password = "MyPass123!"
    assert auth_controller.is_valid_password(valid_password) == True

def test_validate_passwords_mismatch(auth_controller):
    password1 = "MyPass123!"
    password2 = "MyPass124!"
    auth_controller.result_signal_to_ui = Mock()
    assert auth_controller.validate_passwords(password1, password2) == False
    auth_controller.result_signal_to_ui.emit.assert_called_once_with("Passwords do not match")