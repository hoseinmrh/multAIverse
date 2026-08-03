from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import CoreServiceDependency
from app.schemas.api import (
    AdvancementResponse,
    ConversationCreateRequest,
    FutureSelfConversationResponse,
    Page,
    UniverseResetResponse,
    UniverseStateResponse,
)
from app.schemas.domain import (
    ArtifactRead,
    EventRead,
    LifeStateSnapshotRead,
    UniverseRead,
)

router = APIRouter(prefix="/universes", tags=["universes"])

Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


@router.get("/{universe_id}", response_model=UniverseRead)
def get_universe(universe_id: UUID, service: CoreServiceDependency) -> UniverseRead:
    return service.get_universe(universe_id)


@router.get("/{universe_id}/timeline", response_model=Page[LifeStateSnapshotRead])
def get_timeline(
    universe_id: UUID,
    service: CoreServiceDependency,
    offset: Offset = 0,
    limit: Limit = 20,
) -> Page[LifeStateSnapshotRead]:
    result = service.get_timeline(universe_id, offset, limit)
    return Page(items=result.items, pagination=result.pagination)


@router.get("/{universe_id}/state", response_model=UniverseStateResponse)
def get_state(universe_id: UUID, service: CoreServiceDependency) -> UniverseStateResponse:
    return service.get_universe_state(universe_id)


@router.post("/{universe_id}/advance", response_model=AdvancementResponse)
async def advance_universe(
    universe_id: UUID, service: CoreServiceDependency
) -> AdvancementResponse:
    return await service.advance_universe(universe_id)


@router.post("/{universe_id}/reset", response_model=UniverseResetResponse)
def reset_universe(universe_id: UUID, service: CoreServiceDependency) -> UniverseResetResponse:
    return service.reset_universe(universe_id)


@router.get("/{universe_id}/events", response_model=Page[EventRead])
def get_events(
    universe_id: UUID,
    service: CoreServiceDependency,
    offset: Offset = 0,
    limit: Limit = 20,
) -> Page[EventRead]:
    result = service.get_events(universe_id, offset, limit)
    return Page(items=result.items, pagination=result.pagination)


@router.get("/{universe_id}/artifacts", response_model=Page[ArtifactRead])
def get_artifacts(
    universe_id: UUID,
    service: CoreServiceDependency,
    offset: Offset = 0,
    limit: Limit = 20,
) -> Page[ArtifactRead]:
    result = service.get_artifacts(universe_id, offset, limit)
    return Page(items=result.items, pagination=result.pagination)


@router.post(
    "/{universe_id}/future-self/conversations",
    response_model=FutureSelfConversationResponse,
)
async def create_future_self_conversation(
    universe_id: UUID,
    payload: ConversationCreateRequest,
    service: CoreServiceDependency,
    offset: Offset = 0,
    limit: Limit = 50,
) -> FutureSelfConversationResponse:
    return await service.create_conversation(universe_id, payload.title, offset, limit)
