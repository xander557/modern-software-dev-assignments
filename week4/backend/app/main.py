from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import engine
from .models import Base
from .routers import action_items as action_items_router
from .routers import auth as auth_router
from .routers import notes as notes_router

app = FastAPI(title="Modern Software Dev Starter (Week 4)")

# Ensure data dir exists
Path("data").mkdir(parents=True, exist_ok=True)

# Mount static frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.on_event("startup")
def startup_event() -> None:
    # Drop all tables and recreate (fresh start for auth migration)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def root() -> FileResponse:
    return FileResponse("frontend/index.html")


# Routers
app.include_router(auth_router.router)
app.include_router(notes_router.router)
app.include_router(action_items_router.router)
