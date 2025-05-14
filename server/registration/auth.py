import json

from decimal import Decimal
from fastapi import Query, HTTPException, APIRouter

from db import connect_to_db

router = APIRouter()


async def save_to_db(email: str, password: str):
    try:
        conn = await connect_to_db()

        result = await conn.fetchval("SELECT COUNT(*) FROM users WHERE email = $1;", email)
        if result > 0:
            raise HTTPException(status_code=409, detail="Email already exists")

        await conn.execute(
            "INSERT INTO users (email, password) VALUES ($1, $2);",
            email, password
        )
        await conn.close()
        return {"status": "success", "email": email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def get_data_from_db():
    try:
        conn = await connect_to_db()
        rows = await conn.fetch("SELECT * FROM users;")
        await conn.close()

        data = [{
            "email": row["email"],
            "password": row["password"],
            "balance": float(row["balance"]),
            "is log": row["is_logged_in"]
        } for row in rows]

        with open("account.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def update_balance(email: str, amount: float):
    try:
        conn = await connect_to_db()

        result = await conn.fetchval("SELECT COUNT(*) FROM users WHERE email = $1;", email)
        if result == 0:
            raise HTTPException(status_code=401, detail="Invalid email")

        current_balance = await conn.fetchval("SELECT balance FROM users WHERE email = $1;", email)
        new_balance = current_balance + Decimal(str(amount))

        await conn.execute(
            "UPDATE users SET balance = $1 WHERE email = $2;",
            new_balance, email
        )

        await conn.close()
        return {"status": "success", "email": email, "new_balance": float(new_balance)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def login(email: str, password: str):
    try:
        conn = await connect_to_db()
        row = await conn.fetchrow(
            "SELECT email, balance FROM users WHERE email = $1 AND password = $2;",
            email, password
        )
        if row is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        await conn.execute(
            "UPDATE users SET is_logged_in = TRUE WHERE email = $1;",
            email
        )

        await conn.close()
        return {"email": row["email"], "balance": row["balance"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def logaut(email: str):
    try:
        conn = await connect_to_db()

        result = await conn.fetchval("SELECT is_logged_in FROM users WHERE email = $1;", email)
        if result is None:
            raise HTTPException(status_code=401, detail="Invalid email")
        if result is False:
            raise HTTPException(status_code=409, detail="User already logged out")

        await conn.execute(
            "UPDATE users SET is_logged_in = FALSE WHERE email = $1;",
            email
        )

        await conn.close()
        return {"user": email, "status": "disconnected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

async def check_is_email_exists(email: str):
    try:
        conn = await connect_to_db()
        result = await conn.fetchval("SELECT COUNT(*) FROM users WHERE email = $1;", email)
        await conn.close()

        if result > 0:
            raise HTTPException(status_code=409, detail="Email already exists")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


"""
curl -X 'POST' 'http://127.0.0.1:8000/user_registration?email=<email>&password=<password>' -H 'accept: application/json'
"""
@router.post("/user_registration")
async def save_data(email: str, password: str):
    return await save_to_db(email, password)

"""
curl -X 'POST' 'http://127.0.0.1:8000/user_login?email=<email>&password=<password>' -H 'accept: application/json'
"""
@router.post("/user_login")
async def post_login(email: str, password: str):
    return await login(email, password)

"""
curl "http://127.0.0.1:8000/user_logout?email=<email>" 
"""
@router.get("/user_logout")
async def post_logaut(email: str):
    return await logaut(email)

"""
curl "http://127.0.0.1:8000/get_users_db" 
"""
@router.get("/get_users_db")
async def get_data():
    return await get_data_from_db()

"""
curl "http://127.0.0.1:8000/update_balance?email=<user_email>&amount=<some_float_val>"
"""
@router.get("/update_balance")
async def update_balance_endpoint(email: str, amount: float):
    return await update_balance(email, amount)
