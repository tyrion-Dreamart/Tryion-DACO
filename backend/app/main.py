from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.db.base import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: None)
    yield
    await engine.dispose()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="ERP financiero-operativo para empresas de servicios e ingeniería.",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.is_production:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts_list)

    app.include_router(api_router)

    @app.get("/health", tags=["System"])
    async def health():
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_application()