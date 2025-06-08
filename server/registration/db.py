import os

import asyncpg
from fastapi import HTTPException
from dotenv import load_dotenv


load_dotenv()
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
database = os.getenv("POSTGRES_DATABASE")
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT")


DB_PARAMS = {
    "user": user,
    "password": password,
    "database": database,
    "host": host,
    "port": port
}

async def connect_to_db():
    try:
        print(f"Connecting with: user={os.getenv('POSTGRES_USER')}, password=****, database={os.getenv('POSTGRES_DATABASE')}, host={os.getenv('POSTGRES_HOST')}, port={os.getenv('POSTGRES_PORT')}")
        conn = await asyncpg.connect(**DB_PARAMS)
        return conn
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="DB connection failed")
