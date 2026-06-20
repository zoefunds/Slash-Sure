from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.api.v1.routes import auth, operators, incidents, slashing, insurance, monitoring, risk
from app.api.v1.ws.events import router as ws_router
from app.db.base import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting SlashSure API v{settings.VERSION}")
    # Create DB tables on startup (production: use Alembic migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified")
    yield
    logger.info("Shutting down SlashSure API")
    from app.services.genlayer.client import genlayer_client
    await genlayer_client.close()


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="SlashSure API",
    description="AI-powered slashing monitoring and insurance layer for decentralized networks",
    version=settings.VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.VERSION, "env": settings.APP_ENV}


@app.get("/api/v1/contract/stats")
async def contract_stats():
    from app.services.genlayer.client import genlayer_client
    stats = await genlayer_client.get_contract_stats()
    return {"stats": stats}


# Register routers
prefix = "/api/v1"
app.include_router(auth.router, prefix=prefix)
app.include_router(operators.router, prefix=prefix)
app.include_router(incidents.router, prefix=prefix)
app.include_router(slashing.router, prefix=prefix)
app.include_router(insurance.router, prefix=prefix)
app.include_router(monitoring.router, prefix=prefix)
app.include_router(risk.router, prefix=prefix)
app.include_router(ws_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
