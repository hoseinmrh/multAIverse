from dataclasses import dataclass
from typing import Literal

from app.services.narrative.mock import MockNarrativeProvider
from app.services.narrative.openai import (
    OpenAINarrativeConfiguration,
    OpenAINarrativeProvider,
    ReasoningEffort,
    VerbosityLevel,
)
from app.services.narrative.provider import NarrativeProvider


class NarrativeProviderConfigurationError(ValueError):
    """Raised for an unavailable provider without disclosing configuration values."""


@dataclass(frozen=True)
class NarrativeProviderStatus:
    requested_provider: Literal["mock", "openai"]
    active_provider: Literal["mock", "openai"] | None
    state: Literal["ready", "configured", "fallback", "unavailable"]
    model: str | None
    fallback_enabled: bool
    detail: str


def get_narrative_provider_status(
    provider_name: str,
    *,
    has_api_key: bool = False,
    model: str = "",
    fallback_to_mock: bool = True,
) -> NarrativeProviderStatus:
    normalized = provider_name.strip().casefold()
    if normalized == "mock":
        return NarrativeProviderStatus(
            requested_provider="mock",
            active_provider="mock",
            state="ready",
            model=None,
            fallback_enabled=False,
            detail="Offline deterministic narrative generation is ready.",
        )
    if normalized != "openai":
        raise NarrativeProviderConfigurationError("Unsupported narrative provider configuration")
    configured = has_api_key and bool(model.strip())
    if configured:
        return NarrativeProviderStatus(
            requested_provider="openai",
            active_provider="openai",
            state="configured",
            model=model.strip(),
            fallback_enabled=fallback_to_mock,
            detail=(
                "OpenAI structured narrative generation is configured with mock fallback."
                if fallback_to_mock
                else "OpenAI-only narrative generation is configured; failures preserve the "
                "current simulation state."
            ),
        )
    if fallback_to_mock:
        return NarrativeProviderStatus(
            requested_provider="openai",
            active_provider="mock",
            state="fallback",
            model=model.strip() or None,
            fallback_enabled=True,
            detail="OpenAI configuration is incomplete; the offline mock fallback is active.",
        )
    return NarrativeProviderStatus(
        requested_provider="openai",
        active_provider=None,
        state="unavailable",
        model=model.strip() or None,
        fallback_enabled=False,
        detail="OpenAI configuration is incomplete and mock fallback is disabled.",
    )


def create_narrative_provider(
    provider_name: str = "mock",
    *,
    api_key: str = "",
    model: str = "",
    timeout_seconds: float = 30,
    max_retries: int = 2,
    fallback_to_mock: bool = True,
    reasoning_effort: ReasoningEffort | None = None,
    verbosity: VerbosityLevel | None = None,
) -> NarrativeProvider:
    normalized = provider_name.strip().casefold()
    if normalized == "mock":
        return MockNarrativeProvider()
    if normalized != "openai":
        raise NarrativeProviderConfigurationError("Unsupported narrative provider configuration")
    if not api_key.strip() or not model.strip():
        if fallback_to_mock:
            return MockNarrativeProvider()
        raise NarrativeProviderConfigurationError(
            "OpenAI narrative generation is not fully configured"
        )
    return OpenAINarrativeProvider(
        OpenAINarrativeConfiguration(
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            fallback_to_mock=fallback_to_mock,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
        )
    )
