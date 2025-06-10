# tests/test_verification.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from main import app  # routrr for verification
from verification import is_code_valid, connect_to_db # mbmb

client = TestClient(app)


@pytest.fixture
def mock_db():
    with patch("verification.connect_to_db") as mock_connect:
        mock_conn = AsyncMock() # connect_to_db -- async
        mock_connect.return_value = mock_conn # budet vozvrashat'sa mock_conn posle visova connect_to_db
        yield mock_conn # ochistka fiksturi posle testa

@pytest.fixture
def mock_generate_code():
    with patch("verification.generate_code") as mock_gen:
        mock_gen.return_value = "123456"
        yield mock_gen

@pytest.fixture
def mock_send_email():
    with patch("verification.send_email_async") as mock_email:
        yield mock_email

def test_check_code_valid(mock_db):
    mock_db.fetchrow.return_value = {"code": "123456", "is_used": False} # conn.fetchrow("SELECT code, is_used FROM verification_codes WHERE email = $1;", email)
        # await conn.execute("""
        #     UPDATE verification_codes
        #     SET is_used = true
        #     WHERE email = $1;
        # """, email)
    mock_db.execute.return_value = None

    data = {"email": "test@example.com", "user_code": "123456"}
    response = client.post("/check-code/", json=data)
    assert response.status_code == 200
    
    data = {"email": "test@example.com", "user_code": "123455"}
    response = client.post("/check-code/", json=data)
    assert response.status_code != 200


def test_send_verification_code(mock_db, mock_generate_code):

    mock_db.fetchval.return_value = 0
    mock_db.execute.return_value = None

    data = {"email": "test@example.com"}

    response = client.post("/send-code/", json=data)

    assert response.status_code == 200

    mock_generate_code.assert_called_once()
    generated_code = mock_generate_code.return_value
    assert generated_code == "123456"
    assert generated_code.isdigit() and len(generated_code) == 6