# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Data Explorer — Upload CSV/JSON files, explore data with tables, visualize with charts, and export results.

Built with FastAPI 0.135+, Python 3.13, Pydantic v2, and Uvicorn.

## Commands

```bash
pip install -r requirements.txt          # Install dependencies
uvicorn main:app --reload --port 8000    # Start dev server (http://localhost:8000)
python -m pytest                         # Run tests
ruff check .                             # Lint
ruff format .                            # Format
```

## Architecture

- `main.py` — FastAPI application entry point
- `routers/` — API route modules
- `models/` — Pydantic models and DB schemas
- `services/` — Business logic
- `tests/` — Test files

## Rules

- Pydantic models for all request/response bodies
- Parameterized SQL queries only — never string interpolation
- Async handlers (`async def`) for all endpoints
- OpenAPI docs auto-generated at `/docs`
- Type hints on all function signatures
