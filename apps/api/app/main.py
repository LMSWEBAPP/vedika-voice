import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.database import init_db
from app.core.errors import VeyraException, format_error_response
from app.core.logging import logger, request_id_ctx
from app.websocket.agent_test_ws import router as agent_ws_router
from app.websocket.telephony_ws import router as telephony_ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables exist
    logger.info("Initializing Veyra Voice Database...")
    await init_db()
    logger.info(
        f"Veyra Voice API started. AI_PROVIDER={settings.AI_PROVIDER}, TELEPHONY_PROVIDER={settings.TELEPHONY_PROVIDER}"
    )
    yield
    # Shutdown
    logger.info("Veyra Voice API shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Production-Oriented AI Outbound Voice Calling Platform Backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Assigns unique request_id and measures execution latency."""
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_ctx.set(req_id)
    start_time = time.time()

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"
        return response
    finally:
        request_id_ctx.reset(token)


# Standardized Exception Handlers
@app.exception_handler(VeyraException)
async def veyra_exception_handler(request: Request, exc: VeyraException):
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_response(exc),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = request_id_ctx.get()
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "request_id": req_id,
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = request_id_ctx.get()
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected internal server error occurred.",
                "request_id": req_id,
            }
        },
    )


# Include Routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)
app.include_router(agent_ws_router)
app.include_router(telephony_ws_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
