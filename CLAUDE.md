# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Data Explorer — Upload CSV/JSON datasets, explore data with interactive tables, save and execute queries, visualize with Plotly charts, and export results. Backed by Supabase (PostgreSQL + Auth + RLS) for persistence and user isolation. Falls back to in-memory mode when Supabase is not configured.

Built with FastAPI 0.135+, Python 3.13, Pydantic v2, Supabase (auth + database), pandas 3, Plotly 6, and Uvicorn.

## Quick Start

```bash
# 1. Set up Supabase (local)
npx supabase start                          # Start local Supabase stack
npx supabase db reset                       # Apply migrations + seed data

# 2. Configure environment
cp .env.example .env
# Fill in values from `npx supabase status`:
#   SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET

# 3. Install and run
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000   # http://localhost:8000

# Demo login: demo@data-explorer.local / demo-password-123
```

### In-Memory Mode (No Database)

Leave `SUPABASE_URL` blank in `.env` to run without a database. Upload/preview/visualize/export work but data is lost on restart and auth is disabled.

## Commands

```bash
cp .env.example .env                              # Configure environment variables
pip install -r requirements.txt                   # Install dependencies
npx supabase start                                # Start local Supabase (Postgres + Auth)
npx supabase db reset                             # Apply migrations + seed data
uvicorn app.main:app --reload --port 8000         # Start dev server (http://localhost:8000)
python -m pytest tests/ -v --tb=short             # Run tests
ruff check .                                      # Lint
ruff format .                                     # Format
docker compose up --build                         # Run via Docker
```

## Architecture

```
app/
  main.py                  -- FastAPI app, CORS, router registration, health check, static mount
  auth.py                  -- JWT validation dependency (extracts user ID from Supabase JWT)
  database.py              -- Supabase client factory (service-role + anon clients)
  models.py                -- Pydantic request/response models for all endpoints
  routers/
    auth.py                -- POST /api/auth/signup, /signin, /signout, GET /api/auth/profile
    upload.py              -- POST /api/upload, GET /api/datasets, GET /api/datasets/{name}/preview
    visualize.py           -- GET /api/visualize/{name}, GET /api/export/{name}
    queries.py             -- CRUD /api/queries, POST /api/queries/{id}/execute, GET results
  services/
    __init__.py            -- Shared DataService singleton
    data_service.py        -- DataService: ingest, list, preview, chart, export, saved queries
frontend/
  index.html               -- Vanilla JS UI served as static files at /
supabase/
  config.toml              -- Supabase project configuration
  migrations/
    20240101000000_initial_schema.sql  -- profiles, datasets, saved_queries, query_results + RLS
  seed.sql                 -- Demo user + 3 datasets + 8 queries + 5 result snapshots
tests/
  conftest.py              -- Fixtures: test_app (standalone FastAPI), client, seeded_client
  test_data_service.py     -- Unit tests for DataService (no HTTP, no DB)
  test_upload_router.py    -- Integration tests for upload/datasets routes
  test_visualize_router.py -- Integration tests for visualize/export routes + round-trip
```

## Database Schema

Four tables, all with RLS (users see only their own data):

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `profiles` | id (UUID PK -> auth.users), email, full_name, plan | Auto-created via trigger on signup |
| `datasets` | id (UUID PK), owner_id (FK), name, schema (JSONB), row_count, source | Stores dataset metadata; actual data processed in-memory via pandas |
| `saved_queries` | id (UUID PK), owner_id (FK), dataset_id (FK), name, sql_query | User-saved analysis queries |
| `query_results` | id (UUID PK), query_id (FK), result_data (JSONB), execution_time_ms | Cached execution results |

## API Endpoints

### Auth (require no token)
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/signup | Register new user; returns JWT tokens |
| POST | /api/auth/signin | Sign in with email + password |

### Auth (require JWT)
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/auth/signout | Invalidate session |
| GET | /api/auth/profile | Get current user's profile |

### Datasets (auth optional for upload/list/preview)
| Method | Path | Description |
|--------|------|-------------|
| POST | /api/upload | Upload CSV or JSON file |
| GET | /api/datasets | List datasets (auth: full metadata; anon: names only) |
| GET | /api/datasets/{name}/preview | Preview first N rows (default 10) |
| GET | /api/visualize/{name} | Generate Plotly chart HTML |
| GET | /api/export/{name} | Export as CSV or JSON |

### Saved Queries (require JWT)
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/queries | List saved queries |
| POST | /api/queries | Create a saved query |
| GET | /api/queries/{id} | Get a specific query |
| DELETE | /api/queries/{id} | Delete a query |
| POST | /api/queries/{id}/execute | Execute and cache results |
| GET | /api/queries/{id}/results | List cached results |

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Liveness probe |

All list responses use named envelopes (e.g. `{"datasets": [...]}`) -- never bare arrays.

## Environment Variables

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Uvicorn listen port |
| `HOST` | `0.0.0.0` | Uvicorn listen host |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated allowed origins |
| `MAX_UPLOAD_MB` | `50` | Maximum file upload size in MB |
| `SUPABASE_URL` | _(empty = in-memory mode)_ | Supabase API URL |
| `SUPABASE_ANON_KEY` | | Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | | Supabase service role key |
| `SUPABASE_JWT_SECRET` | | JWT secret for token validation |

## Rules

- Pydantic models for all request/response bodies (see `app/models.py`)
- Async handlers (`async def`) for all endpoints
- Type hints on all function signatures
- Response envelopes: return `{"key": [...]}` -- never bare arrays
- Parameterized queries -- never string interpolation for SQL
- RLS policies on all tables -- users can only access their own data
- JWT authentication via Supabase Auth -- validated in `app/auth.py`
- OpenAPI docs auto-generated at `/docs`

## Testing Notes

- `conftest.py` mounts only the API routers into a standalone `FastAPI()` app -- **never** use `TestClient(app.main.app)` directly (the `StaticFiles` mount at `/` causes lifespan hangs in CI)
- Tests run in in-memory mode (no `SUPABASE_URL` set) -- no database required
- `seeded_client` fixture pre-uploads `sample.csv` with columns `name, age, score`
- Tests are self-contained -- `DataService` state is reset between tests via autouse fixture
- `data_service.list_dataset_names()` for in-memory name lists; `data_service.list_datasets(owner_id=...)` for DB-backed metadata
- NEVER name helper classes with `Test` prefix -- conflicts with pytest collection

## Seed Data

The seed creates a demo user and realistic sample data:
- **Demo credentials**: `demo@data-explorer.local` / `demo-password-123`
- **3 datasets**: E-commerce sales (48 rows), Weather stations (450 rows), Employee survey (215 rows)
- **8 saved queries**: Revenue analysis, temperature averages, satisfaction scores, etc.
- **5 result snapshots**: Pre-cached query results for instant display

## Common Gotchas

1. Missing `SUPABASE_URL` silently falls back to in-memory mode -- no error, but no persistence
2. `npx supabase db reset` is required after changing migrations (applies migrations + seed)
3. Auth endpoints return 401 for invalid credentials, not 400
4. The `profiles` table is auto-populated by a trigger -- don't insert manually on signup
5. Upload/list/preview work without auth tokens (anonymous mode); queries require auth
6. The visualize and upload routers share the same `DataService` instance via `app.services`
7. `StaticFiles` mount at `/` must be last -- it catches all unmatched routes
