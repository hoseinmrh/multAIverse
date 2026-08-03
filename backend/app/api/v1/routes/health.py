from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.core.config import get_settings
from app.models.enums import SimulationMode
from app.schemas.api import PublicConfigResponse
from app.services.narrative import get_narrative_provider_status

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
    provider_status = get_narrative_provider_status(
        settings.narrative_provider,
        has_api_key=settings.has_openai_api_key,
        model=settings.openai_model,
        fallback_to_mock=settings.openai_fallback_to_mock,
    )
    return PublicConfigResponse(
        app_name=settings.app_name,
        app_version=settings.app_version,
        narrative_provider=settings.narrative_provider,
        narrative_provider_status={
            "active_provider": provider_status.active_provider,
            "state": provider_status.state,
            "model": provider_status.model,
            "fallback_enabled": provider_status.fallback_enabled,
            "detail": provider_status.detail,
        },
        simulation_modes=list(SimulationMode),
        max_universe_branches=3,
        fictional_simulation_disclaimer=(
            "Multiverse creates fictional scenarios for entertainment and reflection. "
            "Its simulations are not predictions or professional advice."
        ),
    )
