"""Shared pytest fixtures for Data Explorer tests.

IMPORTANT: We mount routers into a *standalone* FastAPI() instance rather
than importing the real ``app.main.app``.  This avoids lifespan hangs that
occur when TestClient wraps a full application with StaticFiles mounted at
the root — those hangs block CI for minutes per test file.
"""
from __future__ import annotations

import io
import textwrap

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import upload, visualize
from app.services.data_service import DataService


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_app() -> FastAPI:
    """Minimal FastAPI app with only the API routers — no StaticFiles."""
    app = FastAPI(title="data-explorer-test")
    app.include_router(upload.router, prefix="/api")
    app.include_router(visualize.router, prefix="/api")
    return app


@pytest.fixture()
def client(test_app: FastAPI) -> TestClient:
    """Synchronous TestClient bound to the minimal test app."""
    return TestClient(test_app)


# ---------------------------------------------------------------------------
# Pre-seeded client: one CSV dataset already ingested
# ---------------------------------------------------------------------------

CSV_CONTENT = textwrap.dedent(
    """\
    name,age,score
    Alice,30,95.5
    Bob,25,82.0
    Carol,28,88.0
    Dave,35,70.0
    Eve,22,91.0
    """
).encode()

JSON_CONTENT = (
    b'[{"name":"Alice","value":10},{"name":"Bob","value":20}]'
)


@pytest.fixture()
def seeded_client(client: TestClient) -> TestClient:
    """Client with a single CSV dataset ('sample') already uploaded."""
    files = {"file": ("sample.csv", io.BytesIO(CSV_CONTENT), "text/csv")}
    resp = client.post("/api/upload", files=files)
    assert resp.status_code == 200, resp.text
    return client


# ---------------------------------------------------------------------------
# Isolated DataService (no HTTP layer)
# ---------------------------------------------------------------------------

@pytest.fixture()
def data_service() -> DataService:
    """Fresh DataService instance per test — no shared state."""
    return DataService()
