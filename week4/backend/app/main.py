import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .db import engine
from .models import Base
from .routers import action_items as action_items_router
from .routers import auth as auth_router
from .routers import notes as notes_router

app = FastAPI(title="Modern Software Dev Starter (Week 4)")

# Ensure data dir exists
Path("data").mkdir(parents=True, exist_ok=True)

# Mount static frontend only if not in test mode and directory exists
ENABLE_STATIC_FILES = os.getenv("ENABLE_STATIC_FILES", "true").lower() == "true"
FRONTEND_DIR = Path("frontend")

if ENABLE_STATIC_FILES and FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.on_event("startup")
def startup_event() -> None:
    # Drop all tables and recreate (fresh start for auth migration)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    """Serve the frontend index.html if available, otherwise return API info."""
    index_path = FRONTEND_DIR / "index.html"
    if ENABLE_STATIC_FILES and index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(
        content={
            "message": "Modern Software Dev API",
            "version": "Week 4",
            "docs": "/docs",
            "status": "ok",
        }
    )


# Routers
app.include_router(auth_router.router)
app.include_router(notes_router.router)
app.include_router(action_items_router.router)
