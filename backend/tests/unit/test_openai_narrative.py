import logging
from dataclasses import dataclass
from typing import Any, cast

import httpx
import pytest
from openai import APITimeoutError, AuthenticationError, BadRequestError, RateLimitError, omit
from openai.lib._pydantic import to_strict_json_schema
from sqlalchemy.orm import Session

from app.models import PersonProfile, Scenario, Universe
from app.models.enums import ArtifactType
from app.repositories import (
    LifeStateSnapshotRepository,
    PersonProfileRepository,
    ScenarioRepository,
    UniverseRepository,
)
from app.services.demo_seed import APPLIED_AI_UNIVERSE_ID, DemoSeedService
from app.services.narrative import (
    FutureSelfReplyRequest,
    MockNarrativeProvider,
    NarrativeContext,
    NarrativeContextBuilder,
    NarrativeProviderAuthenticationError,
    NarrativeProviderEmptyResponseError,
    NarrativeProviderInputLimitError,
    NarrativeProviderInvalidOutputError,
    NarrativeProviderRateLimitError,
    NarrativeProviderRequestError,
    NarrativeProviderTimeoutError,
    OpenAINarrativeConfiguration,
    OpenAINarrativeProvider,
    UniverseBranchRequest,
    get_narrative_provider_status,
)
from app.services.narrative.openai import (
    OUTPUT_TOKEN_BUDGETS,
    ReasoningEffort,
    VerbosityLevel,
)
from app.services.narrative.prompts import (
    MAX_FUTURE_SELF_HISTORY_MESSAGES,
    MAX_NARRATIVE_INPUT_CHARS,
    NarrativeInputTooLargeError,
    NarrativePrompt,
    build_artifact_prompt,
    build_future_self_reply_prompt,
    build_significant_event_prompt,
    build_year_summary_prompt,
)
from app.services.narrative.schemas import (
    FutureSelfMessage,
    GeneratedArtifact,
    GeneratedEvent,
    GeneratedFutureSelfProfile,
    GeneratedFutureSelfReply,
    GeneratedUniverseBranches,
    GeneratedYearSummary,
)
from app.services.simulation import state_from_snapshot


@dataclass
class FakeResponse:
    output_parsed: object | None
    output_text: str = "{}"


class FakeResponses:
    def __init__(self, outcomes: list[object]) -> None:
        self.outcomes = outcomes
        self.calls: list[dict[str, Any]] = []

    async def parse(self, **kwargs: Any) -> FakeResponse:
        self.calls.append(kwargs)
        if not self.outcomes:
            raise AssertionError("Unexpected SDK request")
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        if not isinstance(outcome, FakeResponse):
            raise AssertionError("Fake SDK outcome must be a response or exception")
        return outcome


class FakeClient:
    def __init__(self, outcomes: list[object]) -> None:
        self.responses = FakeResponses(outcomes)


def _required[ValueT](value: ValueT | None) -> ValueT:
    assert value is not None
    return value


def _seeded_context(
    session: Session,
) -> tuple[NarrativeContext, PersonProfile, Scenario, Universe]:
    seeded = DemoSeedService(session).seed()
    profile = _required(PersonProfileRepository(session).get(seeded.profile_id))
    scenario = _required(ScenarioRepository(session).get(seeded.scenario_id))
    universe = _required(UniverseRepository(session).get(APPLIED_AI_UNIVERSE_ID))
    snapshot = _required(LifeStateSnapshotRepository(session).latest(universe.id))
    return (
        NarrativeContextBuilder().build(
            profile=profile,
            scenario=scenario,
            universe=universe,
            current_state=state_from_snapshot(snapshot),
        ),
        profile,
        scenario,
        universe,
    )


def _completed_context(context: NarrativeContext, event: GeneratedEvent) -> NarrativeContext:
    payload = context.model_dump(mode="python")
    payload["current_year"] += 1
    payload["current_state"]["year"] += 1
    payload["current_state"]["age"] += 1
    payload["previous_event_keys"] = [event.event_key]
    payload["last_major_events"] = [
        {
            "event_key": event.event_key,
            "year": event.year,
            "title": event.title,
            "description": event.description,
            "category": event.category,
            "importance": event.importance,
        }
    ]
    return NarrativeContext.model_validate(payload)


def _provider(
    outcomes: list[object], *, retries: int = 0, fallback: bool = False
) -> tuple[OpenAINarrativeProvider, FakeClient]:
    client = FakeClient(outcomes)
    provider = OpenAINarrativeProvider(
        OpenAINarrativeConfiguration(
            api_key="sk-test-only",
            model="test-model",
            max_retries=retries,
            fallback_to_mock=fallback,
            retry_base_seconds=0,
            reasoning_effort="low",
            verbosity="low",
        ),
        client=client,
    )
    return provider, client


def _timeout() -> APITimeoutError:
    return APITimeoutError(request=httpx.Request("POST", "https://api.openai.com/v1/responses"))


def _authentication(message: str = "authentication failed") -> AuthenticationError:
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(401, request=request)
    return AuthenticationError(message, response=response, body=None)


def _rate_limit() -> RateLimitError:
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(429, request=request)
    return RateLimitError("rate limited", response=response, body=None)


def _bad_request(*, code: str = "invalid_request_error") -> BadRequestError:
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    response = httpx.Response(400, request=request)
    return BadRequestError(
        "request rejected",
        response=response,
        body={"error": {"code": code}},
    )


@pytest.mark.anyio
async def test_all_openai_tasks_use_responses_structured_outputs(session: Session) -> None:
    context, _, scenario, _ = _seeded_context(session)
    mock = MockNarrativeProvider()
    branch_request = UniverseBranchRequest(
        profile=context.profile,
        decision_question=scenario.decision_question,
        scenario_seed=scenario.seed,
        simulation_mode=scenario.simulation_mode,
    )
    branches = await mock.generate_universe_branches(branch_request)
    event = await mock.generate_significant_event(context)
    completed = _completed_context(context, event)
    summary = await mock.generate_year_summary(completed, event)
    artifact = await mock.generate_artifact(completed, event, ArtifactType.DIARY_ENTRY)
    profile = await mock.generate_future_self_profile(completed)
    reply_request = FutureSelfReplyRequest(
        context=completed,
        profile=profile,
        message="What changed your life most?",
    )
    reply = await mock.generate_future_self_response(reply_request)
    provider, client = _provider(
        [
            FakeResponse(GeneratedUniverseBranches(branches=list(branches))),
            FakeResponse(event),
            FakeResponse(summary),
            FakeResponse(artifact),
            FakeResponse(profile),
            FakeResponse(reply),
        ]
    )

    assert len(await provider.generate_universe_branches(branch_request)) == 3
    assert await provider.generate_significant_event(context) == event
    assert await provider.generate_year_summary(completed, event) == summary
    assert await provider.generate_artifact(completed, event, ArtifactType.DIARY_ENTRY) == artifact
    assert await provider.generate_future_self_profile(completed) == profile
    assert await provider.generate_future_self_response(reply_request) == reply

    assert len(client.responses.calls) == 6
    assert len({call["instructions"] for call in client.responses.calls}) == 6
    assert all(call["store"] is False for call in client.responses.calls)
    assert all(call["truncation"] == "disabled" for call in client.responses.calls)
    assert all(call["model"] == "test-model" for call in client.responses.calls)
    assert all(call["text_format"] is not None for call in client.responses.calls)
    assert all(call["reasoning"] == {"effort": "low"} for call in client.responses.calls)
    assert all(call["verbosity"] == "low" for call in client.responses.calls)
    assert [call["max_output_tokens"] for call in client.responses.calls] == list(
        OUTPUT_TOKEN_BUDGETS.values()
    )


@pytest.mark.anyio
async def test_invalid_schema_and_oversized_output_are_rejected(session: Session) -> None:
    context, _, _, _ = _seeded_context(session)
    provider, _ = _provider([FakeResponse({"title": "missing required fields"})])
    with pytest.raises(NarrativeProviderInvalidOutputError):
        await provider.generate_significant_event(context)

    event = await MockNarrativeProvider().generate_significant_event(context)
    oversized, _ = _provider([FakeResponse(event, "x" * 30_001)])
    with pytest.raises(NarrativeProviderInvalidOutputError):
        await oversized.generate_significant_event(context)


@pytest.mark.anyio
async def test_openai_branches_must_preserve_custom_directions(session: Session) -> None:
    context, _, scenario, _ = _seeded_context(session)
    request = UniverseBranchRequest(
        profile=context.profile,
        decision_question=scenario.decision_question,
        scenario_seed=scenario.seed,
        simulation_mode=scenario.simulation_mode,
        branch_directions=["Study", "Career", "Create"],
    )
    branches = list(await MockNarrativeProvider().generate_universe_branches(request))
    branches[0] = branches[0].model_copy(update={"starting_direction": "Unrelated"})
    provider, _ = _provider([FakeResponse(GeneratedUniverseBranches(branches=branches))])

    with pytest.raises(NarrativeProviderInvalidOutputError):
        await provider.generate_universe_branches(request)


@pytest.mark.anyio
async def test_timeout_authentication_rate_limit_empty_and_bounded_retries(
    session: Session,
) -> None:
    context, _, _, _ = _seeded_context(session)

    timeout_provider, timeout_client = _provider([_timeout()])
    with pytest.raises(NarrativeProviderTimeoutError):
        await timeout_provider.generate_significant_event(context)
    assert len(timeout_client.responses.calls) == 1

    auth_provider, auth_client = _provider([_authentication()], retries=2)
    with pytest.raises(NarrativeProviderAuthenticationError):
        await auth_provider.generate_significant_event(context)
    assert len(auth_client.responses.calls) == 1

    rate_provider, rate_client = _provider([_rate_limit(), _rate_limit(), _rate_limit()], retries=2)
    with pytest.raises(NarrativeProviderRateLimitError):
        await rate_provider.generate_significant_event(context)
    assert len(rate_client.responses.calls) == 3

    empty_provider, empty_client = _provider(
        [FakeResponse(None, ""), FakeResponse(None, "")], retries=1
    )
    with pytest.raises(NarrativeProviderEmptyResponseError):
        await empty_provider.generate_significant_event(context)
    assert len(empty_client.responses.calls) == 2


@pytest.mark.anyio
async def test_unsupported_optional_control_retries_once_without_controls(
    session: Session,
) -> None:
    context, _, _, _ = _seeded_context(session)
    event = await MockNarrativeProvider().generate_significant_event(context)
    provider, client = _provider(
        [_bad_request(code="unsupported_parameter"), FakeResponse(event)], retries=2
    )

    assert await provider.generate_significant_event(context) == event
    assert len(client.responses.calls) == 2
    assert client.responses.calls[0]["reasoning"] == {"effort": "low"}
    assert client.responses.calls[0]["verbosity"] == "low"
    assert client.responses.calls[1]["reasoning"] is omit
    assert client.responses.calls[1]["verbosity"] is omit


@pytest.mark.anyio
async def test_other_bad_requests_are_not_retried(session: Session) -> None:
    context, _, _, _ = _seeded_context(session)
    provider, client = _provider([_bad_request()], retries=2)

    with pytest.raises(NarrativeProviderRequestError) as raised:
        await provider.generate_significant_event(context)

    assert raised.value.http_status == 400
    assert len(client.responses.calls) == 1


@pytest.mark.anyio
async def test_transient_failure_falls_back_to_deterministic_mock(session: Session) -> None:
    context, _, _, _ = _seeded_context(session)
    provider, client = _provider([_timeout()], fallback=True)

    event = await provider.generate_significant_event(context)

    assert event == await MockNarrativeProvider().generate_significant_event(context)
    assert provider.last_used_provider == "mock"
    assert len(client.responses.calls) == 1


@pytest.mark.anyio
async def test_future_self_reply_rejects_unstored_event_reference(session: Session) -> None:
    context, _, _, _ = _seeded_context(session)
    profile = await MockNarrativeProvider().generate_future_self_profile(context)
    request = FutureSelfReplyRequest(context=context, profile=profile, message="What happened?")
    invalid_reply = {
        "content": "A major event happened.",
        "referenced_event_keys": ["invented-event"],
        "tone": "reflective",
        "fictional_character": True,
    }
    provider, _ = _provider([FakeResponse(invalid_reply)])

    with pytest.raises(NarrativeProviderInvalidOutputError):
        await provider.generate_future_self_response(request)


def test_prompt_input_size_is_bounded() -> None:
    with pytest.raises(NarrativeInputTooLargeError):
        NarrativePrompt(instructions="i", input="x" * MAX_NARRATIVE_INPUT_CHARS).validate_size()


@pytest.mark.anyio
async def test_oversized_provider_input_never_calls_sdk_and_can_fallback(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    context, _, _, _ = _seeded_context(session)

    def oversized_prompt(_: NarrativeContext) -> NarrativePrompt:
        return NarrativePrompt(
            instructions="i", input="x" * MAX_NARRATIVE_INPUT_CHARS
        ).validate_size()

    monkeypatch.setattr(
        "app.services.narrative.openai.build_significant_event_prompt", oversized_prompt
    )
    unavailable, unavailable_client = _provider([])
    with pytest.raises(NarrativeProviderInputLimitError):
        await unavailable.generate_significant_event(context)
    assert unavailable_client.responses.calls == []

    fallback, fallback_client = _provider([], fallback=True)
    event = await fallback.generate_significant_event(context)
    assert event == await MockNarrativeProvider().generate_significant_event(context)
    assert fallback_client.responses.calls == []


def test_openai_configuration_repr_and_status_are_secret_free() -> None:
    secret = "sk-never-render-this"
    configuration = OpenAINarrativeConfiguration(api_key=secret, model="test-model")
    status = get_narrative_provider_status(
        "openai", has_api_key=False, model="", fallback_to_mock=True
    )

    assert secret not in repr(configuration)
    assert status.active_provider == "mock"
    assert status.state == "fallback"
    assert "key" not in status.detail.casefold()


@pytest.mark.anyio
async def test_future_self_prompt_keeps_only_recent_history(session: Session) -> None:
    context, _, _, _ = _seeded_context(session)
    profile = await MockNarrativeProvider().generate_future_self_profile(context)
    history = [
        FutureSelfMessage(
            role="user" if index % 2 == 0 else "future_self",
            content=f"history-{index}",
        )
        for index in range(12)
    ]
    prompt = build_future_self_reply_prompt(
        FutureSelfReplyRequest(
            context=context,
            profile=profile,
            message="What should I remember?",
            conversation_history=history,
        )
    )

    assert "history-3" not in prompt.input
    assert "history-4" in prompt.input
    assert "history-11" in prompt.input
    assert prompt.input.count("history-") == MAX_FUTURE_SELF_HISTORY_MESSAGES


@pytest.mark.anyio
async def test_prompts_send_only_task_relevant_context(session: Session) -> None:
    context, _, _, _ = _seeded_context(session)
    event = await MockNarrativeProvider().generate_significant_event(context)
    completed = _completed_context(context, event)

    event_prompt = build_significant_event_prompt(context)
    summary_prompt = build_year_summary_prompt(completed, event)
    artifact_prompt = build_artifact_prompt(completed, event, None)

    assert '"allowed_effect_fields"' in event_prompt.input
    assert '"previous_event_keys"' in event_prompt.input
    for prompt in (summary_prompt, artifact_prompt):
        assert '"allowed_effect_fields"' not in prompt.input
        assert '"previous_event_keys"' not in prompt.input
        assert '"automatic_effects"' not in prompt.input
        assert '"choices"' not in prompt.input


def test_optional_generation_controls_are_validated() -> None:
    configuration = OpenAINarrativeConfiguration(api_key="sk-test", model="test-model")

    assert configuration.reasoning_effort is None
    assert configuration.verbosity is None
    with pytest.raises(ValueError, match="reasoning effort"):
        OpenAINarrativeConfiguration(
            api_key="sk-test",
            model="test-model",
            reasoning_effort=cast(ReasoningEffort, "unbounded"),
        )
    with pytest.raises(ValueError, match="verbosity"):
        OpenAINarrativeConfiguration(
            api_key="sk-test",
            model="test-model",
            verbosity=cast(VerbosityLevel, "verbose"),
        )


def test_all_openai_output_schemas_avoid_dynamic_object_properties() -> None:
    schemas = (
        GeneratedUniverseBranches,
        GeneratedEvent,
        GeneratedYearSummary,
        GeneratedArtifact,
        GeneratedFutureSelfProfile,
        GeneratedFutureSelfReply,
    )

    def assert_closed(value: object) -> None:
        if isinstance(value, dict):
            additional_properties = value.get("additionalProperties")
            assert additional_properties is None or additional_properties is False
            for child in value.values():
                assert_closed(child)
        elif isinstance(value, list):
            for child in value:
                assert_closed(child)

    for schema in schemas:
        assert_closed(to_strict_json_schema(schema))


@pytest.mark.anyio
async def test_sanitized_logging_never_includes_error_message_or_secret(
    session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    context, _, _, _ = _seeded_context(session)
    secret = "sk-live-secret-profile-Hosein"
    provider, _ = _provider([_authentication(secret)])
    provider_logger = logging.getLogger("app.services.narrative.openai")
    provider_logger.disabled = False

    with (
        caplog.at_level(logging.WARNING, logger=provider_logger.name),
        pytest.raises(NarrativeProviderAuthenticationError),
    ):
        await provider.generate_significant_event(context)

    assert secret not in caplog.text
    assert context.profile.name not in caplog.text
    assert "authentication_failed" in caplog.text
    assert "http_status=401" in caplog.text
