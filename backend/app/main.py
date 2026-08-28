from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.agent import router as agent_router
from app.api.routes.health import router as health_router
from app.core.config import get_settings
from app.core.database import dispose_engine
from app.schemas.health import HealthResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await dispose_engine()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(health_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")


@app.get("/", response_model=HealthResponse, include_in_schema=False)
async def root() -> HealthResponse:
    return HealthResponse()


@app.get("/health", response_model=HealthResponse, tags=["health"])
async def health_alias() -> HealthResponse:
    """Conventional unversioned health endpoint for platforms and the Day 1 demo."""
    return HealthResponse()
