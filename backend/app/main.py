from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import (
    NotFoundError, http_handler, not_found_handler, unexpected_handler, validation_handler,
    database_handler,
)
from app.core.logging import configure_logging, log_request

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_exception_handler(NotFoundError, not_found_handler)
app.add_exception_handler(RequestValidationError, validation_handler)
app.add_exception_handler(HTTPException, http_handler)
app.add_exception_handler(Exception, unexpected_handler)
app.add_exception_handler(SQLAlchemyError, database_handler)
app.middleware("http")(log_request)
app.include_router(api_router)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
