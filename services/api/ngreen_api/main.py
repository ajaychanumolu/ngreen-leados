"""FastAPI application."""

from __future__ import annotations

import logging
import re
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ngreen_api.db import get_session_factory, prepare_database
from ngreen_api.deps import ApiError
from ngreen_api.redact import scrub
from ngreen_api.routers import (
    accounts,
    auth,
    calls,
    catalog,
    contacts,
    health,
    imports,
    me,
    opportunities,
    overview,
    privacy,
    reports,
    research,
    tasks,
)
from ngreen_api.seed import seed_demo
from ngreen_api.settings import get_settings

_REQUEST_ID = re.compile(r"[A-Za-z0-9-]{8,64}")
_access = logging.getLogger("ngreen.access")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    prepare_database()
    db = get_session_factory()()
    try:
        if get_settings().demo_auth_enabled:
            seed_demo(db)
    finally:
        db.close()
    yield


app = FastAPI(title="N Green LeadOS", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(me.router)
app.include_router(overview.router)
app.include_router(accounts.router)
app.include_router(catalog.router)
app.include_router(contacts.router)
app.include_router(imports.router)
app.include_router(opportunities.router)
app.include_router(tasks.router)
app.include_router(reports.router)
app.include_router(privacy.router)
app.include_router(research.router)
app.include_router(calls.router)


@app.middleware("http")
async def request_id(request: Request, call_next):
    incoming = request.headers.get("x-request-id", "")
    current = incoming if _REQUEST_ID.fullmatch(incoming) else uuid.uuid4().hex
    response = await call_next(request)
    response.headers["X-Request-ID"] = current
    _access.info("%s %s %s", request.method, scrub(request.url.path), response.status_code)
    return response


@app.exception_handler(ApiError)
def api_error(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message},
    )


@app.exception_handler(RequestValidationError)
def validation_error(_request: Request, _exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"code": "validation_error", "message": "The request body is not valid."},
    )
