import logging
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, get_settings
from app.db import Base, engine, ensure_database_exists
from app import orm_models  # noqa: F401
from app.routers import auth, chat, documents, qa

FRONTEND_DIST_DIR = BASE_DIR / "frontend" / "dist"
FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"
logger = logging.getLogger(__name__)

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Knowledge base question answering service powered by FastAPI, Vue 3 and LangChain.",
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(qa.router)
app.include_router(auth.router)
app.include_router(chat.router)

if FRONTEND_ASSETS_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS_DIR), name="assets")


@app.on_event("startup")
def on_startup() -> None:
    try:
        ensure_database_exists()
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Database startup skipped: %s. Check MYSQL_URL, MySQL connectivity, and account permissions.",
            exc,
        )


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@app.get("/", tags=["system"], include_in_schema=False, response_model=None)
async def root() -> Response:
    index_file = FRONTEND_DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        {
            "message": f"{settings.app_name} is running.",
            "docs": "/docs",
            "frontend": "Build the Vue app with `npm install && npm run build` inside the `frontend` directory.",
        }
    )


@app.get("/{full_path:path}", include_in_schema=False, response_model=None)
async def spa_fallback(full_path: str) -> Response:
    if full_path.startswith(("documents", "qa", "docs", "openapi.json", "redoc", "assets", "health")):
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    index_file = FRONTEND_DIST_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse({"detail": "Frontend build not found."}, status_code=404)
