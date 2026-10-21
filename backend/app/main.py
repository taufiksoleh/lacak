from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import entities, investigations, system
from app.config import get_settings
from app.db import SessionLocal, init_db
from app.services.collector import seed_entities

STATIC_DIR = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    with SessionLocal() as db:
        seed_entities(db)
    yield


app = FastAPI(title="Lacak API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(investigations.router)
app.include_router(entities.router)
app.include_router(system.router)


@app.get("/api/health")
def health():
    return {"ok": True}


# Sajikan build frontend (produksi / Docker) bila tersedia
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        file = (STATIC_DIR / path).resolve()
        if path and file.is_file() and STATIC_DIR in file.parents:
            return FileResponse(file)
        return FileResponse(STATIC_DIR / "index.html")
