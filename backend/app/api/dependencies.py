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
    return CoreApplicationService(
        session,
        narrative_provider=create_narrative_provider(settings.narrative_provider),
    )


CoreServiceDependency = Annotated[CoreApplicationService, Depends(get_core_service)]
