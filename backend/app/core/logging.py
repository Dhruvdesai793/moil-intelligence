import logging
from time import perf_counter

from starlette.requests import Request


logger = logging.getLogger("moil.requests")


def configure_logging(level: str) -> None:
    logging.basicConfig(level=level.upper(), format="%(asctime)s %(levelname)s %(message)s")


async def log_request(request: Request, call_next):
    started = perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        logger.info("method=%s path=%s status=%s duration_ms=%.2f",
                    request.method, request.url.path, status,
                    (perf_counter() - started) * 1000)
