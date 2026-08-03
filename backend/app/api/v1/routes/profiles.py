from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.dependencies import CoreServiceDependency
from app.schemas.api import DeleteResponse, Page
from app.schemas.domain import PersonProfileCreate, PersonProfileRead, PersonProfileUpdate

router = APIRouter(prefix="/profiles", tags=["profiles"])

Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


@router.post("", response_model=PersonProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: PersonProfileCreate, service: CoreServiceDependency
) -> PersonProfileRead:
    return service.create_profile(payload)


@router.get("", response_model=Page[PersonProfileRead])
def list_profiles(
    service: CoreServiceDependency, offset: Offset = 0, limit: Limit = 20
) -> Page[PersonProfileRead]:
    result = service.list_profiles(offset, limit)
    return Page(items=result.items, pagination=result.pagination)


@router.get("/{profile_id}", response_model=PersonProfileRead)
def get_profile(profile_id: UUID, service: CoreServiceDependency) -> PersonProfileRead:
    return service.get_profile(profile_id)


@router.patch("/{profile_id}", response_model=PersonProfileRead)
def update_profile(
    profile_id: UUID,
    payload: PersonProfileUpdate,
    service: CoreServiceDependency,
) -> PersonProfileRead:
    return service.update_profile(profile_id, payload)


@router.delete("/{profile_id}", response_model=DeleteResponse)
def delete_profile(profile_id: UUID, service: CoreServiceDependency) -> DeleteResponse:
    service.delete_profile(profile_id)
    return DeleteResponse(deleted=True, id=profile_id)
