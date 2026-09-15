import logging

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.schemas.common import ErrorDetail, ErrorResponse


class NotFoundError(Exception):
    pass


async def database_handler(request, exc):
    logging.getLogger("moil.errors").warning("Database request failed (%s)", type(exc).__name__)
    return error_response(503, "database_unavailable",
                          "Database unavailable or schema missing. Check DATABASE_URL and run alembic upgrade head.")


def error_response(status: int, code: str, message: str) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status, content=body.model_dump(mode="json"))


async def not_found_handler(request, exc):
    return error_response(404, "not_found", str(exc))


async def validation_handler(request, exc: RequestValidationError):
    return error_response(422, "validation_error", str(exc))


async def http_handler(request, exc: HTTPException):
    return error_response(exc.status_code, "http_error", str(exc.detail))


async def unexpected_handler(request, exc):
    logging.getLogger("moil.errors").error("Unhandled request error", exc_info=exc)
    return error_response(500, "internal_error", "An unexpected server error occurred.")
