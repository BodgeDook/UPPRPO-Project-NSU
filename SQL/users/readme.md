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
\d users
                          Table "public.users"
    Column    |          Type          | Collation | Nullable | Default 
--------------+------------------------+-----------+----------+---------
 email        | character varying(255) |           | not null | 
 password     | character varying(255) |           | not null | 
 balance      | numeric(10,2)          |           | not null | 0.00
 is_logged_in | boolean                |           |          | false
Indexes:
    "users_pkey" PRIMARY KEY, btree (email)


#### Status CODES
*POST user_registration*

Code | Meaning                         | Implemented
-----+---------------------------------+------------
500  | DB connection failed            | Yes
409  | Email already exists            | Yes
500  | Unexpecred error {error message}| Yes
200  | Successful registration         | No



*POST user_login*

Code  | Meaning                         | Implemented
------+---------------------------------+------------
500   | DB connection failed            | Yes
401   | Invalid email or password       | Yes
500   | Unexpecred error {error message}| Yes
200   | Successful login                | No
