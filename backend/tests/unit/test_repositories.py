from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models import (
    Artifact,
    Choice,
    DelayedEffect,
    Event,
    FutureSelfConversation,
    FutureSelfMessage,
    PersonProfile,
)
from app.models.entities import SnapshotImmutableError
from app.models.enums import (
    ArtifactType,
    EventCategory,
    EventImportance,
    EventSource,
    EventStatus,
    EventType,
    MessageRole,
    RiskLevel,
)
from app.repositories import (
    ArtifactRepository,
    ChoiceRepository,
    DelayedEffectRepository,
    EventRepository,
    FutureSelfConversationRepository,
    FutureSelfMessageRepository,
    LifeStateSnapshotRepository,
    PersonProfileRepository,
)
from app.schemas import ArtifactRead
from app.services.demo_seed import DemoSeedService


def test_repository_flushes_without_owning_the_commit(session: Session) -> None:
    repository = PersonProfileRepository(session)
    profile_id = uuid4()
    repository.add(
        PersonProfile(
            id=profile_id,
            name="Rollback Test",
            birth_year=2000,
            starting_year=2026,
            starting_age=26,
            location="Milan",
            occupation="Engineer",
            education="MSc",
        )
    )

    session.rollback()

    assert repository.get(profile_id) is None


def test_snapshot_history_rejects_in_place_updates(session: Session) -> None:
    result = DemoSeedService(session).seed()
    snapshots = LifeStateSnapshotRepository(session)
    snapshot = snapshots.latest(result.universe_ids[0])
    assert snapshot is not None

    snapshot.happiness = 1
    with pytest.raises(SnapshotImmutableError, match="append a new snapshot"):
        session.flush()
    session.rollback()


def test_phase_two_entities_and_repository_queries_round_trip(session: Session) -> None:
    result = DemoSeedService(session).seed()
    event_repository = EventRepository(session)
    choice_repository = ChoiceRepository(session)
    delayed_repository = DelayedEffectRepository(session)
    artifact_repository = ArtifactRepository(session)
    conversation_repository = FutureSelfConversationRepository(session)
    message_repository = FutureSelfMessageRepository(session)
    snapshot_repository = LifeStateSnapshotRepository(session)

    with session.begin():
        snapshot = snapshot_repository.latest(result.universe_ids[0])
        assert snapshot is not None
        event = event_repository.add(
            Event(
                universe_id=result.universe_ids[0],
                year=2027,
                title="A consequential offer",
                description="A fictional team offers a leadership opportunity.",
                category=EventCategory.CAREER,
                importance=EventImportance.MAJOR,
                event_type=EventType.DECISION,
                status=EventStatus.PENDING,
                is_generated=False,
                source=EventSource.SYSTEM,
            )
        )
        choice = choice_repository.add(
            Choice(
                event_id=event.id,
                label="Accept the role",
                description="Take on the challenge.",
                immediate_effects={"stats": {"reputation": 3}},
                delayed_effects=[{"trigger_after_years": 1}],
                requirements={"stats": {"discipline": 60}},
                risk_level=RiskLevel.MEDIUM,
                selected=True,
                selected_at=datetime.now(UTC),
            )
        )
        delayed_repository.add(
            DelayedEffect(
                universe_id=result.universe_ids[0],
                source_choice_id=choice.id,
                trigger_year=2028,
                effects={"stats": {"career_level": 4}},
                description="The new responsibility compounds into career growth.",
                applied=False,
            )
        )
        artifact = artifact_repository.add(
            Artifact(
                universe_id=result.universe_ids[0],
                event_id=event.id,
                year=2027,
                artifact_type=ArtifactType.LINKEDIN_UPDATE,
                title="A new chapter",
                content={"platform": "Fictional Network", "content": "Starting a new role."},
                artifact_metadata={"generated": False},
            )
        )
        conversation = conversation_repository.add(
            FutureSelfConversation(
                universe_id=result.universe_ids[0],
                title="A conversation across years",
                future_self_age=30,
            )
        )
        message_repository.add(
            FutureSelfMessage(
                conversation_id=conversation.id,
                role=MessageRole.USER,
                content="Was the path worth it?",
                state_snapshot_id=snapshot.id,
            )
        )

    assert event_repository.for_universe(result.universe_ids[0], status=EventStatus.PENDING) == [
        event
    ]
    assert choice_repository.for_event(event.id) == [choice]
    assert delayed_repository.due_for_universe(result.universe_ids[0], 2028)[0].effects == {
        "stats": {"career_level": 4}
    }
    assert artifact_repository.for_universe(result.universe_ids[0]) == [artifact]
    assert conversation_repository.for_universe(result.universe_ids[0]) == [conversation]
    assert (
        message_repository.for_conversation(conversation.id)[0].content == "Was the path worth it?"
    )

    artifact_schema = ArtifactRead.model_validate(artifact)
    assert artifact_schema.metadata == {"generated": False}
