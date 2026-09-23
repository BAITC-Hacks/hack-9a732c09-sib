"""Run from repository root: python -m uvicorn backend.app.main:app."""

import logging
import os
from contextlib import asynccontextmanager
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from .schemas import CaseSummary, Error, ErrorResponse, Health, RunAccepted, RunRequest, RunSnapshot
from .service import RunService
from .summary import build_summary

logger = logging.getLogger(__name__)


def cors_origins():
    raw = os.environ.get("BACKEND_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    origins = [part.strip() for part in raw.split(",") if part.strip()]
    for origin in origins:
        parsed = urlsplit(origin)
        if (parsed.scheme not in ("http", "https") or parsed.hostname not in ("localhost", "127.0.0.1", "::1")
                or parsed.username is not None or parsed.password is not None or parsed.path
                or parsed.query or parsed.fragment):
            raise ValueError("BACKEND_CORS_ORIGINS must contain local development origins without paths")
        _ = parsed.port  # Reject malformed ports at startup.
    return origins


def error_response(status, code, message, details=None):
    body = ErrorResponse(error=Error(code=code, message=message, details=details or []))
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))


def create_app(service=None, summary_provider=build_summary):
    runs = service if service is not None else RunService()

    @asynccontextmanager
    async def lifespan(app):
        yield
        await run_in_threadpool(runs.close)

    app = FastAPI(title="False Positive Demo API", version="1.0.0", lifespan=lifespan)
    app.state.runs = runs

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Include only field locations and error types, never submitted values.
        details = [f"{'.'.join(map(str, e['loc']))}: {e['type']}" for e in exc.errors()]
        return error_response(422, "VALIDATION_ERROR", "Request validation failed.", details)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        code = "RUN_NOT_FOUND" if exc.status_code == 404 and request.url.path.startswith("/api/v1/runs/") else "HTTP_ERROR"
        return error_response(exc.status_code, code, "Run was not found." if code == "RUN_NOT_FOUND" else "Request failed.")

    @app.middleware("http")
    async def service_errors(request: Request, call_next):
        # Inside outer CORS middleware, so even normalized 500s are readable by the UI.
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error("API request failed (%s)", type(exc).__name__)
            return error_response(500, "INTERNAL_ERROR", "Internal service error.")

    # Last added middleware is outermost, including normalized 500 responses.
    app.add_middleware(CORSMiddleware, allow_origins=cors_origins(), allow_credentials=False,
                       allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
    errors = {500: {"model": ErrorResponse}}

    @app.get("/api/v1/health", response_model=Health, operation_id="getHealth", responses=errors)
    async def health():
        return Health()

    @app.get("/api/v1/case/summary", response_model=CaseSummary, operation_id="getCaseSummary", responses=errors)
    def summary():
        return summary_provider()

    @app.post("/api/v1/runs", response_model=RunAccepted, status_code=202, operation_id="createRun",
              responses={**errors, 422: {"model": ErrorResponse}})
    def create_run(body: RunRequest):
        return runs.create(body)

    @app.get("/api/v1/runs/{run_id}", response_model=RunSnapshot, operation_id="getRun",
             responses={**errors, 404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}})
    def get_run(run_id: UUID):
        result = runs.get(run_id)
        if result is None:
            raise HTTPException(status_code=404)
        return result

    return app


app = create_app()
