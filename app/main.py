"""FastAPI application entry point for Data Explorer."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import auth, queries, upload, visualize

app = FastAPI(
    title="Data Explorer",
    version="1.0.0",
    description="Upload, explore, query, and visualize datasets with real-time charts.",
)

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


@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "ok"}


app.include_router(auth.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(visualize.router, prefix="/api")
app.include_router(queries.router, prefix="/api")
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
