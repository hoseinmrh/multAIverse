import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import app, create_app


@pytest.mark.anyio
async def test_health_endpoint() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Multiverse API",
        "version": "0.1.0",
    }


@pytest.mark.anyio
async def test_local_frontend_cors_preflight() -> None:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.anyio
async def test_public_provider_status_never_exposes_openai_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "sk-live-never-return-this"
    monkeypatch.setenv("NARRATIVE_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    monkeypatch.setenv("OPENAI_MODEL", "configured-model")
    monkeypatch.setenv("OPENAI_FALLBACK_TO_MOCK", "true")
    get_settings.cache_clear()
    application = create_app()
    try:
        async with AsyncClient(
            transport=ASGITransport(app=application), base_url="http://testserver"
        ) as client:
            response = await client.get("/api/v1/config/public")
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json()["narrative_provider_status"] == {
        "active_provider": "openai",
        "state": "configured",
        "model": "configured-model",
        "fallback_enabled": True,
        "detail": "OpenAI structured narrative generation is configured with mock fallback.",
    }
    assert secret not in response.text
    assert "api_key" not in response.text.casefold()


def test_openai_environment_settings_are_bounded_and_backend_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NARRATIVE_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-settings-test")
    monkeypatch.setenv("OPENAI_MODEL", "settings-model")
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "17.5")
    monkeypatch.setenv("OPENAI_MAX_RETRIES", "4")
    monkeypatch.setenv("OPENAI_FALLBACK_TO_MOCK", "false")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "low")
    monkeypatch.setenv("OPENAI_VERBOSITY", "low")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        assert settings.narrative_provider == "openai"
        assert settings.has_openai_api_key is True
        assert settings.openai_model == "settings-model"
        assert settings.openai_timeout_seconds == 17.5
        assert settings.openai_max_retries == 4
        assert settings.openai_fallback_to_mock is False
        assert settings.openai_reasoning_effort == "low"
        assert settings.openai_verbosity == "low"
        assert "sk-settings-test" not in repr(settings)
    finally:
        get_settings.cache_clear()
