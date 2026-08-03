from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Request
from openai import APITimeoutError
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import get_core_service
from app.models import Artifact, Choice, Event, LifeStateSnapshot, Scenario, Universe
from app.models.enums import ArtifactType, EventStatus
from app.services.application import CoreApplicationService
from app.services.demo_seed import APPLIED_AI_UNIVERSE_ID, DemoSeedService
from app.services.narrative import (
    GeneratedArtifact,
    GeneratedEvent,
    GeneratedUniverseBranch,
    MockNarrativeProvider,
    NarrativeProvider,
    OpenAINarrativeConfiguration,
    OpenAINarrativeProvider,
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


class StrictLLMProvider(MockNarrativeProvider):
    provider_name = "openai"
    last_used_provider = "openai"
    llm_only = True

    def __init__(self) -> None:
        self.branch_calls = 0
        self.event_calls = 0

    async def generate_universe_branches(
        self, request: UniverseBranchRequest
    ) -> tuple[GeneratedUniverseBranch, ...]:
        self.branch_calls += 1
        branches = await super().generate_universe_branches(request)
        return tuple(
            branch.model_copy(
                update={
                    "name": f"LLM {branch.name}",
                    "slug": f"llm-{branch.slug}",
                    "subtitle": f"LLM-authored: {branch.subtitle}",
                }
            )
            for branch in branches
        )

    async def generate_significant_event(self, context: NarrativeContext) -> GeneratedEvent:
        self.event_calls += 1
        event = await super().generate_significant_event(context)
        return event.model_copy(
            update={
                "event_key": f"llm-{event.event_key}",
                "title": f"LLM {event.title}",
            }
        )


class FailingStrictLLMProvider(StrictLLMProvider):
    async def generate_universe_branches(
        self, request: UniverseBranchRequest
    ) -> tuple[GeneratedUniverseBranch, ...]:
        raise RuntimeError("provider failed")


def _override_service(
    application: FastAPI,
    factory: sessionmaker[Session],
    provider: NarrativeProvider,
) -> None:
    def service_override() -> Generator[CoreApplicationService, None, None]:
        with factory() as database_session:
            yield CoreApplicationService(database_session, provider)

    application.dependency_overrides[get_core_service] = service_override


class _TimeoutResponses:
    async def parse(self, **_: object) -> None:
        raise APITimeoutError(Request("POST", "https://api.openai.com/v1/responses"))


class _TimeoutClient:
    responses = _TimeoutResponses()


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
async def test_legacy_branch_repair_rolls_back_when_narrative_fails(
    api_app: FastAPI, session_factory: sessionmaker[Session]
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        profile = await client.post(
            "/api/v1/profiles",
            json={
                "name": "Ari",
                "birth_year": 1998,
                "starting_year": 2026,
                "starting_age": 28,
                "location": "Rome",
                "occupation": "Analyst",
                "education": "MSc",
            },
        )
        scenario = await client.post(
            "/api/v1/scenarios",
            json={
                "profile_id": profile.json()["id"],
                "title": "A decision",
                "decision_question": "Which path should Ari choose?",
                "number_of_universes": 3,
                "simulation_mode": "realistic",
                "seed": 102,
            },
        )
        scenario_id = UUID(scenario.json()["id"])
        generated = await client.post(f"/api/v1/scenarios/{scenario_id}/generate-universes")
        original_ids = {item["id"] for item in generated.json()["universes"]}

    with session_factory() as database_session, database_session.begin():
        stored = database_session.get(Scenario, scenario_id)
        assert stored is not None
        stored.description = (
            "Optional branch directions: Continue studying | Build a career | Create content."
        )

    _override_service(api_app, session_factory, FailingBranchProvider())
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        failed = await client.post(f"/api/v1/scenarios/{scenario_id}/generate-universes")

    assert failed.status_code == 503
    with session_factory() as verification:
        preserved_ids = {
            str(item)
            for item in verification.scalars(
                select(Universe.id).where(Universe.scenario_id == scenario_id)
            )
        }
        assert preserved_ids == original_ids


@pytest.mark.anyio
async def test_strict_llm_mode_replaces_unplayed_mock_story_and_authors_yearly_event(
    api_app: FastAPI, session_factory: sessionmaker[Session]
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        profile = await client.post(
            "/api/v1/profiles",
            json={
                "name": "Samira",
                "birth_year": 1998,
                "starting_year": 2026,
                "starting_age": 28,
                "location": "Milan",
                "occupation": "Analyst",
                "education": "MSc",
            },
        )
        scenario = await client.post(
            "/api/v1/scenarios",
            json={
                "profile_id": profile.json()["id"],
                "title": "A new chapter",
                "decision_question": "What should Samira prioritize?",
                "description": (
                    "Optional branch directions: Study further | Build a career | Create media."
                ),
                "number_of_universes": 3,
                "simulation_mode": "realistic",
                "seed": 303,
            },
        )
        scenario_id = UUID(scenario.json()["id"])
        generated = await client.post(f"/api/v1/scenarios/{scenario_id}/generate-universes")
        original_ids = {item["id"] for item in generated.json()["universes"]}
        first_original_id = next(iter(original_ids))
        pending = await client.post(f"/api/v1/universes/{first_original_id}/advance")
        assert pending.status_code == 200
        assert pending.json()["event"]["event"]["source"] == "mock"

    provider = StrictLLMProvider()
    _override_service(api_app, session_factory, provider)
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        regenerated = await client.post(f"/api/v1/scenarios/{scenario_id}/generate-universes")
        assert regenerated.status_code == 201
        assert regenerated.json()["generated"] is True
        universes = regenerated.json()["universes"]
        replacement_ids = {item["id"] for item in universes}
        assert replacement_ids.isdisjoint(original_ids)
        assert provider.branch_calls == 1
        assert all(item["name"].startswith("LLM ") for item in universes)
        assert all(item["visual_theme"]["narrative_provider"] == "openai" for item in universes)

        yearly = await client.post(f"/api/v1/universes/{universes[0]['id']}/advance")
        assert yearly.status_code == 200
        assert yearly.json()["blocked"] is True
        assert yearly.json()["event"]["event"]["source"] == "openai"
        assert yearly.json()["event"]["event"]["title"].startswith("LLM ")
        assert provider.event_calls == 1

        event_id = yearly.json()["event"]["event"]["id"]
        choice_id = yearly.json()["event"]["choices"][0]["id"]
        resolved = await client.post(f"/api/v1/events/{event_id}/choices/{choice_id}/select")
        assert resolved.status_code == 200
        timeline_events = await client.get(f"/api/v1/universes/{universes[0]['id']}/events")
        assert timeline_events.status_code == 200
        assert timeline_events.json()["pagination"]["total"] == 2
        assert {item["source"] for item in timeline_events.json()["items"]} == {"openai"}


@pytest.mark.anyio
async def test_strict_llm_replacement_failure_preserves_existing_mock_story(
    api_app: FastAPI, session_factory: sessionmaker[Session]
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        profile = await client.post(
            "/api/v1/profiles",
            json={
                "name": "Noor",
                "birth_year": 1997,
                "starting_year": 2026,
                "starting_age": 29,
                "location": "Rome",
                "occupation": "Designer",
                "education": "BA",
            },
        )
        scenario = await client.post(
            "/api/v1/scenarios",
            json={
                "profile_id": profile.json()["id"],
                "title": "Three directions",
                "decision_question": "Which direction should Noor take?",
                "number_of_universes": 3,
                "simulation_mode": "realistic",
                "seed": 304,
            },
        )
        scenario_id = UUID(scenario.json()["id"])
        generated = await client.post(f"/api/v1/scenarios/{scenario_id}/generate-universes")
        original_ids = {item["id"] for item in generated.json()["universes"]}

    _override_service(api_app, session_factory, FailingStrictLLMProvider())
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        failed = await client.post(f"/api/v1/scenarios/{scenario_id}/generate-universes")

    assert failed.status_code == 503
    with session_factory() as verification:
        preserved_ids = {
            str(item)
            for item in verification.scalars(
                select(Universe.id).where(Universe.scenario_id == scenario_id)
            )
        }
        assert preserved_ids == original_ids


@pytest.mark.anyio
async def test_openai_timeout_preserves_universe_state(
    api_app: FastAPI,
    session: Session,
    session_factory: sessionmaker[Session],
) -> None:
    DemoSeedService(session).seed()
    provider = OpenAINarrativeProvider(
        OpenAINarrativeConfiguration(
            api_key="sk-test-only",
            model="test-model",
            max_retries=0,
            fallback_to_mock=False,
        ),
        client=_TimeoutClient(),
    )
    _override_service(api_app, session_factory, provider)

    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        failed = await client.post(f"/api/v1/universes/{APPLIED_AI_UNIVERSE_ID}/advance")

    assert failed.status_code == 503
    assert "sk-test-only" not in failed.text
    with session_factory() as verification:
        universe = verification.get(Universe, APPLIED_AI_UNIVERSE_ID)
        snapshots = verification.scalar(
            select(func.count())
            .select_from(LifeStateSnapshot)
            .where(LifeStateSnapshot.universe_id == APPLIED_AI_UNIVERSE_ID)
        )
        events = verification.scalar(
            select(func.count())
            .select_from(Event)
            .where(Event.universe_id == APPLIED_AI_UNIVERSE_ID)
        )
        assert universe is not None and universe.current_year == 2026
        assert snapshots == 1
        assert events == 0


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
