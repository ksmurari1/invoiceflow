"""FastAPI application factory and ASGI entry point (`uvicorn app.main:app`)."""

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.errors import register_error_handlers
from app.logging_config import configure_logging
from app.routers import clients, dashboard, health, invoices, me

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    """
    Build the FastAPI application with middleware, error handlers and routers.

    Returns:
        Configured FastAPI application.
    """
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)
    if settings.ENV == "production":
        # The MVP has no login: every request acts as the demo user. Never run it publicly.
        raise RuntimeError("Demo-user mode is for local use only; refusing to start in production.")

    app = FastAPI(title="InvoiceFlow API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["Content-Disposition"],
    )

    register_error_handlers(app)

    app.include_router(health.router)

    api_router = APIRouter(prefix=API_PREFIX)
    api_router.include_router(me.router)
    api_router.include_router(clients.router)
    api_router.include_router(invoices.router)
    api_router.include_router(dashboard.router)
    app.include_router(api_router)

    return app


app = create_app()
