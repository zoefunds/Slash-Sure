import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import settings
from app.api.v1.routes import auth, operators, incidents, slashing, insurance, monitoring, risk, admin
from app.api.v1.routes.genlayer import router as genlayer_router
from app.api.v1.ws.events import router as ws_router
from app.db.base import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SlashSure API v%s", settings.VERSION)

    # DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified")

    # Redis
    from app.core.redis import get_redis
    await get_redis()

    # Monitoring worker
    from app.workers.monitoring_worker import run_monitoring_worker
    worker_task = asyncio.create_task(run_monitoring_worker())
    logger.info("Monitoring worker started")

    yield

    # Shutdown
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

    # genlayer_client uses synchronous SDK — no async close needed

    from app.core.redis import close_redis
    await close_redis()

    logger.info("SlashSure API shut down cleanly")


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="SlashSure API",
    description="AI-powered slashing monitoring and insurance layer for decentralised networks",
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
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    logger.debug("%s %s", request.method, request.url.path)
    response = await call_next(request)
    return response


@app.get("/health")
async def health():
    from app.core.redis import get_redis
    redis_ok = False
    try:
        r = await get_redis()
        await r.ping()
        redis_ok = True
    except Exception:
        pass
    return {
        "status": "ok",
        "version": settings.VERSION,
        "env": settings.APP_ENV,
        "redis": redis_ok,
        "contract": settings.GENLAYER_CONTRACT_ADDRESS,
    }


# Register routers
prefix = "/api/v1"
app.include_router(auth.router,        prefix=prefix)
app.include_router(operators.router,   prefix=prefix)
app.include_router(incidents.router,   prefix=prefix)
app.include_router(slashing.router,    prefix=prefix)
app.include_router(insurance.router,   prefix=prefix)
app.include_router(monitoring.router,  prefix=prefix)
app.include_router(risk.router,        prefix=prefix)
app.include_router(genlayer_router,    prefix=prefix)
app.include_router(admin.router,       prefix=prefix)
app.include_router(ws_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
