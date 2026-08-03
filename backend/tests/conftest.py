from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi import FastAPI
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import build_engine, get_session
from app.main import create_app


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def db_engine(tmp_path: Path) -> Generator[Engine, None, None]:
    engine = build_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(db_engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=db_engine, class_=Session, expire_on_commit=False)


@pytest.fixture
def session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    with session_factory() as database_session:
        yield database_session


@pytest.fixture
def api_app(
    session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch
) -> Generator[FastAPI, None, None]:
    monkeypatch.setenv("NARRATIVE_PROVIDER", "mock")
    get_settings.cache_clear()
    application = create_app()

    def override_session() -> Generator[Session, None, None]:
        with session_factory() as database_session:
            yield database_session

    application.dependency_overrides[get_session] = override_session
    yield application
    get_settings.cache_clear()
