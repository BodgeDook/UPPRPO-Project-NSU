import json

from decimal import Decimal 
from fastapi import FastAPI, Query
import uvicorn
import psycopg2

# app = FastAPI()


DB_PARAMS = {
    "dbname": "",
    "user": "",
    "password": "",  
    "host": "localhost",
    "port": "5432"
}

def connect_to_db():
    """ Подключение к PostgreSQL """
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        return conn, cur
    except Exception as e:
        print(f"Error with connection to db: {e}")
        return None, None

def check_email_exists(email):
    try:
        conn, cur = connect_to_db()
        if conn is None or cur is None:
            return False

        cur.execute("SELECT COUNT(*) FROM parsed_data WHERE email = %s;", (email,))
        result = cur.fetchone()

        conn.close()

        return result[0] > 0
    except Exception as e:
        print(f"Exception checking email: {e}")
        return False
    

def save_to_db(email: str, password: str):
    try:
        conn, cur = connect_to_db()
        if conn is None or cur is None:
            return {"error": "DB didn't connected"}

        cur.execute("SELECT COUNT(*) FROM users WHERE email = %s;", (email,))
        result = cur.fetchone()

        if result[0] > 0:
            return {"error": "Email already exists"}
        

        cur.execute(
            """
            INSERT INTO users (email, password)
            VALUES (%s, %s);
            """,
            (email, password)
        )

        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success", "email": email}

    except Exception as e:
        print(f"Exception with saving bd: {e}")
        return {"error": str(e)}

def get_data_from_db():

    try:
        conn, cur = connect_to_db()
        if conn is None or cur is None:
            return {"error": "DB didn't connected"}
        
        cur.execute("SELECT * FROM users;")  
        rows = cur.fetchall()
        
        conn.close()
        
        data = [{"email": row[0], "password": row[1], "balance": float(row[2])} for row in rows]

        with open("account.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

        return data
    except Exception as e:
        print(f"Exception with reading bd: {e}")
        return {"error": str(e)}

def update_balance(email: str, amount: float):
    try:
        conn, cur = connect_to_db()
        if conn is None or cur is None:
            return {"error": "DB didn't connect"}

        cur.execute("SELECT COUNT(*) FROM users WHERE email = %s;", (email,))
        result = cur.fetchone()

        if result[0] == 0:
            return {"error": "Email not found"}


        cur.execute("SELECT balance FROM users WHERE email = %s;", (email,))
        current_balance = cur.fetchone()[0]

        new_balance = current_balance + Decimal(str(amount))
        cur.execute(
            """
            UPDATE users
            SET balance = %s
            WHERE email = %s;
            """,
            (new_balance, email)
        )

        conn.commit()
        cur.close()
        conn.close()

        return {"status": "success", "email": email, "new_balance": float(new_balance)}

    except Exception as e:
        print(f"Exception with updating balance: {e}")
        return {"error": str(e)}

def check_login_credentials(email: str, password: str):
    if True:
        return 0 # email/password matched
    if False:
        return 1 # email and/or password did not match or do not exist
    return 420


app = FastAPI()

@app.post("/login")
def login(email: str, password: str):

    message = check_login_credentials(email, password)
    if message: # so the password/email matched
        return 0
    else:
        return 1 # code for email/password incorect or does not exist

@app.post("/Register")
def register(email: str, password: str):
    if check_email_exists(email):
        return 2 # "this email exists" error
    else:
        status = save_to_db(email, password)
        if status == 0: # user registered
            return 0
        elif status == 1:   # user not registered
            #sql.delete(email/password)
            return 1
        else:
            #sql.delete(email/password)
            return 420  # "i dunno" error



# @app.get("/get_data")
# def get_data():
#     return get_data_from_db()

# @app.get("/update_balance")
# def update_balance_endpoint(email: str, amount: float):
#     response = update_balance(email, amount)
#     return response

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

