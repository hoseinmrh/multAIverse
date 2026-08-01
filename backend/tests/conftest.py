from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import build_engine


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
