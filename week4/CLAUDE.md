# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Minimal full-stack "developer's command center" application for Claude Code automation experiments.

- **Backend:** FastAPI + SQLAlchemy with SQLite
- **Frontend:** Static HTML/CSS/JS served by FastAPI (no build toolchain)
- **Testing:** pytest with TestClient
- **Code quality:** black + ruff via pre-commit

## Development Commands

```bash
make run                             # Start app at http://localhost:8000 (API docs at /docs)
make test                            # Run all tests
make format                          # Auto-format with black + ruff --fix
make lint                            # Check with ruff only
make seed                            # Manually apply data/seed.sql

# Testing variations
pytest backend/tests/test_notes.py   # Run specific test file
pytest -k "test_name"                # Run tests matching pattern
PYTHONPATH=. pytest --maxfail=1 -x   # Stop on first failure
```

## Architecture 

**Entry point:** `backend/app/main.py`
- Mounts static frontend at `/static`, serves `index.html` at root
- Includes routers for `/notes` and `/action-items`
- Runs `apply_seed_if_needed()` on startup to auto-seed from `data/seed.sql`

**Database:** `backend/app/db.py`
- SQLite at `./data/app.db` (configurable via `DATABASE_PATH` env var)
- `get_db()`: FastAPI dependency (yields session, auto-commits/rolls back)
- `get_session()`: Context manager for manual session usage

**Data flow:** Models (`models.py`) → Pydantic schemas (`schemas.py`) → Routers (`routers/*.py`)

**Services:** `backend/app/services/extract.py` - Action item extraction logic

## Key Patterns

**Adding a new endpoint:**
1. Add SQLAlchemy model in `models.py`
2. Add Pydantic schemas in `schemas.py`
3. Create router in `routers/` with `APIRouter(prefix="/...", tags=["..."])`
4. Include router in `main.py` via `app.include_router()`
5. Write tests using the `client` fixture from `conftest.py`

**Database sessions:**
- In routers: `db: Session = Depends(get_db)`
- In services/scripts: `with get_session() as db:`

**Testing:** The `client` fixture provides isolated temp DB per test.

## Environment

Requires conda environment `cs146s`: `conda activate cs146s`
