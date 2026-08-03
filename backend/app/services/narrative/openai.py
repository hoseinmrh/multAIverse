import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Literal, TypeVar

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    RateLimitError,
    omit,
)
from pydantic import BaseModel, ValidationError

from app.models.enums import ArtifactType
from app.services.narrative.mock import MockNarrativeProvider
from app.services.narrative.prompts import (
    NarrativeInputTooLargeError,
    NarrativePrompt,
    build_artifact_prompt,
    build_future_self_profile_prompt,
    build_future_self_reply_prompt,
    build_significant_event_prompt,
    build_universe_branches_prompt,
    build_year_summary_prompt,
)
from app.services.narrative.schemas import (
    FutureSelfReplyRequest,
    GeneratedArtifact,
    GeneratedEvent,
    GeneratedFutureSelfProfile,
    GeneratedFutureSelfReply,
    GeneratedUniverseBranch,
    GeneratedUniverseBranches,
    GeneratedYearSummary,
    NarrativeContext,
    UniverseBranchRequest,
)

logger = logging.getLogger(__name__)

MAX_NARRATIVE_OUTPUT_CHARS = 30_000
OUTPUT_TOKEN_BUDGETS = {
    "universe_branches": 3_000,
    "significant_event": 2_200,
    "year_summary": 1_000,
    "artifact": 1_400,
    "future_self_profile": 900,
    "future_self_reply": 800,
}
type ReasoningEffort = Literal["none", "low", "medium", "high", "xhigh", "max"]
type VerbosityLevel = Literal["low", "medium", "high"]
REASONING_EFFORTS = {"none", "low", "medium", "high", "xhigh", "max"}
VERBOSITY_LEVELS = {"low", "medium", "high"}

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class NarrativeProviderError(RuntimeError):
    """Safe provider failure that never embeds prompts, profiles, or credentials."""

    code = "provider_error"
    retryable = False

    def __init__(self, operation: str, *, http_status: int | None = None) -> None:
        self.operation = operation
        self.http_status = http_status
        super().__init__(f"Narrative provider failed during {operation}")


class NarrativeProviderTimeoutError(NarrativeProviderError):
    code = "timeout"
    retryable = True


class NarrativeProviderRateLimitError(NarrativeProviderError):
    code = "rate_limited"
    retryable = True


class NarrativeProviderConnectionError(NarrativeProviderError):
    code = "connection_error"
    retryable = True


class NarrativeProviderAuthenticationError(NarrativeProviderError):
    code = "authentication_failed"


class NarrativeProviderRequestError(NarrativeProviderError):
    code = "request_rejected"


class NarrativeProviderInvalidOutputError(NarrativeProviderError):
    code = "invalid_output"
    retryable = True


class NarrativeProviderEmptyResponseError(NarrativeProviderError):
    code = "empty_response"
    retryable = True


class NarrativeProviderInputLimitError(NarrativeProviderError):
    code = "input_too_large"


@dataclass(frozen=True)
class OpenAINarrativeConfiguration:
    api_key: str = field(repr=False)
    model: str
    timeout_seconds: float = 30
    max_retries: int = 2
    fallback_to_mock: bool = True
    retry_base_seconds: float = 0.25
    reasoning_effort: ReasoningEffort | None = None
    verbosity: VerbosityLevel | None = None

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise ValueError("OpenAI credentials are required")
        if not self.model.strip():
            raise ValueError("OPENAI_MODEL is required")
        if not 0 < self.timeout_seconds <= 120:
            raise ValueError("OpenAI timeout must be between 0 and 120 seconds")
        if not 0 <= self.max_retries <= 5:
            raise ValueError("OpenAI retries must be between 0 and 5")
        if self.retry_base_seconds < 0:
            raise ValueError("Retry delay cannot be negative")
        if self.reasoning_effort is not None and self.reasoning_effort not in REASONING_EFFORTS:
            raise ValueError("Unsupported OpenAI reasoning effort")
        if self.verbosity is not None and self.verbosity not in VERBOSITY_LEVELS:
            raise ValueError("Unsupported OpenAI verbosity")


class OpenAINarrativeProvider:
    """Responses API adapter returning schema-validated narrative proposals only."""

    provider_name = "openai"

    def __init__(
        self,
        configuration: OpenAINarrativeConfiguration,
        *,
        client: Any | None = None,
        fallback_provider: MockNarrativeProvider | None = None,
    ) -> None:
        self.configuration = configuration
        self.client = client or AsyncOpenAI(
            api_key=configuration.api_key,
            timeout=configuration.timeout_seconds,
            max_retries=0,
        )
        self.fallback_provider = (
            fallback_provider
            if fallback_provider is not None
            else MockNarrativeProvider()
            if configuration.fallback_to_mock
            else None
        )
        self.last_used_provider = "openai"
        self.llm_only = self.fallback_provider is None

    async def generate_universe_branches(
        self, request: UniverseBranchRequest
    ) -> tuple[GeneratedUniverseBranch, ...]:
        result = await self._generate(
            "universe_branches",
            lambda: build_universe_branches_prompt(request),
            GeneratedUniverseBranches,
            fallback=lambda: self._mock_branches(request),
            validate=lambda output: self._validate_branches(output, request),
        )
        return tuple(result.branches)

    async def generate_significant_event(self, context: NarrativeContext) -> GeneratedEvent:
        result = await self._generate(
            "significant_event",
            lambda: build_significant_event_prompt(context),
            GeneratedEvent,
            fallback=lambda: (
                self.fallback_provider.generate_significant_event(context)
                if self.fallback_provider
                else self._no_fallback()
            ),
            validate=lambda output: self._validate_event(output, context),
        )
        return result

    async def generate_year_summary(
        self, context: NarrativeContext, event: GeneratedEvent
    ) -> GeneratedYearSummary:
        result = await self._generate(
            "year_summary",
            lambda: build_year_summary_prompt(context, event),
            GeneratedYearSummary,
            fallback=lambda: (
                self.fallback_provider.generate_year_summary(context, event)
                if self.fallback_provider
                else self._no_fallback()
            ),
            validate=lambda output: self._validate_summary(output, context),
        )
        return result

    async def generate_artifact(
        self,
        context: NarrativeContext,
        event: GeneratedEvent,
        artifact_type: ArtifactType | None = None,
    ) -> GeneratedArtifact:
        result = await self._generate(
            "artifact",
            lambda: build_artifact_prompt(context, event, artifact_type),
            GeneratedArtifact,
            fallback=lambda: (
                self.fallback_provider.generate_artifact(context, event, artifact_type)
                if self.fallback_provider
                else self._no_fallback()
            ),
            validate=lambda output: self._validate_artifact(output, event, artifact_type),
        )
        return result

    async def generate_future_self_profile(
        self, context: NarrativeContext
    ) -> GeneratedFutureSelfProfile:
        result = await self._generate(
            "future_self_profile",
            lambda: build_future_self_profile_prompt(context),
            GeneratedFutureSelfProfile,
            fallback=lambda: (
                self.fallback_provider.generate_future_self_profile(context)
                if self.fallback_provider
                else self._no_fallback()
            ),
            validate=lambda output: self._validate_future_profile(output, context),
        )
        return result

    async def generate_future_self_response(
        self, request: FutureSelfReplyRequest
    ) -> GeneratedFutureSelfReply:
        result = await self._generate(
            "future_self_reply",
            lambda: build_future_self_reply_prompt(request),
            GeneratedFutureSelfReply,
            fallback=lambda: (
                self.fallback_provider.generate_future_self_response(request)
                if self.fallback_provider
                else self._no_fallback()
            ),
            validate=lambda output: self._validate_future_reply(output, request),
        )
        return result

    async def _mock_branches(self, request: UniverseBranchRequest) -> GeneratedUniverseBranches:
        if self.fallback_provider is None:
            return await self._no_fallback()
        branches = await self.fallback_provider.generate_universe_branches(request)
        return GeneratedUniverseBranches(branches=list(branches))

    async def _no_fallback[ResultT](self) -> ResultT:
        raise NarrativeProviderError("fallback")

    async def _generate(
        self,
        operation: str,
        prompt_builder: Callable[[], NarrativePrompt],
        schema: type[SchemaT],
        *,
        fallback: Callable[[], Awaitable[SchemaT]],
        validate: Callable[[SchemaT], None] | None = None,
    ) -> SchemaT:
        try:
            prompt = prompt_builder()
        except NarrativeInputTooLargeError as error:
            limit_error = NarrativeProviderInputLimitError(operation)
            logger.warning(
                "Narrative provider input rejected operation=%s category=%s",
                operation,
                limit_error.code,
            )
            if self.fallback_provider is None:
                raise limit_error from error
            result = await fallback()
            if validate is not None:
                validate(result)
            self.last_used_provider = "mock"
            return result

        last_error: NarrativeProviderError | None = None
        total_attempts = self.configuration.max_retries + 1
        use_optional_controls = bool(
            self.configuration.reasoning_effort or self.configuration.verbosity
        )
        for attempt in range(1, total_attempts + 1):
            retry_without_optional_controls = False
            try:
                response = await self.client.responses.parse(
                    model=self.configuration.model,
                    instructions=prompt.instructions,
                    input=[{"role": "user", "content": prompt.input}],
                    text_format=schema,
                    max_output_tokens=OUTPUT_TOKEN_BUDGETS[operation],
                    store=False,
                    truncation="disabled",
                    timeout=self.configuration.timeout_seconds,
                    reasoning=(
                        {"effort": self.configuration.reasoning_effort}
                        if use_optional_controls and self.configuration.reasoning_effort is not None
                        else omit
                    ),
                    verbosity=(
                        self.configuration.verbosity
                        if use_optional_controls and self.configuration.verbosity is not None
                        else omit
                    ),
                )
                result = self._validated_output(response, schema, operation)
                if validate is not None:
                    validate(result)
                self.last_used_provider = "openai"
                return result
            except NarrativeProviderError as error:
                last_error = error
            except ValidationError as error:
                last_error = NarrativeProviderInvalidOutputError(operation)
                last_error.__cause__ = error
            except Exception as error:
                retry_without_optional_controls = (
                    use_optional_controls and self._is_optional_control_compatibility_error(error)
                )
                last_error = self._classify_error(error, operation)

            logger.warning(
                "Narrative provider request failed operation=%s attempt=%d/%d category=%s "
                "retryable=%s http_status=%s",
                operation,
                attempt,
                total_attempts,
                last_error.code,
                last_error.retryable or retry_without_optional_controls,
                last_error.http_status,
            )
            if attempt == total_attempts:
                break
            if retry_without_optional_controls:
                use_optional_controls = False
            elif not last_error.retryable:
                break
            if self.configuration.retry_base_seconds:
                await asyncio.sleep(self.configuration.retry_base_seconds * 2 ** (attempt - 1))

        if self.fallback_provider is not None:
            logger.warning(
                "Narrative provider using mock fallback operation=%s category=%s",
                operation,
                last_error.code if last_error else "provider_error",
            )
            result = await fallback()
            if validate is not None:
                validate(result)
            self.last_used_provider = "mock"
            return result
        raise last_error or NarrativeProviderError(operation)

    @staticmethod
    def _validated_output(response: object, schema: type[SchemaT], operation: str) -> SchemaT:
        output_text = getattr(response, "output_text", "")
        if isinstance(output_text, str) and len(output_text) > MAX_NARRATIVE_OUTPUT_CHARS:
            raise NarrativeProviderInvalidOutputError(operation)
        parsed = getattr(response, "output_parsed", None)
        if parsed is None:
            raise NarrativeProviderEmptyResponseError(operation)
        payload = parsed.model_dump(mode="python") if isinstance(parsed, BaseModel) else parsed
        result = schema.model_validate(payload)
        if len(result.model_dump_json()) > MAX_NARRATIVE_OUTPUT_CHARS:
            raise NarrativeProviderInvalidOutputError(operation)
        return result

    @staticmethod
    def _classify_error(error: Exception, operation: str) -> NarrativeProviderError:
        if isinstance(error, APITimeoutError):
            return NarrativeProviderTimeoutError(operation)
        if isinstance(error, RateLimitError):
            return NarrativeProviderRateLimitError(operation, http_status=error.status_code)
        if isinstance(error, AuthenticationError):
            return NarrativeProviderAuthenticationError(operation, http_status=error.status_code)
        if isinstance(error, APIConnectionError):
            return NarrativeProviderConnectionError(operation)
        if isinstance(error, APIStatusError):
            if error.status_code == 429:
                return NarrativeProviderRateLimitError(operation, http_status=error.status_code)
            if error.status_code in {408, 409} or error.status_code >= 500:
                return NarrativeProviderConnectionError(operation, http_status=error.status_code)
            if error.status_code in {401, 403}:
                return NarrativeProviderAuthenticationError(
                    operation, http_status=error.status_code
                )
            return NarrativeProviderRequestError(operation, http_status=error.status_code)
        return NarrativeProviderError(operation)

    @staticmethod
    def _is_optional_control_compatibility_error(error: Exception) -> bool:
        if not isinstance(error, APIStatusError) or error.status_code != 400:
            return False
        body = error.body if isinstance(error.body, dict) else {}
        detail = body.get("error", body)
        if not isinstance(detail, dict):
            return False
        return detail.get("code") == "unsupported_parameter"

    @staticmethod
    def _validate_branches(
        result: GeneratedUniverseBranches, request: UniverseBranchRequest
    ) -> None:
        if len(result.branches) != request.number_of_branches:
            raise NarrativeProviderInvalidOutputError("universe_branches")
        if len({branch.slug for branch in result.branches}) != len(result.branches):
            raise NarrativeProviderInvalidOutputError("universe_branches")
        if (
            request.branch_directions
            and [branch.starting_direction for branch in result.branches]
            != request.branch_directions
        ):
            raise NarrativeProviderInvalidOutputError("universe_branches")

    @staticmethod
    def _validate_event(result: GeneratedEvent, context: NarrativeContext) -> None:
        if result.year != context.current_year + 1:
            raise NarrativeProviderInvalidOutputError("significant_event")
        if result.event_key in set(context.previous_event_keys):
            raise NarrativeProviderInvalidOutputError("significant_event")

    @staticmethod
    def _validate_summary(result: GeneratedYearSummary, context: NarrativeContext) -> None:
        if result.year != context.current_year:
            raise NarrativeProviderInvalidOutputError("year_summary")

    @staticmethod
    def _validate_artifact(
        result: GeneratedArtifact,
        event: GeneratedEvent,
        artifact_type: ArtifactType | None,
    ) -> None:
        if result.metadata.event_key != event.event_key:
            raise NarrativeProviderInvalidOutputError("artifact")
        if artifact_type is not None and result.artifact_type != artifact_type:
            raise NarrativeProviderInvalidOutputError("artifact")

    @staticmethod
    def _validate_future_profile(
        result: GeneratedFutureSelfProfile, context: NarrativeContext
    ) -> None:
        expected = (
            context.profile.name,
            context.current_state.age,
            context.current_state.location,
            context.current_state.career_title,
            context.universe.name,
            context.current_state.happiness,
            context.current_state.stress,
        )
        actual = (
            result.name,
            result.age,
            result.location,
            result.occupation,
            result.universe,
            result.happiness,
            result.stress,
        )
        if actual != expected:
            raise NarrativeProviderInvalidOutputError("future_self_profile")

    @staticmethod
    def _validate_future_reply(
        result: GeneratedFutureSelfReply, request: FutureSelfReplyRequest
    ) -> None:
        allowed_keys = set(request.context.previous_event_keys)
        allowed_keys.update(event.event_key for event in request.context.last_major_events)
        if not set(result.referenced_event_keys).issubset(allowed_keys):
            raise NarrativeProviderInvalidOutputError("future_self_reply")
