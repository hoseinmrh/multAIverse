from typing import Protocol, runtime_checkable

from app.models.enums import ArtifactType
from app.services.narrative.schemas import (
    FutureSelfReplyRequest,
    GeneratedArtifact,
    GeneratedEvent,
    GeneratedFutureSelfProfile,
    GeneratedFutureSelfReply,
    GeneratedUniverseBranch,
    GeneratedYearSummary,
    NarrativeContext,
    UniverseBranchRequest,
)


@runtime_checkable
class NarrativeProvider(Protocol):
    """Read-only narrative port; implementations receive values and return proposals."""

    provider_name: str
    last_used_provider: str
    llm_only: bool

    async def generate_universe_branches(
        self, request: UniverseBranchRequest
    ) -> tuple[GeneratedUniverseBranch, ...]: ...

    async def generate_significant_event(self, context: NarrativeContext) -> GeneratedEvent: ...

    async def generate_year_summary(
        self, context: NarrativeContext, event: GeneratedEvent
    ) -> GeneratedYearSummary: ...

    async def generate_artifact(
        self,
        context: NarrativeContext,
        event: GeneratedEvent,
        artifact_type: ArtifactType | None = None,
    ) -> GeneratedArtifact: ...

    async def generate_future_self_profile(
        self, context: NarrativeContext
    ) -> GeneratedFutureSelfProfile: ...

    async def generate_future_self_response(
        self, request: FutureSelfReplyRequest
    ) -> GeneratedFutureSelfReply: ...
