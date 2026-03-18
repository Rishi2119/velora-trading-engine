"""
Velora Backend — FastAPI Application Entry Point
Unified backend connecting all services.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from backend.config.settings import settings
from backend.database.database import init_db
from backend.utils.logger import logger

# ── API Routers ───────────────────────────────────────────────────────────────
from backend.api.auth import router as auth_router
from backend.api.trading import router as trading_router
from backend.api.analytics import router as analytics_router
from backend.api.ai import router as ai_router
from backend.api.market import router as market_router
from backend.api.ws_feed import ws_feed_handler
from backend.api.engine import router as engine_router
from backend.api.strategy import router as strategy_router

# ── Rate Limiter ──────────────────────────────────────────────────────────────
from backend.utils.limiter import limiter


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    logger.info("Database initialized")

    # Auto connect MT5 if configured
    if settings.MT5_ACCOUNT and settings.MT5_PASSWORD and settings.MT5_SERVER:
        try:
            from backend.utils.mt5_manager import mt5_manager
            logger.info(f"Auto-connecting to MT5 Account {settings.MT5_ACCOUNT}")
            res = mt5_manager.connect(settings.MT5_ACCOUNT, settings.MT5_PASSWORD, settings.MT5_SERVER)
            if res.get("connected"):
                logger.info("MT5 Connected Successfully")
            else:
                logger.error(f"MT5 Connection Failed: {res.get('error')}")
        except Exception as e:
            logger.error(f"MT5 Auto-connect error: {e}")

    yield
    logger.info("Shutting down Velora backend")
    try:
        from backend.utils.mt5_manager import mt5_manager
        if mt5_manager.connected:
            mt5_manager.disconnect()
    except Exception:
        pass


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Velora Trading Platform API — "
        "AI-powered forex/crypto trading engine with MT5 integration."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

# CORS — restrict to configured origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router,     prefix="/api/v1")
app.include_router(trading_router,  prefix="/api/v1")
app.include_router(analytics_router,prefix="/api/v1")
app.include_router(ai_router,       prefix="/api/v1")
app.include_router(market_router,   prefix="/api/v1")
app.include_router(engine_router,   prefix="/api/v1")
app.include_router(strategy_router, prefix="/api/v1")


# ── WebSocket Feed ────────────────────────────────────────────────────────────
@app.websocket("/ws/feed")
async def websocket_feed(websocket: WebSocket):
    """Real-time engine event feed."""
    await ws_feed_handler(websocket)


# ── Root + Health ─────────────────────────────────────────────────────────────
@app.get("/", tags=["System"])
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
