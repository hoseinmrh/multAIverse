from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_session
from app.services.application import CoreApplicationService
from app.services.narrative import create_narrative_provider

SessionDependency = Annotated[Session, Depends(get_session)]


def get_core_service(session: SessionDependency) -> CoreApplicationService:
    settings = get_settings()
    api_key = (
        settings.openai_api_key.get_secret_value() if settings.openai_api_key is not None else ""
    )
    return CoreApplicationService(
        session,
        narrative_provider=create_narrative_provider(
            settings.narrative_provider,
            api_key=api_key,
            model=settings.openai_model,
            timeout_seconds=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
            fallback_to_mock=settings.openai_fallback_to_mock,
            reasoning_effort=settings.openai_reasoning_effort,
            verbosity=settings.openai_verbosity,
        ),
    )


CoreServiceDependency = Annotated[CoreApplicationService, Depends(get_core_service)]
