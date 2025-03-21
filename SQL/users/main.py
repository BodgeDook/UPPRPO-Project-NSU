import json
import time
import os

from decimal import Decimal 
from fastapi import FastAPI, Query
from fastapi import HTTPException
import uvicorn
import psycopg2

if os.getenv("DEVELOP_MACHINE"):
    print("Running on the development machine.")


DB_PARAMS = {
    "dbname": "upprpo_users",
    "user": "postgres",
    "password": "1234",  
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
        raise HTTPException(status_code=500, detail="DB connection failed")


def save_to_db(email: str, password: str):
    try:
        conn, cur = connect_to_db()
        if conn is None or cur is None:
            raise HTTPException(status_code=500, detail="DB connection failed")

        cur.execute("SELECT COUNT(*) FROM users WHERE email = %s;", (email,))
        result = cur.fetchone()

        if result[0] > 0:
            raise HTTPException(status_code=409, detail="Email already exists")
        

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
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def get_data_from_db():

    try:
        conn, cur = connect_to_db()
        if conn is None or cur is None:
            raise HTTPException(status_code=500, detail="DB connection failed")
        
        cur.execute("SELECT * FROM users;")  
        rows = cur.fetchall()
        
        conn.close()
        
        data = [{"email": row[0], "password": row[1], "balance": float(row[2]), "is log": row[3]} for row in rows]

        with open("account.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

def update_balance(email: str, amount: float):
    try:
        conn, cur = connect_to_db()
        if conn is None or cur is None:
            raise HTTPException(status_code=500, detail="DB connection failed")

        cur.execute("SELECT COUNT(*) FROM users WHERE email = %s;", (email,))
        result = cur.fetchone()

        if result[0] == 0:
            raise HTTPException(status_code=401, detail="Invalid email")


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
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")



def login(email: str, password: str):
    try:
        conn, cur = connect_to_db()
        if conn is None or cur is None:
            raise HTTPException(status_code=500, detail="DB connection failed")

        cur.execute("SELECT email, balance FROM users WHERE email = %s AND password = %s;", (email, password))
        result = cur.fetchone()

        if result is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user_email, user_balance = result

        cur.execute(
            """
            UPDATE users
            SET is_logged_in = TRUE
            WHERE email = %s;
            """,
            (email,)
        )

        conn.commit()
        cur.close()
        conn.close()
        return {"email": user_email, "balance": user_balance}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


def logaut(email:str):
    try:
        conn, cur = connect_to_db()
        if conn is None or cur is None:
            raise HTTPException(status_code=500, detail="DB connection failed")
        
        
        cur.execute("SELECT is_logged_in FROM users WHERE email = %s;", (email,))
        result = cur.fetchone()

        if result is None:
            raise HTTPException(status_code=401, detail="Invalid email")
        if result[0] is False:
            raise HTTPException(status_code=409, detail="User already logged in")

        cur.execute(
                    """
                    UPDATE users
                    SET is_logged_in = FALSE
                    WHERE email = %s;
                    """,
                    (email,)
                )
        conn.commit()
        cur.close()
        conn.close()
        return {"user:", email, "was disconnected!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")




app = FastAPI()


# curl -X 'POST' 'http://127.0.0.1:8000/user_registration?email=<email>&password=<password>' -H 'accept: application/json'
@app.post("/user_registration")
def save_data(email: str, password: str):
    if os.getenv("DEVELOP_MACHINE"):
        time.sleep(5)
    
    return save_to_db(email, password)

# curl -X 'POST' 'http://127.0.0.1:8000/user_login?email=<email>&password=<password>' -H 'accept: application/json'
@app.post("/user_login")
def post_login(email: str, password: str):
    if os.getenv("DEVELOP_MACHINE"):
        time.sleep(5)

    return login(email, password)

# curl "http://127.0.0.1:8000/user_logout?email=<email>" 
@app.get("/user_logout")
def post_logaut(email: str):
    return logaut(email)

# curl "http://127.0.0.1:8000/get_all_db" 
@app.get("/get_all_db")
def get_data():
    return get_data_from_db()

# curl "http://127.0.0.1:8000/update_balance?email=<user_email>&amount=<some_float_val>"
@app.get("/update_balance")
def update_balance_endpoint(email: str, amount: float):
    response = update_balance(email, amount)
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)



