from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import CoreServiceDependency
from app.schemas.domain import ArtifactRead

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/{artifact_id}", response_model=ArtifactRead)
def get_artifact(artifact_id: UUID, service: CoreServiceDependency) -> ArtifactRead:
    return service.get_artifact(artifact_id)
