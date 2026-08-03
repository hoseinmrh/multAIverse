from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.core.config import get_settings
from app.models.enums import SimulationMode
from app.schemas.api import PublicConfigResponse

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name, version=settings.app_version)


@router.get("/config/public", response_model=PublicConfigResponse)
def public_config() -> PublicConfigResponse:
    settings = get_settings()
    return PublicConfigResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        narrative_provider=settings.narrative_provider,
        simulation_modes=list(SimulationMode),
        max_universe_branches=3,
        fictional_simulation_disclaimer=(
            "Multiverse creates fictional scenarios for entertainment and reflection. "
            "Its simulations are not predictions or professional advice."
        ),
    )
