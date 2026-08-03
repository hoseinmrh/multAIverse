from app.services.narrative.mock import MockNarrativeProvider
from app.services.narrative.provider import NarrativeProvider


class NarrativeProviderConfigurationError(ValueError):
    """Raised when a provider that is unavailable in the current phase is requested."""


def create_narrative_provider(provider_name: str = "mock") -> NarrativeProvider:
    normalized = provider_name.strip().casefold()
    if normalized == "mock":
        return MockNarrativeProvider()
    raise NarrativeProviderConfigurationError(
        f"Unsupported narrative provider {provider_name!r}; Phase 4 supports 'mock' only"
    )
