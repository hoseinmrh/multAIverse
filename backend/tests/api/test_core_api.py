from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session, sessionmaker

from app.models import Event, Universe
from app.services.demo_seed import DEMO_PROFILE_ID, DEMO_SCENARIO_ID, DemoSeedService


@pytest.mark.anyio
async def test_complete_seeded_backend_happy_path(api_app: FastAPI, session: Session) -> None:
    DemoSeedService(session).seed()

    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        profiles = await client.get("/api/v1/profiles", params={"limit": 1})
        assert profiles.status_code == 200
        assert profiles.json()["items"][0]["id"] == str(DEMO_PROFILE_ID)
        assert profiles.json()["pagination"] == {
            "offset": 0,
            "limit": 1,
            "total": 1,
            "has_more": False,
        }

        profile = await client.get(f"/api/v1/profiles/{DEMO_PROFILE_ID}")
        assert profile.status_code == 200
        assert profile.json()["name"] == "Hosein"

        scenario = await client.get(f"/api/v1/scenarios/{DEMO_SCENARIO_ID}")
        assert scenario.status_code == 200
        assert scenario.json()["scenario"]["decision_question"].startswith("What should")

        generation = await client.post(f"/api/v1/scenarios/{DEMO_SCENARIO_ID}/generate-universes")
        assert generation.status_code == 201
        assert generation.json()["generated"] is False
        assert len(generation.json()["universes"]) == 3
        universe_ids = [UUID(item["id"]) for item in generation.json()["universes"]]

        universe = await client.get(f"/api/v1/universes/{universe_ids[0]}")
        assert universe.status_code == 200
        initial_year = universe.json()["current_year"]

        advancement = await client.post(f"/api/v1/universes/{universe_ids[0]}/advance")
        assert advancement.status_code == 200
        blocked = advancement.json()
        assert blocked["blocked"] is True
        assert blocked["state"] is None
        assert len(blocked["event"]["choices"]) == 2

        blocked_again = await client.post(f"/api/v1/universes/{universe_ids[0]}/advance")
        assert blocked_again.status_code == 409
        assert blocked_again.json()["error"]["code"] == "conflict"

        event_id = blocked["event"]["event"]["id"]
        choice_id = blocked["event"]["choices"][0]["id"]
        resolution = await client.post(f"/api/v1/events/{event_id}/choices/{choice_id}/select")
        assert resolution.status_code == 200
        resolved = resolution.json()
        assert resolved["blocked"] is False
        assert resolved["idempotent"] is False
        assert resolved["state"]["year"] == initial_year + 1
        assert resolved["summary"]["year"] == initial_year + 1
        assert len(resolved["artifacts"]) == 1

        repeated = await client.post(f"/api/v1/events/{event_id}/choices/{choice_id}/select")
        assert repeated.status_code == 200
        assert repeated.json()["idempotent"] is True
        assert repeated.json()["state"]["id"] == resolved["state"]["id"]

        event = await client.get(f"/api/v1/events/{event_id}")
        assert event.status_code == 200
        assert sum(choice["selected"] for choice in event.json()["choices"]) == 1

        timeline = await client.get(
            f"/api/v1/universes/{universe_ids[0]}/timeline", params={"limit": 1}
        )
        assert timeline.status_code == 200
        assert timeline.json()["pagination"]["total"] == 2
        assert timeline.json()["pagination"]["has_more"] is True

        artifacts = await client.get(f"/api/v1/universes/{universe_ids[0]}/artifacts")
        assert artifacts.status_code == 200
        assert artifacts.json()["pagination"]["total"] == 1
        artifact_id = artifacts.json()["items"][0]["id"]
        artifact = await client.get(f"/api/v1/artifacts/{artifact_id}")
        assert artifact.status_code == 200
        assert artifact.json()["metadata"]["is_fictional"] is True

        comparison = await client.get(f"/api/v1/scenarios/{DEMO_SCENARIO_ID}/comparison")
        assert comparison.status_code == 200
        assert len(comparison.json()["universes"]) == 3
        assert "score_components" in comparison.json()["universes"][0]
        assert "overall_score" not in comparison.json()["universes"][0]

        conversation = await client.post(
            f"/api/v1/universes/{universe_ids[0]}/future-self/conversations",
            json={},
        )
        assert conversation.status_code == 200
        conversation_body = conversation.json()
        assert conversation_body["identity"]["fictional_character"] is True
        assert conversation_body["conversation"]["personality_summary"]

        conversation_id = conversation_body["conversation"]["id"]
        message = await client.post(
            f"/api/v1/future-self/conversations/{conversation_id}/messages",
            json={"content": "What decision changed your life most?"},
        )
        assert message.status_code == 200
        assert [item["role"] for item in message.json()["messages"]] == [
            "user",
            "future_self",
        ]

        paged_conversation = await client.get(
            f"/api/v1/future-self/conversations/{conversation_id}",
            params={"limit": 1},
        )
        assert paged_conversation.status_code == 200
        assert paged_conversation.json()["pagination"]["total"] == 2
        assert paged_conversation.json()["pagination"]["has_more"] is True

        reset = await client.post(f"/api/v1/universes/{universe_ids[0]}/reset")
        assert reset.status_code == 200
        assert reset.json()["state"]["year"] == initial_year
        reset_timeline = await client.get(f"/api/v1/universes/{universe_ids[0]}/timeline")
        assert reset_timeline.json()["pagination"]["total"] == 1
        reset_artifacts = await client.get(f"/api/v1/universes/{universe_ids[0]}/artifacts")
        assert reset_artifacts.json()["pagination"]["total"] == 0
        removed_conversation = await client.get(
            f"/api/v1/future-self/conversations/{conversation_id}"
        )
        assert removed_conversation.status_code == 404


@pytest.mark.anyio
async def test_public_config_and_profile_crud_use_explicit_safe_responses(
    api_app: FastAPI,
) -> None:
    profile_payload = {
        "name": "Ada",
        "birth_year": 1996,
        "starting_year": 2026,
        "starting_age": 30,
        "location": "Turin",
        "occupation": "Engineer",
        "education": "MSc",
    }
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        config = await client.get("/api/v1/config/public")
        assert config.status_code == 200
        serialized = config.text.casefold()
        assert "api_key" not in serialized
        assert "openai_api_key" not in serialized
        assert config.json()["narrative_provider"] == "mock"
        assert config.json()["narrative_provider_status"] == {
            "active_provider": "mock",
            "state": "ready",
            "model": None,
            "fallback_enabled": False,
            "detail": "Offline deterministic narrative generation is ready.",
        }

        created = await client.post("/api/v1/profiles", json=profile_payload)
        assert created.status_code == 201
        profile_id = created.json()["id"]

        updated = await client.patch(f"/api/v1/profiles/{profile_id}", json={"location": "Bologna"})
        assert updated.status_code == 200
        assert updated.json()["location"] == "Bologna"

        deleted = await client.delete(f"/api/v1/profiles/{profile_id}")
        assert deleted.status_code == 200
        assert deleted.json() == {"deleted": True, "id": profile_id}

        missing = await client.get(f"/api/v1/profiles/{profile_id}")
        assert missing.status_code == 404
        assert missing.json()["error"] == {
            "code": "not_found",
            "message": "Profile was not found",
            "details": {"id": profile_id},
        }

        invalid = await client.get("/api/v1/profiles/not-a-uuid")
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "validation_error"
        assert "input" not in invalid.text


@pytest.mark.anyio
async def test_new_scenario_generates_three_persisted_universes(
    api_app: FastAPI, session_factory: sessionmaker[Session]
) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=api_app), base_url="http://testserver"
    ) as client:
        profile = await client.post(
            "/api/v1/profiles",
            json={
                "name": "Mina",
                "birth_year": 1999,
                "starting_year": 2026,
                "starting_age": 27,
                "location": "Florence",
                "occupation": "Engineer",
                "education": "MSc",
            },
        )
        scenario = await client.post(
            "/api/v1/scenarios",
            json={
                "profile_id": profile.json()["id"],
                "title": "After graduation",
                "decision_question": "What should Mina prioritize?",
                "description": (
                    "Three fictional alternatives.\n\n"
                    "Optional branch directions: Continue studying | Build an analyst career | "
                    "Become a content creator."
                ),
                "number_of_universes": 3,
                "simulation_mode": "cinematic",
                "seed": 12345,
            },
        )
        assert scenario.status_code == 201

        generated = await client.post(
            f"/api/v1/scenarios/{scenario.json()['id']}/generate-universes"
        )
        assert generated.status_code == 201
        assert generated.json()["generated"] is True
        universes = generated.json()["universes"]
        assert len(universes) == 3
        expected_directions = {
            "Continue studying",
            "Build an analyst career",
            "Become a content creator",
        }
        assert {item["name"] for item in universes} == expected_directions
        assert {item["starting_direction"] for item in universes} == expected_directions
        assert len({item["random_seed"] for item in universes}) == 3
        assert all(0 <= item["random_seed"] <= 2**53 - 1 for item in universes)

        legacy_directions = (
            ("Applied AI Leader", "applied-ai-leader"),
            ("Robotics Researcher", "robotics-researcher"),
            ("Startup Founder", "startup-founder"),
        )
        with session_factory() as database_session, database_session.begin():
            for item, (name, slug) in zip(universes, legacy_directions, strict=True):
                universe = database_session.get(Universe, UUID(item["id"]))
                assert universe is not None
                universe.name = name
                universe.slug = slug
                universe.starting_direction = name

        repaired = await client.post(
            f"/api/v1/scenarios/{scenario.json()['id']}/generate-universes"
        )
        assert repaired.status_code == 201
        assert repaired.json()["generated"] is True
        universes = repaired.json()["universes"]
        assert {item["name"] for item in universes} == expected_directions

        for universe in universes:
            state = await client.get(f"/api/v1/universes/{universe['id']}/state")
            assert state.status_code == 200
            assert state.json()["state"]["year"] == 2026

        creator = next(
            item for item in universes if item["starting_direction"] == "Become a content creator"
        )
        advanced = await client.post(f"/api/v1/universes/{creator['id']}/advance")
        legacy_event_id = advanced.json()["event"]["event"]["id"]
        with session_factory() as database_session, database_session.begin():
            event = database_session.get(Event, UUID(legacy_event_id))
            assert event is not None
            event.narrative_key = "startup-founder-role"
            event.title = "The company outgrows one founder's job"
            event.description = "An old demo event."

        prepared = await client.post(
            f"/api/v1/scenarios/{scenario.json()['id']}/generate-universes"
        )
        assert prepared.status_code == 201
        assert prepared.json()["generated"] is False
        events = await client.get(f"/api/v1/universes/{creator['id']}/events")
        replacement = events.json()["items"][0]
        assert replacement["id"] != legacy_event_id
        assert replacement["narrative_key"].startswith("custom-creator-")
        assert "founder" not in replacement["title"].casefold()
