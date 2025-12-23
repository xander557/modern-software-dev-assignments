import os
import tempfile
from collections.abc import Generator

# Disable static files before importing the app
os.environ["ENABLE_STATIC_FILES"] = "false"

import pytest
from backend.app.db import get_db
from backend.app.main import app
from backend.app.models import Base
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    db_fd, db_path = tempfile.mkstemp()
    os.close(db_fd)

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    os.unlink(db_path)


@pytest.fixture()
def test_user(client: TestClient) -> dict:
    """Create a test user and return credentials."""
    username = "testuser"
    password = "testpass123"

    # Register user
    response = client.post(
        "/auth/register",
        json={"username": username, "password": password},
    )
    assert response.status_code == 201

    return {"username": username, "password": password, "id": response.json()["id"]}


@pytest.fixture()
def authenticated_client(client: TestClient, test_user: dict) -> TestClient:
    """Return a client with authentication cookie set."""
    # Login
    response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert response.status_code == 200

    return client


# ============================================================================
# Multi-User Fixtures
# ============================================================================


@pytest.fixture()
def multiple_users(client: TestClient) -> list[dict]:
    """Create multiple test users for isolation testing."""
    users = [
        {"username": "user1", "password": "pass1"},
        {"username": "user2", "password": "pass2"},
        {"username": "user3", "password": "pass3"},
    ]
    created_users = []
    for user in users:
        response = client.post("/auth/register", json=user)
        assert response.status_code == 201
        user_data = response.json()
        created_users.append(
            {
                "id": user_data["id"],
                "username": user["username"],
                "password": user["password"],
            }
        )
    return created_users


# ============================================================================
# Note Fixtures
# ============================================================================


@pytest.fixture()
def sample_notes(authenticated_client: TestClient) -> list[dict]:
    """Create sample notes for testing."""
    notes_data = [
        {"title": "Meeting Notes", "content": "Discuss Q4 planning"},
        {"title": "Todo List", "content": "TODO: Review code\n- Ship feature!"},
        {"title": "Research", "content": "Look into FastAPI performance"},
        {"title": "Ideas", "content": "New feature brainstorming"},
    ]
    created_notes = []
    for note_data in notes_data:
        response = authenticated_client.post("/notes/", json=note_data)
        assert response.status_code == 201
        created_notes.append(response.json())
    return created_notes


@pytest.fixture()
def note_factory(authenticated_client: TestClient):
    """Factory fixture for creating notes with custom data."""

    def _create_note(title: str = "Test Note", content: str = "Test content") -> dict:
        response = authenticated_client.post(
            "/notes/", json={"title": title, "content": content}
        )
        assert response.status_code == 201
        return response.json()

    return _create_note


# ============================================================================
# Action Item Fixtures
# ============================================================================


@pytest.fixture()
def sample_action_items(authenticated_client: TestClient) -> list[dict]:
    """Create sample action items for testing."""
    items_data = [
        {"description": "TODO: Write documentation"},
        {"description": "Ship the new feature!"},
        {"description": "Review pull requests"},
        {"description": "Update dependencies"},
    ]
    created_items = []
    for item_data in items_data:
        response = authenticated_client.post("/action-items/", json=item_data)
        assert response.status_code == 201
        created_items.append(response.json())
    return created_items


@pytest.fixture()
def action_item_factory(authenticated_client: TestClient):
    """Factory fixture for creating action items with custom data."""

    def _create_action_item(
        description: str = "Test task", complete: bool = False
    ) -> dict:
        response = authenticated_client.post(
            "/action-items/", json={"description": description}
        )
        assert response.status_code == 201
        item = response.json()

        if complete:
            response = authenticated_client.put(f"/action-items/{item['id']}/complete")
            assert response.status_code == 200
            item = response.json()

        return item

    return _create_action_item
