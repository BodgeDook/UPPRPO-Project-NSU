START SERVER:
  $python3 main.py

REGISTRATE USER:
  $curl -X 'POST' 'http://127.0.0.1:8000/user_registration?email=<user_email>&password=<user_password>' -H 'accept: application/json'

LOGIN USER:
  $curl -X 'POST' 'http://127.0.0.1:8000/user_login?email=<email>&password=<password>' -H 'accept: application/json'

LOGOUT USER:
  $curl "http://127.0.0.1:8000/user_logout?email=<email>" 


GET ALL DATA FROM DB:
  $curl "http://127.0.0.1:8000/get_all_db" 

ADD SOME MONEY TO CERTAIN USER:
  $curl "http://127.0.0.1:8000/update_balance?email=<user_email>&amount=<some_float_val>"



table structure:
### Users Table

| Column      | Type                    | Nullable | Default |
|------------|-------------------------|----------|---------|
| email      | character varying(255)  | NOT NULL |         |
| password   | character varying(255)  | NOT NULL |         |
| balance    | numeric(10,2)           | NOT NULL | 0.00    |
| is_logged_in | boolean               |          | false   |

**Indexes:**
- `users_pkey` PRIMARY KEY, btree (email)


#### Status CODES
### POST /`user_registration`

| Code | Meaning                          | Implemented |
|------|----------------------------------|-------------|
| 500  | DB connection failed            | Yes         |
| 409  | Email already exists            | Yes         |
| 500  | Unexpected error {error message} | Yes         |
| 200  | Successful registration         | No          |



### POST /`user_login`

| Code  | Meaning                          | Implemented |
|-------|----------------------------------|-------------|
| 500   | DB connection failed            | Yes         |
| 401   | Invalid email or password       | Yes         |
| 500   | Unexpected error {error message} | Yes         |
| 200   | Successful login                | No          |


#### Environment variables
DEVELOP_MACHINE — indicates if the code is being run on developer's machine, duh.
Used in post_login() and save_data() to imitate loading times.

```sh
export DEVELOP_MACHINE=1
```
+reload your terminal

_On macOS:_
```sh
echo 'export DEVELOP_MACHINE=1' >> ~/.zshrc
source ~/.zshrc
```