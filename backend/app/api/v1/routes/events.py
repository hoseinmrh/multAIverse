from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import CoreServiceDependency
from app.schemas.api import AdvancementResponse, EventDetailResponse

router = APIRouter(prefix="/events", tags=["events and choices"])


@router.get("/{event_id}", response_model=EventDetailResponse)
def get_event(event_id: UUID, service: CoreServiceDependency) -> EventDetailResponse:
    return service.get_event(event_id)


@router.post(
    "/{event_id}/choices/{choice_id}/select",
    response_model=AdvancementResponse,
)
async def select_choice(
    event_id: UUID, choice_id: UUID, service: CoreServiceDependency
) -> AdvancementResponse:
    return await service.select_choice(event_id, choice_id)
