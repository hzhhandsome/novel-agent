from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_session
from app.main import create_app


def test_create_project_returns_first_chapters():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    testing_session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    app = create_app()

    def override_session():
        with testing_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    client = TestClient(app)

    response = client.post(
        "/api/projects",
        json={"idea": "一个失忆修书人在废城里修补会改变现实的书"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["idea"].startswith("一个失忆修书人")
    assert len(body["chapters"]) >= 3
