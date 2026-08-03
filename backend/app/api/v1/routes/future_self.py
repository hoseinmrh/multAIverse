from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import CoreServiceDependency
from app.schemas.api import (
    FutureSelfConversationResponse,
    FutureSelfMessageRequest,
)

router = APIRouter(prefix="/future-self/conversations", tags=["future self"])

Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


@router.get("/{conversation_id}", response_model=FutureSelfConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    service: CoreServiceDependency,
    offset: Offset = 0,
    limit: Limit = 50,
) -> FutureSelfConversationResponse:
    return await service.get_conversation(conversation_id, offset, limit)


@router.post("/{conversation_id}/messages", response_model=FutureSelfConversationResponse)
async def send_message(
    conversation_id: UUID,
    payload: FutureSelfMessageRequest,
    service: CoreServiceDependency,
    offset: Offset = 0,
    limit: Limit = 50,
) -> FutureSelfConversationResponse:
    return await service.send_future_self_message(conversation_id, payload.content, offset, limit)
