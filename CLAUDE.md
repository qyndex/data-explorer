# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Data Explorer — Upload CSV/JSON files, explore data with tables, visualize with charts (Plotly), and export results. In-memory dataset store; no database required.

Built with FastAPI 0.135+, Python 3.13, Pydantic v2, pandas 3, plotly 6, and Uvicorn.

## Commands

```bash
cp .env.example .env                              # Configure environment variables
pip install -r requirements.txt                   # Install dependencies
uvicorn app.main:app --reload --port 8000         # Start dev server (http://localhost:8000)
python -m pytest tests/ -v --tb=short            # Run tests
ruff check .                                      # Lint
ruff format .                                     # Format
docker compose up --build                        # Run via Docker
```

## Architecture

```
app/
  main.py                  — FastAPI app, CORS middleware, router registration, static mount
  routers/
    upload.py              — POST /api/upload, GET /api/datasets, GET /api/datasets/{name}/preview
    visualize.py           — GET /api/visualize/{name}, GET /api/export/{name}
  services/
    data_service.py        — DataService: ingest, list, preview, generate_chart, export
frontend/
  index.html               — Vanilla JS UI served as static files at /
tests/
  conftest.py              — Fixtures: test_app (standalone FastAPI), client, seeded_client, data_service
  test_data_service.py     — Unit tests for DataService (no HTTP)
  test_upload_router.py    — Integration tests for upload/datasets routes
  test_visualize_router.py — Integration tests for visualize/export routes + full round-trip
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/upload | Upload CSV or JSON file; returns filename + summary |
| GET | /api/datasets | List all ingested dataset names |
| GET | /api/datasets/{name}/preview | Preview first N rows (default 10) |
| GET | /api/visualize/{name} | Generate Plotly chart HTML |
| GET | /api/export/{name} | Export as CSV or JSON |

All list responses use named envelopes (e.g. `{"datasets": [...]}`) — never bare arrays.

## Environment Variables

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Uvicorn listen port |
| `HOST` | `0.0.0.0` | Uvicorn listen host |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated allowed origins |

## Rules

- Pydantic models for all request/response bodies
- Async handlers (`async def`) for all endpoints
- Type hints on all function signatures
- Response envelopes: return `{"key": [...]}` — never bare arrays
- OpenAPI docs auto-generated at `/docs`

## Testing Notes

- `conftest.py` mounts only the API routers into a standalone `FastAPI()` app — **never** use `TestClient(app.main.app)` directly (the `StaticFiles` mount at `/` causes lifespan hangs in CI)
- `seeded_client` fixture pre-uploads `sample.csv` with columns `name, age, score`
- Tests are self-contained — `DataService` state is per-instance, no shared state between tests
