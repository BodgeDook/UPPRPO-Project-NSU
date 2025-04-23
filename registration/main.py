from fastapi import FastAPI
from auth import router as auth_router
from verification import router as verification_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(verification_router)
