START SERVER:
  $python3 main.py

ADD USER:
  $curl -X 'POST' 'http://127.0.0.1:8000/save_to_db?email=<user_email>&password=<user_password>' -H 'accept: application/json'

SHOW ALL DB:
  $curl "http://127.0.0.1:8000/get_data"

ADD SOME MONEY TO CERTAIN USER:
  $curl "http://127.0.0.1:8000/update_balance?email=<user_email>&<number(it may be float)>"