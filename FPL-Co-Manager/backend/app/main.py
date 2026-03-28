"""
FPL AI Co-Manager — FastAPI application.

Deterministic optimizer; Kimi explanations via GMI only; HydraDB read/write;
Dify workflow POST after each analyze (orchestration).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.session import init_db
from app.providers.ai_credentials import is_live_key
from app.providers.gmi_model_validation import validate_gmi_kimi_models
from app.routes import analyze, compare_route, health, import_team, memory_routes, parse_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    if is_live_key(settings.dify_api_key):
        logger.info("Dify: DIFY_API_KEY is set (workflow will be called on /api/analyze)")
    else:
        logger.warning("Dify: DIFY_API_KEY missing or placeholder — check backend/.env")
    for msg in await validate_gmi_kimi_models(settings):
        if "not set" in msg.lower() or "skipping" in msg.lower():
            logger.info("[startup] %s", msg)
        else:
            logger.warning("[startup] %s", msg)
    yield


settings = get_settings()
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app = FastAPI(
    title="FPL AI Co-Manager",
    description="Import FPL squads, optimize lineup, transfers, and persist recommendations.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(import_team.router)
app.include_router(analyze.router)
app.include_router(parse_image.router)
app.include_router(memory_routes.router)
app.include_router(compare_route.router)


@app.get("/api/demo-hints")
def demo_hints() -> dict:
    """Hackathon demo: suggest trying a public entry ID (may vary by season)."""
    return {
        "sample_team_id": 919028,
        "note": "Replace with any visible FPL league entry ID. If import fails, use manual squad entry.",
    }
