from fastapi import APIRouter

from app.api.v1.routes.artifacts import router as artifacts_router
from app.api.v1.routes.events import router as events_router
from app.api.v1.routes.future_self import router as future_self_router
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.profiles import router as profiles_router
from app.api.v1.routes.scenarios import router as scenarios_router
from app.api.v1.routes.universes import router as universes_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health_router)
api_router.include_router(profiles_router)
api_router.include_router(scenarios_router)
api_router.include_router(universes_router)
api_router.include_router(events_router)
api_router.include_router(artifacts_router)
api_router.include_router(future_self_router)
