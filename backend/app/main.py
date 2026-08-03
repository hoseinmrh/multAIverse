from collections.abc import Mapping

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.schemas.api import ErrorDetail, ErrorResponse
from app.services.application import (
    ApplicationServiceError,
    NarrativeUnavailableError,
    ResourceConflictError,
    ResourceNotFoundError,
)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: Mapping[str, object] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetail.model_validate(
            {"code": code, "message": message, "details": details or {}}
        )
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Local-first API for the Multiverse fictional life simulator.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(ApplicationServiceError)
    async def application_error_handler(_: Request, error: ApplicationServiceError) -> JSONResponse:
        status_code = 400
        if isinstance(error, ResourceNotFoundError):
            status_code = 404
        elif isinstance(error, ResourceConflictError):
            status_code = 409
        elif isinstance(error, NarrativeUnavailableError):
            status_code = 503
        return _error_response(status_code, error.code, error.message, error.details)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, error: RequestValidationError) -> JSONResponse:
        issues = [
            {
                "location": [str(part) for part in issue["loc"]],
                "message": issue["msg"],
                "type": issue["type"],
            }
            for issue in error.errors()
        ]
        return _error_response(
            422,
            "validation_error",
            "Request validation failed",
            {"issues": issues},
        )

    @application.exception_handler(ValidationError)
    async def schema_validation_error_handler(_: Request, error: ValidationError) -> JSONResponse:
        issues = [
            {
                "location": [str(part) for part in issue["loc"]],
                "message": issue["msg"],
                "type": issue["type"],
            }
            for issue in error.errors()
        ]
        return _error_response(
            422,
            "validation_error",
            "Request validation failed",
            {"issues": issues},
        )

    @application.exception_handler(IntegrityError)
    async def integrity_error_handler(_: Request, __: IntegrityError) -> JSONResponse:
        return _error_response(
            409,
            "conflict",
            "The request conflicts with existing persisted data",
        )

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(_: Request, error: StarletteHTTPException) -> JSONResponse:
        message = str(error.detail) if isinstance(error.detail, str) else "HTTP request failed"
        code = "not_found" if error.status_code == 404 else "http_error"
        return _error_response(error.status_code, code, message)

    @application.exception_handler(Exception)
    async def unexpected_error_handler(_: Request, __: Exception) -> JSONResponse:
        return _error_response(
            500,
            "internal_error",
            "An unexpected backend error occurred; existing progress was preserved",
        )

    application.include_router(api_router)
    return application


app = create_app()
