"""
GENESIS AI Platform — FastAPI Application Entry Point
"""
import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import get_settings
from app.database import create_tables, close_db
from app.dependencies import startup, shutdown
from app.routers import (
    agents_router, tasks_router, evolution_router,
    memory_router, skills_router, system_router, a2a_router,
)

log = structlog.get_logger(__name__)
settings = get_settings()

# ── Configure structured logging ──────────────────────────────
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer() if settings.app_env == "development"
        else structlog.processors.JSONRenderer(),
    ]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    log.info("genesis.starting", version="2.0.0", env=settings.app_env)
    await create_tables()
    await startup()
    yield
    await shutdown()
    await close_db()
    log.info("genesis.stopped")


# ── FastAPI App ───────────────────────────────────────────────
app = FastAPI(
    title="GENESIS AI Platform",
    description=(
        "Genetic Evolution Network with Episodic & Semantic Intelligence System. "
        "Multi-agent platform with LLM-powered genetic evolution, 4-tier memory, "
        "and autonomous skill building."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ─────────────────────────────────
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = int((time.time() - start) * 1000)
    response.headers["X-Response-Time-Ms"] = str(duration)
    return response


# ── Global exception handler ──────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


# ── Register routers ──────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(agents_router,   prefix=PREFIX)
app.include_router(tasks_router,    prefix=PREFIX)
app.include_router(evolution_router, prefix=PREFIX)
app.include_router(memory_router,   prefix=PREFIX)
app.include_router(skills_router,   prefix=PREFIX)
app.include_router(system_router,   prefix=PREFIX)
app.include_router(a2a_router,      prefix=PREFIX)


# ── Root ──────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name": "GENESIS AI Platform",
        "version": "2.0.0",
        "status": "operational",
        "docs": "/docs",
        "api": "/api/v1",
        "endpoints": {
            "agents":    f"{PREFIX}/agents",
            "tasks":     f"{PREFIX}/tasks",
            "evolution": f"{PREFIX}/evolution",
            "memory":    f"{PREFIX}/memory",
            "skills":    f"{PREFIX}/skills",
            "health":    f"{PREFIX}/system/health",
            "stats":     f"{PREFIX}/system/stats",
            "a2a":       f"{PREFIX}/a2a/agent.json",
        },
    }


@app.get("/api/v1")
async def api_root():
    return {"version": "v1", "status": "operational"}
