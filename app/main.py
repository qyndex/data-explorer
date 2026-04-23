import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import upload, visualize

app = FastAPI(title="Data Explorer", version="0.1.0")

# CORS: restrict origins in production, allow localhost for dev
ALLOWED_ORIGINS = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(upload.router, prefix="/api")
app.include_router(visualize.router, prefix="/api")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
