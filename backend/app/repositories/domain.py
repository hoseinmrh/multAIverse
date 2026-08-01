from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.models import (
    Artifact,
    Choice,
    DelayedEffect,
    Event,
    FutureSelfConversation,
    FutureSelfMessage,
    LifeStateSnapshot,
    PersonProfile,
    Scenario,
    Universe,
)
from app.models.enums import EventStatus


class ReadRepository[ModelT: Base]:
    """Typed read operations shared by entity repositories."""

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, entity_id: UUID) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def list(self) -> list[ModelT]:
        return list(self.session.scalars(select(self.model)).all())


class MutableRepository[ModelT: Base](ReadRepository[ModelT]):
    """Persistence operations that flush but never commit."""

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: ModelT) -> None:
        self.session.delete(entity)
        self.session.flush()


class PersonProfileRepository(MutableRepository[PersonProfile]):
    model = PersonProfile

    def find_by_name(self, name: str) -> PersonProfile | None:
        return self.session.scalar(select(PersonProfile).where(PersonProfile.name == name))

    def update(self, profile: PersonProfile, changes: Mapping[str, object]) -> PersonProfile:
        for field, value in changes.items():
            if field not in PersonProfile.__table__.columns:
                raise ValueError(f"Unknown profile field: {field}")
            if field in {"id", "created_at", "updated_at"}:
                raise ValueError(f"Profile field cannot be updated: {field}")
            setattr(profile, field, value)
        self.session.flush()
        return profile


class ScenarioRepository(MutableRepository[Scenario]):
    model = Scenario

    def for_profile(self, profile_id: UUID) -> list[Scenario]:
        statement = (
            select(Scenario).where(Scenario.profile_id == profile_id).order_by(Scenario.created_at)
        )
        return list(self.session.scalars(statement).all())


class UniverseRepository(MutableRepository[Universe]):
    model = Universe

    def for_scenario(self, scenario_id: UUID) -> list[Universe]:
        statement = (
            select(Universe).where(Universe.scenario_id == scenario_id).order_by(Universe.name)
        )
        return list(self.session.scalars(statement).all())

    def find_by_slug(self, scenario_id: UUID, slug: str) -> Universe | None:
        return self.session.scalar(
            select(Universe).where(Universe.scenario_id == scenario_id, Universe.slug == slug)
        )


class EventRepository(MutableRepository[Event]):
    model = Event

    def for_universe(self, universe_id: UUID, *, status: EventStatus | None = None) -> list[Event]:
        statement: Select[tuple[Event]] = select(Event).where(Event.universe_id == universe_id)
        if status is not None:
            statement = statement.where(Event.status == status)
        statement = statement.order_by(Event.year, Event.created_at)
        return list(self.session.scalars(statement).all())


class LifeStateSnapshotRepository(ReadRepository[LifeStateSnapshot]):
    """Append-only access to immutable life-state history."""

    model = LifeStateSnapshot

    def add(self, snapshot: LifeStateSnapshot) -> LifeStateSnapshot:
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def for_universe(self, universe_id: UUID) -> list[LifeStateSnapshot]:
        statement = (
            select(LifeStateSnapshot)
            .where(LifeStateSnapshot.universe_id == universe_id)
            .order_by(LifeStateSnapshot.year)
        )
        return list(self.session.scalars(statement).all())

    def latest(self, universe_id: UUID) -> LifeStateSnapshot | None:
        statement = (
            select(LifeStateSnapshot)
            .where(LifeStateSnapshot.universe_id == universe_id)
            .order_by(LifeStateSnapshot.year.desc())
            .limit(1)
        )
        return self.session.scalar(statement)


class ChoiceRepository(MutableRepository[Choice]):
    model = Choice

    def for_event(self, event_id: UUID) -> list[Choice]:
        statement = select(Choice).where(Choice.event_id == event_id).order_by(Choice.label)
        return list(self.session.scalars(statement).all())


class DelayedEffectRepository(MutableRepository[DelayedEffect]):
    model = DelayedEffect

    def due_for_universe(self, universe_id: UUID, through_year: int) -> list[DelayedEffect]:
        statement = (
            select(DelayedEffect)
            .where(
                DelayedEffect.universe_id == universe_id,
                DelayedEffect.trigger_year <= through_year,
                DelayedEffect.applied.is_(False),
            )
            .order_by(DelayedEffect.trigger_year)
        )
        return list(self.session.scalars(statement).all())


class ArtifactRepository(MutableRepository[Artifact]):
    model = Artifact

    def for_universe(self, universe_id: UUID) -> list[Artifact]:
        statement = (
            select(Artifact)
            .where(Artifact.universe_id == universe_id)
            .order_by(Artifact.year, Artifact.created_at)
        )
        return list(self.session.scalars(statement).all())


class FutureSelfConversationRepository(MutableRepository[FutureSelfConversation]):
    model = FutureSelfConversation

    def for_universe(self, universe_id: UUID) -> list[FutureSelfConversation]:
        statement = (
            select(FutureSelfConversation)
            .where(FutureSelfConversation.universe_id == universe_id)
            .order_by(FutureSelfConversation.created_at)
        )
        return list(self.session.scalars(statement).all())


class FutureSelfMessageRepository(MutableRepository[FutureSelfMessage]):
    model = FutureSelfMessage

    def for_conversation(self, conversation_id: UUID) -> list[FutureSelfMessage]:
        statement = (
            select(FutureSelfMessage)
            .where(FutureSelfMessage.conversation_id == conversation_id)
            .order_by(FutureSelfMessage.created_at)
        )
        return list(self.session.scalars(statement).all())
