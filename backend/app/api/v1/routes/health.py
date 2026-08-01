from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.core.config import get_settings

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
