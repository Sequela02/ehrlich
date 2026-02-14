import importlib
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ehrlich.api.routes.health import router as health_router
from ehrlich.api.routes.investigation import close_repository, init_repository
from ehrlich.api.routes.investigation import router as investigation_router
from ehrlich.api.routes.methodology import router as methodology_router
from ehrlich.api.routes.molecule import router as molecule_router
from ehrlich.api.routes.stats import router as stats_router
from ehrlich.api.routes.upload import router as upload_router
from ehrlich.config import get_settings
from ehrlich.investigation.application.registry_factory import build_tool_registry

logger = logging.getLogger(__name__)

_OPTIONAL_DEPS = {
    "chemprop": "Chemprop D-MPNN (deep learning)",
}


def _check_optional(module: str) -> bool:
    try:
        importlib.import_module(module)
        return True
    except ImportError:
        return False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    if not settings.has_api_key:
        logger.warning(
            "No Anthropic API key configured. "
            "Set EHRLICH_ANTHROPIC_API_KEY or ANTHROPIC_API_KEY to run investigations."
        )
    else:
        logger.info(
            "Anthropic API key configured (director=%s, researcher=%s)",
            settings.director_model,
            settings.researcher_model,
        )

    registry = build_tool_registry()
    logger.info("Tool registry: %d tools available", len(registry.list_tools()))

    for mod, desc in _OPTIONAL_DEPS.items():
        status = "available" if _check_optional(mod) else "not installed"
        logger.info("  %s: %s", desc, status)

    await init_repository(settings.database_url)
    logger.info("PostgreSQL repository initialized")

    yield

    await close_repository()
    logger.info("PostgreSQL connection pool closed")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Ehrlich",
        description="AI-powered scientific discovery engine",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(investigation_router, prefix="/api/v1")
    app.include_router(methodology_router, prefix="/api/v1")
    app.include_router(molecule_router, prefix="/api/v1")
    app.include_router(stats_router, prefix="/api/v1")
    app.include_router(upload_router, prefix="/api/v1")

    return app
