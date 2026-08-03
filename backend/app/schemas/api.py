from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue

from app.models.enums import SimulationMode
from app.schemas.domain import (
    ArtifactRead,
    ChoiceRead,
    EventRead,
    FutureSelfConversationRead,
    FutureSelfMessageRead,
    LifeStateSnapshotRead,
    ScenarioRead,
    UniverseRead,
)
from app.services.narrative.schemas import GeneratedFutureSelfProfile, GeneratedYearSummary


class ApiSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ErrorDetail(ApiSchema):
    code: str
    message: str
    details: dict[str, JsonValue] = Field(default_factory=dict)


class ErrorResponse(ApiSchema):
    error: ErrorDetail


class Pagination(ApiSchema):
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    total: int = Field(ge=0)
    has_more: bool


class Page[ItemT](ApiSchema):
    items: list[ItemT]
    pagination: Pagination


class NarrativeProviderStatusResponse(ApiSchema):
    active_provider: Literal["mock", "openai"] | None
    state: Literal["ready", "configured", "fallback", "unavailable"]
    model: str | None
    fallback_enabled: bool
    detail: str


class PublicConfigResponse(ApiSchema):
    app_name: str
    app_version: str
    narrative_provider: Literal["mock", "openai"]
    narrative_provider_status: NarrativeProviderStatusResponse
    simulation_modes: list[SimulationMode]
    max_universe_branches: int
    fictional_simulation_disclaimer: str


class DeleteResponse(ApiSchema):
    deleted: Literal[True]
    id: UUID


class ScenarioDetailResponse(ApiSchema):
    scenario: ScenarioRead
    universes: list[UniverseRead]


class UniverseGenerationResponse(ApiSchema):
    generated: bool
    universes: list[UniverseRead]


class UniverseStateResponse(ApiSchema):
    universe: UniverseRead
    state: LifeStateSnapshotRead


class EventDetailResponse(ApiSchema):
    event: EventRead
    choices: list[ChoiceRead]


class AdvancementResponse(ApiSchema):
    universe_id: UUID
    target_year: int
    blocked: bool
    idempotent: bool
    state: LifeStateSnapshotRead | None = None
    event: EventDetailResponse | None = None
    summary: GeneratedYearSummary | None = None
    artifacts: list[ArtifactRead] = Field(default_factory=list)


class UniverseResetResponse(ApiSchema):
    universe: UniverseRead
    state: LifeStateSnapshotRead


class ComparisonStats(ApiSchema):
    career_level: int
    health: int
    relationships: int
    research_impact: int
    reputation: int
    freedom: int
    stress: int
    happiness: int
    discipline: int
    creativity: int
    chaos: int


class FinancialPosition(ApiSchema):
    monthly_income_eur: int
    net_worth_eur: int


class ComparisonHistoryPoint(ApiSchema):
    year: int
    happiness: int
    stress: int
    net_worth_eur: int


class ScoreComponents(ApiSchema):
    wellbeing: int
    sustainability: int
    career_momentum: int
    research_momentum: int
    financial_resilience: int


class UniverseComparison(ApiSchema):
    universe: UniverseRead
    current_stats: ComparisonStats
    financial_position: FinancialPosition
    location: str
    career_summary: str
    major_achievements: list[str]
    major_regrets: list[str]
    key_decisions: list[str]
    history: list[ComparisonHistoryPoint]
    score_components: ScoreComponents


class ScenarioComparisonResponse(ApiSchema):
    scenario: ScenarioRead
    universes: list[UniverseComparison]


class ConversationCreateRequest(ApiSchema):
    title: str | None = Field(default=None, min_length=1, max_length=220)


class FutureSelfMessageRequest(ApiSchema):
    content: str = Field(min_length=1, max_length=2_000)


class FutureSelfConversationResponse(ApiSchema):
    conversation: FutureSelfConversationRead
    identity: GeneratedFutureSelfProfile
    messages: list[FutureSelfMessageRead]
    pagination: Pagination
