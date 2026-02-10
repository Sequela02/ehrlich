from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ehrlich.api.routes.health import router as health_router
from ehrlich.api.routes.investigation import router as investigation_router
from ehrlich.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Ehrlich",
        description="AI-powered antimicrobial discovery agent",
        version="0.1.0",
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

    return app
