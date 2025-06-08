# 📚 Table of Contents

- [Preparation](#preparation)
  - [vscode part](#vscode-part)
  - [SQL part](#sql-part)
  - [Docker](#docker)
- [Launch](#launch)
- [FastApi requests](#fastapi-requests)
- [HTTP Exceptions](#http-exceptions)

# Preparation
## vscode part
```
pip install -r requirements.txt
```
You also need to create an *.env* file to work with your PostgreSQL database and Google account, from which confirmation codes will be sent.
There should be such constance:
```
EMAIL_SENDER=
EMAIL_PASSWORD=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DATABASE=
POSTGRES_HOST=fastapi_db
POSTGRES_PORT=5432
```
EMAIL_PASSWORD - it is the app password of the Google account from which the messages will be sent.
You can read it in detail [here.](https://support.google.com/mail/answer/185833?hl=en&ref_topic=3394217&sjid=5235200406851987490-EU)

## SQL part

**users table**

| Column       | Type                     | Nullable | Default |
|--------------|--------------------------|----------|---------|
| email        | `character varying(255)` | not null | -       |
| password     | `character varying(255)` | not null | -       |
| balance      | `numeric(10,2)`          | not null | `0.00`  |
| is_logged_in | `boolean`                | -        | `false` |
```
CREATE TABLE users (
    email VARCHAR(255) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    is_logged_in BOOLEAN DEFAULT FALSE
);
```

**veification_codes table**

| Column     | Type                          | Nullable | Default             |
|------------|-------------------------------|----------|---------------------|
| email      | `text`                        | not null | -                   |
| code       | `text`                        | not null | -                   |
| created_at | `timestamp without time zone` | -        | `CURRENT_TIMESTAMP` |
| is_used    | `boolean`                     | -        | `false`             |
```
CREATE TABLE verification_codes (
    email TEXT NOT NULL,
    code TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_used BOOLEAN DEFAULT FALSE
);
```

## Docker
```
docker-compose up --build
```


# Launch
To launch FastApi app:
```
uvicorn main:app --reload
```

# FastApi requests

- registration
  ```
  curl -X 'POST' 'http://127.0.0.1:8000/user_registration?email=<email>&password=<password>' -H 'accept: application/json'
  ```
- login
  ```
  curl -X 'POST' 'http://127.0.0.1:8000/user_login?email=<email>&password=<password>' -H 'accept: application/json'
  ```
- logout
  ```
  curl "http://127.0.0.1:8000/user_logout?email=<email>"
  ```
- update balance (optionally)
  ```
  curl "http://127.0.0.1:8000/update_balance?email=<user_email>&amount=<some_float_val>"
  ```
- save the users table in json
  ```
  curl "http://127.0.0.1:8000/get_users_db"
  ```

- send code to email
  ```
  curl -X POST "http://127.0.0.1:8000/send-code/" -H "Content-Type: application/json" -d '{"email": "<email>"}'
  ```
- compare the user's code with the code from the verification_codes table
  ```
  curl -X POST "http://127.0.0.1:8000/check-code" -H "Content-Type: application/json" -d '{"email": "<email>", "user_code": "<code>"}'
  ```
- save the verification_codes table in json
  ```
  curl "http://127.0.0.1:8000/get_codes_db" 
  ```

# HTTP Exceptions
```
200 -- OK
400 -- Bad Request
401 -- Unauthorized
404 -- Not Found
409 -- Conflict With Server
422 -- Unprocessable Content
500 -- Internal Server Error
```
