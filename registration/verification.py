import random
import ssl
import json
import re
import os
import asyncio
from functools import partial

from fastapi import BackgroundTasks, HTTPException, APIRouter
from pydantic import BaseModel
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import asyncpg
from dotenv import load_dotenv
load_dotenv()

from db import connect_to_db

sender_email = os.getenv("EMAIL_SENDER")
sender_password = os.getenv("EMAIL_PASSWORD")


class EmailSchema(BaseModel):
    email: str


def generate_code():
    return str(random.randint(100000, 999999))


def is_valid_email_format(email: str) -> bool:
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(email_regex, email) is not None


def send_email(receiver_email, verification_code):
    if not sender_email:
        raise HTTPException(status_code=500, detail="EMAIL_SENDER environment variable not set")
    if not sender_password:
        raise HTTPException(status_code=500, detail="EMAIL_PASSWORD environment variable not set")

    if not is_valid_email_format(receiver_email):
        raise HTTPException(status_code=400, detail="Invalid email format")

    subject = "Сonfirmation of registration (no reply pls)"
    body = f"Your code: {verification_code}"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email error: {str(e)}")


async def send_email_async(receiver_email, verification_code):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, partial(send_email, receiver_email, verification_code))


async def save_to_db(email: str, code: str):
    try:
        conn = await connect_to_db()

        result = await conn.fetchval("SELECT COUNT(*) FROM verification_codes WHERE email = $1;", email)

        if result > 0:
            await conn.execute("""
                UPDATE verification_codes
                SET code = $1, is_used = false
                WHERE email = $2;
            """, code, email)
        else:
            await conn.execute("""
                INSERT INTO verification_codes (email, code)
                VALUES ($1, $2);
            """, email, code)

        await conn.close()
        return {"status": "success", "email": email}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")


async def get_data_from_db():
    try:
        conn = await connect_to_db()
        rows = await conn.fetch("SELECT * FROM verification_codes;")
        await conn.close()

        data = [
            {
                "email": row["email"],
                "code": row["code"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "is_used": row["is_used"],
            }
            for row in rows
        ]

        with open("verification_codes.json", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB fetch error: {str(e)}")


async def is_code_valid(email: str, user_code: str):
    try:
        conn = await connect_to_db()
        row = await conn.fetchrow("SELECT code, is_used FROM verification_codes WHERE email = $1;", email)

        if not row:
            raise HTTPException(status_code=404, detail="Email not found")

        if row["is_used"]:
            raise HTTPException(status_code=400, detail="Code has already been used")

        if user_code != row["code"]:
            raise HTTPException(status_code=401, detail="Invalid code")

        await conn.execute("""
            UPDATE verification_codes
            SET is_used = true
            WHERE email = $1;
        """, email)

        await conn.close()
        return {"status": "success", "message": "Code verified successfully", "email": email}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")


router = APIRouter()

"""
curl -X POST "http://127.0.0.1:8000/send-code/" -H "Content-Type: application/json" -d '{"email": "<email>"}'
"""
@router.post("/send-code/")
async def send_verification_code(data: EmailSchema, background_tasks: BackgroundTasks):
    code = generate_code()
    background_tasks.add_task(send_email_async, data.email, code)
    return await save_to_db(data.email, code)


"""
curl "http://127.0.0.1:8000/get_codes_db" 
"""
@router.get("/get_codes_db")
async def get_data():
    return await get_data_from_db()


"""
curl -X POST "http://127.0.0.1:8000/check-code?email=<email>&user_code=<code>"
"""
@router.post("/check-code")
async def check_code(email: str, user_code: str):
    return await is_code_valid(email, user_code)
