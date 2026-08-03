from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.dependencies import CoreServiceDependency
from app.schemas.api import (
    Page,
    ScenarioComparisonResponse,
    ScenarioDetailResponse,
    UniverseGenerationResponse,
)
from app.schemas.domain import ScenarioCreate, ScenarioRead

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


@router.post("", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
def create_scenario(payload: ScenarioCreate, service: CoreServiceDependency) -> ScenarioRead:
    return service.create_scenario(payload)


@router.get("", response_model=Page[ScenarioRead])
def list_scenarios(
    service: CoreServiceDependency,
    offset: Offset = 0,
    limit: Limit = 20,
    profile_id: UUID | None = None,
) -> Page[ScenarioRead]:
    result = service.list_scenarios(offset, limit, profile_id)
    return Page(items=result.items, pagination=result.pagination)


@router.get("/{scenario_id}", response_model=ScenarioDetailResponse)
def get_scenario(scenario_id: UUID, service: CoreServiceDependency) -> ScenarioDetailResponse:
    return service.get_scenario(scenario_id)


@router.post(
    "/{scenario_id}/generate-universes",
    response_model=UniverseGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_universes(
    scenario_id: UUID, service: CoreServiceDependency
) -> UniverseGenerationResponse:
    return await service.generate_universes(scenario_id)


@router.get("/{scenario_id}/comparison", response_model=ScenarioComparisonResponse)
def compare_universes(
    scenario_id: UUID, service: CoreServiceDependency
) -> ScenarioComparisonResponse:
    return service.compare_universes(scenario_id)
