from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import get_core_service
from app.models import Artifact, Choice, Event, LifeStateSnapshot, Universe
from app.models.enums import ArtifactType, EventStatus
from app.services.application import CoreApplicationService
from app.services.demo_seed import APPLIED_AI_UNIVERSE_ID, DemoSeedService
from app.services.narrative import (
    GeneratedArtifact,
    GeneratedEvent,
    GeneratedUniverseBranch,
    MockNarrativeProvider,
    UniverseBranchRequest,
)
from app.services.narrative.schemas import NarrativeContext


class FailingBranchProvider(MockNarrativeProvider):
    async def generate_universe_branches(self, request: object) -> tuple[()]:
        raise RuntimeError("provider failed")


class FailingArtifactProvider(MockNarrativeProvider):
    async def generate_artifact(
        self,
        context: NarrativeContext,
        event: GeneratedEvent,
        artifact_type: ArtifactType | None = None,
    ) -> GeneratedArtifact:
        raise RuntimeError("artifact failed")


class DuplicateBranchProvider(MockNarrativeProvider):
    async def generate_universe_branches(
        self, request: UniverseBranchRequest
    ) -> tuple[GeneratedUniverseBranch, ...]:
        branches = await super().generate_universe_branches(request)
        duplicate = branches[1].model_copy(update={"slug": branches[0].slug})
        return branches[0], duplicate, branches[2]


def _override_service(
    application: FastAPI,
    factory: sessionmaker[Session],
    provider: MockNarrativeProvider,
) -> None:
    def service_override() -> Generator[CoreApplicationService, None, None]:
        with factory() as database_session:
            yield CoreApplicationService(database_session, provider)

    application.dependency_overrides[get_core_service] = service_override


@pytest.mark.anyio
async def test_universe_generation_rolls_back_when_narrative_fails(
    api_app: FastAPI, session_factory: sessionmaker[Session]
) -> None:
    profile = {
        "name": "Lin",
        "birth_year": 1998,
        "starting_year": 2026,
        "starting_age": 28,
        "location": "Rome",
        "occupation": "Researcher",
        "education": "MSc",
    }
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        created_profile = await client.post("/api/v1/profiles", json=profile)
        scenario = await client.post(
            "/api/v1/scenarios",
            json={
                "profile_id": created_profile.json()["id"],
                "title": "A decision",
                "decision_question": "Which path?",
                "number_of_universes": 3,
                "simulation_mode": "realistic",
                "seed": 99,
            },
        )
        scenario_id = UUID(scenario.json()["id"])

    _override_service(api_app, session_factory, FailingBranchProvider())
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        failed = await client.post(f"/api/v1/scenarios/{scenario_id}/generate-universes")
    assert failed.status_code == 503
    assert failed.json()["error"]["code"] == "narrative_unavailable"
    with session_factory() as verification:
        count = verification.scalar(
            select(func.count()).select_from(Universe).where(Universe.scenario_id == scenario_id)
        )
        assert count == 0


@pytest.mark.anyio
async def test_universe_generation_rolls_back_partially_flushed_branches(
    api_app: FastAPI, session_factory: sessionmaker[Session]
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        profile = await client.post(
            "/api/v1/profiles",
            json={
                "name": "Nia",
                "birth_year": 1997,
                "starting_year": 2026,
                "starting_age": 29,
                "location": "Naples",
                "occupation": "Engineer",
                "education": "MSc",
            },
        )
        scenario = await client.post(
            "/api/v1/scenarios",
            json={
                "profile_id": profile.json()["id"],
                "title": "Three paths",
                "decision_question": "Which path?",
                "number_of_universes": 3,
                "simulation_mode": "realistic",
                "seed": 101,
            },
        )
        scenario_id = UUID(scenario.json()["id"])

    _override_service(api_app, session_factory, DuplicateBranchProvider())
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        failed = await client.post(f"/api/v1/scenarios/{scenario_id}/generate-universes")
    assert failed.status_code == 409
    assert failed.json()["error"]["code"] == "conflict"
    with session_factory() as verification:
        count = verification.scalar(
            select(func.count()).select_from(Universe).where(Universe.scenario_id == scenario_id)
        )
        assert count == 0


@pytest.mark.anyio
async def test_choice_and_state_roll_back_when_artifact_generation_fails(
    api_app: FastAPI,
    session: Session,
    session_factory: sessionmaker[Session],
) -> None:
    DemoSeedService(session).seed()
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        advanced = await client.post(f"/api/v1/universes/{APPLIED_AI_UNIVERSE_ID}/advance")
    event_id = UUID(advanced.json()["event"]["event"]["id"])
    choice_id = UUID(advanced.json()["event"]["choices"][0]["id"])

    _override_service(api_app, session_factory, FailingArtifactProvider())
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        failed = await client.post(f"/api/v1/events/{event_id}/choices/{choice_id}/select")
    assert failed.status_code == 503

    with session_factory() as verification:
        event = verification.get(Event, event_id)
        choice = verification.get(Choice, choice_id)
        snapshots = verification.scalar(
            select(func.count())
            .select_from(LifeStateSnapshot)
            .where(LifeStateSnapshot.universe_id == APPLIED_AI_UNIVERSE_ID)
        )
        artifacts = verification.scalar(
            select(func.count())
            .select_from(Artifact)
            .where(Artifact.universe_id == APPLIED_AI_UNIVERSE_ID)
        )
        assert event is not None and event.status == EventStatus.PENDING
        assert choice is not None and choice.selected is False
        assert snapshots == 1
        assert artifacts == 0
