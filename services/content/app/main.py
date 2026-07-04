from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import ops_router, router as content_router
from app.core.config import settings

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("service_starting", service=settings.app_name, version=settings.app_version)

    if settings.environment in ("local", "test") or settings.debug:
        from app.core.db import Base, engine

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("db_tables_created", env=settings.environment)

    yield
    logger.info("service_stopping", service=settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[settings.request_id_header, settings.trace_id_header],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    import uuid

    request_id = request.headers.get(
        settings.request_id_header, f"req_{uuid.uuid4().hex[:12]}"
    )
    trace_id = request.headers.get(settings.trace_id_header)

    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        content = detail
        if "request_id" not in content:
            content["request_id"] = request_id
    else:
        content = {
            "code": f"HTTP_{exc.status_code}",
            "message": str(detail) if detail else "请求失败",
            "request_id": request_id,
        }

    if trace_id:
        content["trace_id"] = trace_id

    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        code=content.get("code"),
        message=content.get("message"),
    )

    response = JSONResponse(status_code=exc.status_code, content=content)
    response.headers[settings.request_id_header] = request_id
    if trace_id:
        response.headers[settings.trace_id_header] = trace_id
    return response


@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    import uuid

    request_id = request.headers.get(settings.request_id_header, f"req_{uuid.uuid4().hex[:12]}")
    trace_id = request.headers.get(settings.trace_id_header)

    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        trace_id=trace_id,
        method=request.method,
        path=request.url.path,
    )

    logger.info("request_started")

    try:
        response = await call_next(request)
    except Exception as exc:
        logger.exception("request_failed", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "request_id": request_id,
            },
        )

    response.headers[settings.request_id_header] = request_id
    if trace_id:
        response.headers[settings.trace_id_header] = trace_id

    logger.info("request_completed", status_code=response.status_code)
    return response


app.include_router(content_router, prefix=settings.api_v1_prefix)
app.include_router(ops_router, prefix=f"{settings.api_v1_prefix}/ops")

Instrumentator().instrument(app).expose(app)
