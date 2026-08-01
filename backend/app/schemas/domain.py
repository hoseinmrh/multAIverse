from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, JsonValue, model_validator

from app.models.enums import (
    ArtifactType,
    EventCategory,
    EventImportance,
    EventSource,
    EventStatus,
    EventType,
    MessageRole,
    RiskLevel,
    SimulationMode,
    UniverseStatus,
)

JsonObject = dict[str, JsonValue]
NormalizedScore = Field(ge=0, le=100)


class DomainSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True, populate_by_name=True)


class PersonProfileBase(DomainSchema):
    name: str = Field(min_length=1, max_length=120)
    birth_year: int = Field(gt=1900)
    starting_year: int = Field(gt=1900)
    starting_age: int = Field(ge=0, le=130)
    location: str = Field(min_length=1, max_length=160)
    occupation: str = Field(min_length=1, max_length=200)
    education: str = Field(min_length=1)
    biography: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    starting_stats: JsonObject = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_starting_year(self) -> Self:
        if self.starting_year < self.birth_year:
            raise ValueError("starting_year must not be earlier than birth_year")
        return self


class PersonProfileCreate(PersonProfileBase):
    pass


class PersonProfileUpdate(DomainSchema):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    birth_year: int | None = Field(default=None, gt=1900)
    starting_year: int | None = Field(default=None, gt=1900)
    starting_age: int | None = Field(default=None, ge=0, le=130)
    location: str | None = Field(default=None, min_length=1, max_length=160)
    occupation: str | None = Field(default=None, min_length=1, max_length=200)
    education: str | None = Field(default=None, min_length=1)
    biography: str | None = None
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    interests: list[str] | None = None
    goals: list[str] | None = None
    constraints: list[str] | None = None
    starting_stats: JsonObject | None = None


class PersonProfileRead(PersonProfileBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class ScenarioBase(DomainSchema):
    profile_id: UUID
    title: str = Field(min_length=1, max_length=200)
    decision_question: str = Field(min_length=1)
    description: str = ""
    number_of_universes: int = Field(default=3, gt=0, le=10)
    simulation_mode: SimulationMode = SimulationMode.REALISTIC
    seed: int


class ScenarioCreate(ScenarioBase):
    pass


class ScenarioRead(ScenarioBase):
    id: UUID
    created_at: datetime


class UniverseBase(DomainSchema):
    scenario_id: UUID
    name: str = Field(min_length=1, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)
    subtitle: str = Field(min_length=1, max_length=220)
    premise: str = Field(min_length=1)
    visual_theme: JsonObject
    starting_direction: str = Field(min_length=1)
    current_year: int = Field(gt=1900)
    current_age: int = Field(ge=0, le=130)
    random_seed: int
    status: UniverseStatus = UniverseStatus.ACTIVE


class UniverseCreate(UniverseBase):
    pass


class UniverseRead(UniverseBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


class LifeStateSnapshotBase(DomainSchema):
    universe_id: UUID
    year: int = Field(gt=1900)
    age: int = Field(ge=0, le=130)
    location: str = Field(min_length=1, max_length=160)
    career_title: str = Field(min_length=1, max_length=200)
    career_level: int = NormalizedScore
    monthly_income_eur: int = Field(ge=0)
    net_worth_eur: int
    health: int = NormalizedScore
    relationships: int = NormalizedScore
    research_impact: int = NormalizedScore
    reputation: int = NormalizedScore
    freedom: int = NormalizedScore
    stress: int = NormalizedScore
    happiness: int = NormalizedScore
    discipline: int = NormalizedScore
    creativity: int = NormalizedScore
    chaos: int = NormalizedScore
    skills: JsonObject = Field(default_factory=dict)
    active_flags: list[str] = Field(default_factory=list)


class LifeStateSnapshotCreate(LifeStateSnapshotBase):
    pass


class LifeStateSnapshotRead(LifeStateSnapshotBase):
    id: UUID
    created_at: datetime


class EventBase(DomainSchema):
    universe_id: UUID
    year: int = Field(gt=1900)
    title: str = Field(min_length=1, max_length=220)
    description: str = Field(min_length=1)
    category: EventCategory
    importance: EventImportance
    event_type: EventType
    status: EventStatus = EventStatus.PENDING
    is_generated: bool = False
    source: EventSource = EventSource.SYSTEM


class EventCreate(EventBase):
    pass


class EventRead(EventBase):
    id: UUID
    created_at: datetime


class ChoiceBase(DomainSchema):
    event_id: UUID
    label: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=1)
    immediate_effects: JsonObject = Field(default_factory=dict)
    delayed_effects: list[JsonValue] = Field(default_factory=list)
    requirements: JsonObject = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.MEDIUM


class ChoiceCreate(ChoiceBase):
    pass


class ChoiceRead(ChoiceBase):
    id: UUID
    selected: bool
    selected_at: datetime | None


class DelayedEffectBase(DomainSchema):
    universe_id: UUID
    source_choice_id: UUID
    trigger_year: int = Field(gt=1900)
    effects: JsonObject
    description: str = Field(min_length=1)


class DelayedEffectCreate(DelayedEffectBase):
    pass


class DelayedEffectRead(DelayedEffectBase):
    id: UUID
    applied: bool


class ArtifactBase(DomainSchema):
    universe_id: UUID
    event_id: UUID | None = None
    year: int = Field(gt=1900)
    artifact_type: ArtifactType
    title: str = Field(min_length=1, max_length=240)
    content: JsonObject
    metadata: JsonObject = Field(
        default_factory=dict,
        validation_alias=AliasChoices("artifact_metadata", "metadata"),
    )


class ArtifactCreate(ArtifactBase):
    pass


class ArtifactRead(ArtifactBase):
    id: UUID
    created_at: datetime


class FutureSelfConversationBase(DomainSchema):
    universe_id: UUID
    title: str = Field(min_length=1, max_length=220)
    future_self_age: int = Field(ge=0, le=130)


class FutureSelfConversationCreate(FutureSelfConversationBase):
    pass


class FutureSelfConversationRead(FutureSelfConversationBase):
    id: UUID
    created_at: datetime


class FutureSelfMessageBase(DomainSchema):
    conversation_id: UUID
    role: MessageRole
    content: str = Field(min_length=1)
    state_snapshot_id: UUID | None = None


class FutureSelfMessageCreate(FutureSelfMessageBase):
    pass


class FutureSelfMessageRead(FutureSelfMessageBase):
    id: UUID
    created_at: datetime
