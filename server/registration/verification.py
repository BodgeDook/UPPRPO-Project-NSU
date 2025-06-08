import random
import ssl
import json
import os
import asyncio
from functools import partial

from fastapi import BackgroundTasks, HTTPException, APIRouter
from pydantic import BaseModel, EmailStr, Field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from dotenv import load_dotenv
load_dotenv()

from db import connect_to_db

sender_email = os.getenv("EMAIL_SENDER")
sender_password = os.getenv("EMAIL_PASSWORD")

router = APIRouter()

# Модели Pydantic для валидации
class EmailSchema(BaseModel):
    email: EmailStr  # Автоматическая валидация формата email

class CheckCodeSchema(BaseModel):
    email: EmailStr
    user_code: str = Field(..., pattern=r"^\d{6}$")

def generate_code():
    return str(random.randint(100000, 999999))

def send_email(receiver_email, verification_code):
    if not sender_email:
        raise HTTPException(status_code=500, detail="EMAIL_SENDER environment variable not set")
    if not sender_password:
        raise HTTPException(status_code=500, detail="EMAIL_PASSWORD environment variable not set")

    subject = "Confirmation of registration (no reply please)"

    # HTML-содержимое письма
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f6f6f6; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
          <h2 style="text-align: center; color: #333;"> Email Verification Code</h2>
          <p style="text-align: center; font-size: 16px; color: #555;">Use the following code to complete your registration:</p>
          <div style="font-size: 24px; font-weight: bold; text-align: center; padding: 15px; background-color: #f0f0f0; border: 2px dashed #4CAF50; border-radius: 5px; margin: 20px 0;">
            {verification_code}
          </div>
          <p style="text-align: center; color: #888;">This code is valid for a limited time. Please do not share it with anyone.</p>
        </div>
      </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    plain_text = f"Your code: {verification_code}"

    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_content, "html"))

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
        return {"status": "success", "message": "Code verified successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification error: {str(e)}")

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
curl -X POST "http://127.0.0.1:8000/check-code" -H "Content-Type: application/json" -d '{"email": "<email>", "user_code": "<code>"}'
"""
@router.post("/check-code")
async def check_code(data: CheckCodeSchema):
    return await is_code_valid(data.email, data.user_code)