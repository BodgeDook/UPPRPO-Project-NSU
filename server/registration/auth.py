import json
import logging
import re
from decimal import Decimal
from fastapi import HTTPException, APIRouter
from passlib.hash import pbkdf2_sha256
from pydantic import BaseModel, EmailStr, Field
from db import connect_to_db

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic модели
class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserLogout(BaseModel):
    email: EmailStr

class UpdateBalance(BaseModel):
    email: EmailStr
    amount: float

def normalize_email_for_filename(email: str) -> str:
    return re.sub(r"[^\w]", "_", email)

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
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in save_to_db: {str(e)}", exc_info=True)
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
            "SELECT email, password, balance FROM users WHERE email = $1;",
            email
        )
        if row is None:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not pbkdf2_sha256.verify(password, row["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        await conn.execute(
            "UPDATE users SET is_logged_in = TRUE WHERE email = $1;",
            email
        )

        await conn.close()
        return {"email": row["email"], "balance": float(row["balance"])}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error in login: {str(e)}", exc_info=True)
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

@router.post("/user_registration")
async def save_data(user: UserRegistration):
    hashed_password = pbkdf2_sha256.hash(user.password)
    return await save_to_db(user.email, hashed_password)

@router.post("/user_login")
async def post_login(user: UserLogin):
    return await login(user.email, user.password)

@router.post("/user_logout")
async def post_logaut(user: UserLogout):
    return await logaut(user.email)

@router.get("/get_users_db")
async def get_data():
    return await get_data_from_db()

@router.post("/update_balance")
async def update_balance_endpoint(user: UpdateBalance):
    return await update_balance(user.email, user.amount)