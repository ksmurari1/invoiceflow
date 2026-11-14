"""Application errors and handlers that render every error in one envelope format."""

import logging
from collections.abc import Mapping, Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.common import ErrorBody, ErrorField, ErrorResponse

logger = logging.getLogger(__name__)

_HTTP_ERROR_CODES: dict[int, str] = {
    400: "bad_request",
    401: "not_authenticated",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
}

# The first element of a validation error location says where the value came from.
_LOCATION_ROOTS = {"body", "query", "path", "header", "cookie"}


class AppError(Exception):
    """An expected error with an HTTP status, a stable error code and a user-facing message."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: list[ErrorField] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields or []


def error_response(
    status_code: int,
    code: str,
    message: str,
    fields: list[ErrorField] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """
    Build a JSON error response in the standard envelope.

    Args:
        status_code: HTTP status code.
        code: Stable machine-readable error code.
        message: Human-readable message.
        fields: Optional field-level problems.
        headers: Optional extra response headers.

    Returns:
        JSONResponse with body `{"error": {"code", "message", "fields"}}`.
    """
    body = ErrorResponse(error=ErrorBody(code=code, message=message, fields=fields or []))
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


def format_location(loc: Sequence[str | int]) -> str:
    """
    Turn a validation error location into a field path such as `items[0].quantity`.

    Args:
        loc: Location tuple from a Pydantic/FastAPI validation error.

    Returns:
        Dotted field path with list indexes in brackets.
    """
    parts = list(loc)
    if parts and parts[0] in _LOCATION_ROOTS:
        parts = parts[1:]
    path = ""
    for part in parts:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}" if path else str(part)
    return path


async def app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Render an AppError."""
    assert isinstance(exc, AppError)
    return error_response(exc.status_code, exc.code, exc.message, exc.fields)


async def validation_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Render request validation failures as 422 with field-level details."""
    assert isinstance(exc, RequestValidationError)
    errors: Sequence[dict[str, Any]] = exc.errors()
    fields = [
        ErrorField(field=format_location(err.get("loc", ())), message=str(err.get("msg", "")))
        for err in errors
    ]
    return error_response(422, "validation_error", "Request validation failed.", fields)


async def http_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Render framework HTTP errors (404 for unknown routes, 405, ...) in the standard envelope."""
    assert isinstance(exc, StarletteHTTPException)
    code = _HTTP_ERROR_CODES.get(exc.status_code, "http_error")
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return error_response(exc.status_code, code, message, headers=exc.headers)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log unexpected exceptions and return a generic 500 without internal details."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path, exc_info=exc)
    return error_response(500, "internal_error", "An unexpected error occurred.")


def register_error_handlers(app: FastAPI) -> None:
    """
    Attach all error handlers to the application.

    Args:
        app: FastAPI application instance.
    """
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
