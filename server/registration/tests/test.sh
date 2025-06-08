#!/bin/bash

# Тест регистрации
REG_STATUS=$(curl -X POST "http://127.0.0.1:8000/user_registration" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword"}' \
  -w "%{http_code}\n" -o /dev/null)
if [ "$REG_STATUS" != "200" ]; then
  echo "Registration failed with status $REG_STATUS"
  exit 1
fi

# Тест входа
LOGIN_STATUS=$(curl -X POST "http://127.0.0.1:8000/user_login" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpassword"}' \
  -w "%{http_code}\n" -o /dev/null)
if [ "$LOGIN_STATUS" != "200" ]; then
  echo "Login failed with status $LOGIN_STATUS"
  exit 1
fi

# Тест обновления баланса
UPDATE_BALANCE=$(curl -X POST "http://127.0.0.1:8000/update_balance" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "amount": 100.0}' \
  -w "%{http_code}\n" -o /dev/null)
if [ "$UPDATE_BALANCE" != "200" ]; then
    echo "Update balance failed with status $UPDATE_BALANCE"
    exit 1
fi

# Тест получения данных пользователей
GET_DATA=$(curl "http://127.0.0.1:8000/get_users_db" \
  -H "accept: application/json" \
  -w "%{http_code}\n" -o /dev/null)
if [ "$GET_DATA" != "200" ]; then
    echo "Getting database failed with status $GET_DATA"
    exit 1
fi

# Тест выхода
LOGAUT_STATUS=$(curl -X POST "http://127.0.0.1:8000/user_logout" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}' \
  -w "%{http_code}\n" -o /dev/null)
if [ "$LOGAUT_STATUS" != "200" ]; then
    echo "Logout failed with status $LOGAUT_STATUS"
    exit 1
fi

echo "All tests passed successfully!"