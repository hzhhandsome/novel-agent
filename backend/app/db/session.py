from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


engine: Engine | None = None
SessionLocal = sessionmaker(autoflush=False, autocommit=False)


def get_engine() -> Engine:
    global engine
    if engine is None:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        SessionLocal.configure(bind=engine)
    return engine


def get_session() -> Generator[Session, None, None]:
    get_engine()
    with SessionLocal() as session:
        yield session
