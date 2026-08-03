from __future__ import annotations

from datetime import UTC, datetime
from typing import Never
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
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

JsonObject = dict[str, object]


def utc_now() -> datetime:
    return datetime.now(UTC)


class SnapshotImmutableError(RuntimeError):
    """Raised when persisted historical state is modified in place."""


class PersonProfile(Base):
    __tablename__ = "person_profiles"
    __table_args__ = (
        CheckConstraint("birth_year > 1900", name="birth_year_valid"),
        CheckConstraint("starting_year >= birth_year", name="starting_year_valid"),
        CheckConstraint("starting_age >= 0", name="starting_age_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    birth_year: Mapped[int] = mapped_column(Integer, nullable=False)
    starting_year: Mapped[int] = mapped_column(Integer, nullable=False)
    starting_age: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    occupation: Mapped[str] = mapped_column(String(200), nullable=False)
    education: Mapped[str] = mapped_column(Text, nullable=False)
    biography: Mapped[str] = mapped_column(Text, nullable=False, default="")
    strengths: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    interests: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    goals: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    constraints: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    starting_stats: Mapped[JsonObject] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    scenarios: Mapped[list[Scenario]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", passive_deletes=True
    )


class Scenario(Base):
    __tablename__ = "scenarios"
    __table_args__ = (CheckConstraint("number_of_universes > 0", name="universe_count_positive"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("person_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    decision_question: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    number_of_universes: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    simulation_mode: Mapped[SimulationMode] = mapped_column(
        Enum(
            SimulationMode,
            name="simulation_mode",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
        default=SimulationMode.REALISTIC,
    )
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    profile: Mapped[PersonProfile] = relationship(back_populates="scenarios")
    universes: Mapped[list[Universe]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan", passive_deletes=True
    )


class Universe(Base):
    __tablename__ = "universes"
    __table_args__ = (
        UniqueConstraint("scenario_id", "slug", name="uq_universes_scenario_slug"),
        CheckConstraint("current_age >= 0", name="current_age_nonnegative"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    scenario_id: Mapped[UUID] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(220), nullable=False)
    premise: Mapped[str] = mapped_column(Text, nullable=False)
    visual_theme: Mapped[JsonObject] = mapped_column(JSON, nullable=False)
    starting_direction: Mapped[str] = mapped_column(Text, nullable=False)
    current_year: Mapped[int] = mapped_column(Integer, nullable=False)
    current_age: Mapped[int] = mapped_column(Integer, nullable=False)
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[UniverseStatus] = mapped_column(
        Enum(
            UniverseStatus,
            name="universe_status",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
        default=UniverseStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    scenario: Mapped[Scenario] = relationship(back_populates="universes")
    snapshots: Mapped[list[LifeStateSnapshot]] = relationship(
        back_populates="universe",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="LifeStateSnapshot.year",
    )
    events: Mapped[list[Event]] = relationship(
        back_populates="universe", cascade="all, delete-orphan", passive_deletes=True
    )
    delayed_effects: Mapped[list[DelayedEffect]] = relationship(
        back_populates="universe", cascade="all, delete-orphan", passive_deletes=True
    )
    artifacts: Mapped[list[Artifact]] = relationship(
        back_populates="universe", cascade="all, delete-orphan", passive_deletes=True
    )
    future_self_conversations: Mapped[list[FutureSelfConversation]] = relationship(
        back_populates="universe", cascade="all, delete-orphan", passive_deletes=True
    )


class LifeStateSnapshot(Base):
    __tablename__ = "life_state_snapshots"
    __table_args__ = (
        UniqueConstraint("universe_id", "year", name="uq_snapshots_universe_year"),
        CheckConstraint("age >= 0", name="age_nonnegative"),
        CheckConstraint("career_level BETWEEN 0 AND 100", name="career_level_range"),
        CheckConstraint("monthly_income_eur >= 0", name="monthly_income_nonnegative"),
        CheckConstraint("health BETWEEN 0 AND 100", name="health_range"),
        CheckConstraint("relationships BETWEEN 0 AND 100", name="relationships_range"),
        CheckConstraint("research_impact BETWEEN 0 AND 100", name="research_impact_range"),
        CheckConstraint("reputation BETWEEN 0 AND 100", name="reputation_range"),
        CheckConstraint("freedom BETWEEN 0 AND 100", name="freedom_range"),
        CheckConstraint("stress BETWEEN 0 AND 100", name="stress_range"),
        CheckConstraint("happiness BETWEEN 0 AND 100", name="happiness_range"),
        CheckConstraint("discipline BETWEEN 0 AND 100", name="discipline_range"),
        CheckConstraint("creativity BETWEEN 0 AND 100", name="creativity_range"),
        CheckConstraint("chaos BETWEEN 0 AND 100", name="chaos_range"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    universe_id: Mapped[UUID] = mapped_column(
        ForeignKey("universes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(160), nullable=False)
    career_title: Mapped[str] = mapped_column(String(200), nullable=False)
    career_level: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_income_eur: Mapped[int] = mapped_column(Integer, nullable=False)
    net_worth_eur: Mapped[int] = mapped_column(Integer, nullable=False)
    health: Mapped[int] = mapped_column(Integer, nullable=False)
    relationships: Mapped[int] = mapped_column(Integer, nullable=False)
    research_impact: Mapped[int] = mapped_column(Integer, nullable=False)
    reputation: Mapped[int] = mapped_column(Integer, nullable=False)
    freedom: Mapped[int] = mapped_column(Integer, nullable=False)
    stress: Mapped[int] = mapped_column(Integer, nullable=False)
    happiness: Mapped[int] = mapped_column(Integer, nullable=False)
    discipline: Mapped[int] = mapped_column(Integer, nullable=False)
    creativity: Mapped[int] = mapped_column(Integer, nullable=False)
    chaos: Mapped[int] = mapped_column(Integer, nullable=False)
    skills: Mapped[JsonObject] = mapped_column(JSON, nullable=False, default=dict)
    active_flags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    universe: Mapped[Universe] = relationship(back_populates="snapshots")
    future_self_messages: Mapped[list[FutureSelfMessage]] = relationship(
        back_populates="state_snapshot"
    )


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (CheckConstraint("importance != ''", name="importance_present"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    universe_id: Mapped[UUID] = mapped_column(
        ForeignKey("universes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    narrative_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[EventCategory] = mapped_column(
        Enum(
            EventCategory,
            name="event_category",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    importance: Mapped[EventImportance] = mapped_column(
        Enum(
            EventImportance,
            name="event_importance",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    event_type: Mapped[EventType] = mapped_column(
        Enum(
            EventType,
            name="event_type",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    status: Mapped[EventStatus] = mapped_column(
        Enum(
            EventStatus,
            name="event_status",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
        default=EventStatus.PENDING,
    )
    is_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[EventSource] = mapped_column(
        Enum(
            EventSource,
            name="event_source",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
        default=EventSource.SYSTEM,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    universe: Mapped[Universe] = relationship(back_populates="events")
    choices: Mapped[list[Choice]] = relationship(
        back_populates="event", cascade="all, delete-orphan", passive_deletes=True
    )
    artifacts: Mapped[list[Artifact]] = relationship(back_populates="event")


class Choice(Base):
    __tablename__ = "choices"
    __table_args__ = (UniqueConstraint("event_id", "label", name="uq_choices_event_label"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    immediate_effects: Mapped[JsonObject] = mapped_column(JSON, nullable=False, default=dict)
    delayed_effects: Mapped[list[object]] = mapped_column(JSON, nullable=False, default=list)
    requirements: Mapped[JsonObject] = mapped_column(JSON, nullable=False, default=dict)
    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(
            RiskLevel,
            name="risk_level",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
        default=RiskLevel.MEDIUM,
    )
    selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    selected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    event: Mapped[Event] = relationship(back_populates="choices")
    scheduled_effects: Mapped[list[DelayedEffect]] = relationship(back_populates="source_choice")


class DelayedEffect(Base):
    __tablename__ = "delayed_effects"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    universe_id: Mapped[UUID] = mapped_column(
        ForeignKey("universes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_choice_id: Mapped[UUID] = mapped_column(
        ForeignKey("choices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trigger_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    effects: Mapped[JsonObject] = mapped_column(JSON, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    universe: Mapped[Universe] = relationship(back_populates="delayed_effects")
    source_choice: Mapped[Choice] = relationship(back_populates="scheduled_effects")


Index(
    "uq_choices_one_selected_per_event",
    Choice.event_id,
    unique=True,
    sqlite_where=Choice.selected.is_(True),
)


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    universe_id: Mapped[UUID] = mapped_column(
        ForeignKey("universes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(
            ArtifactType,
            name="artifact_type",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    content: Mapped[JsonObject] = mapped_column(JSON, nullable=False)
    artifact_metadata: Mapped[JsonObject] = mapped_column(
        "metadata", JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    universe: Mapped[Universe] = relationship(back_populates="artifacts")
    event: Mapped[Event | None] = relationship(back_populates="artifacts")


class FutureSelfConversation(Base):
    __tablename__ = "future_self_conversations"
    __table_args__ = (CheckConstraint("future_self_age >= 0", name="future_self_age_nonnegative"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    universe_id: Mapped[UUID] = mapped_column(
        ForeignKey("universes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(220), nullable=False)
    future_self_age: Mapped[int] = mapped_column(Integer, nullable=False)
    personality_summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="Reflective, grounded, and consistent with the stored timeline.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    universe: Mapped[Universe] = relationship(back_populates="future_self_conversations")
    messages: Mapped[list[FutureSelfMessage]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", passive_deletes=True
    )


class FutureSelfMessage(Base):
    __tablename__ = "future_self_messages"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("future_self_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(
            MessageRole,
            name="message_role",
            native_enum=False,
            create_constraint=True,
            values_callable=lambda values: [value.value for value in values],
        ),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    state_snapshot_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("life_state_snapshots.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    conversation: Mapped[FutureSelfConversation] = relationship(back_populates="messages")
    state_snapshot: Mapped[LifeStateSnapshot | None] = relationship(
        back_populates="future_self_messages"
    )


@event.listens_for(LifeStateSnapshot, "before_update", propagate=True)
def reject_snapshot_update(*_: object) -> Never:
    raise SnapshotImmutableError(
        "Life-state snapshots are immutable; append a new snapshot instead."
    )
