from fastapi import APIRouter

from app.api.routes import decision, exploration, features, health, jobs, predictions, production
from app.schemas.common import ErrorResponse

api_router = APIRouter(prefix="/api/v1", responses={
    404: {"model": ErrorResponse}, 422: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
})
for module in (health, exploration, features, predictions, production, decision, jobs):
    api_router.include_router(module.router)
