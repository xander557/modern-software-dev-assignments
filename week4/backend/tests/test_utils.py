"""Test utilities and helper functions."""

from typing import Any


def assert_valid_note_schema(data: dict[str, Any]) -> None:
    """Assert that data matches NoteRead schema."""
    assert "id" in data and isinstance(data["id"], int)
    assert "title" in data and isinstance(data["title"], str)
    assert "content" in data and isinstance(data["content"], str)
    assert "user_id" in data and isinstance(data["user_id"], int)


def assert_valid_action_item_schema(data: dict[str, Any]) -> None:
    """Assert that data matches ActionItemRead schema."""
    assert "id" in data and isinstance(data["id"], int)
    assert "description" in data and isinstance(data["description"], str)
    assert "completed" in data and isinstance(data["completed"], bool)
    assert "user_id" in data and isinstance(data["user_id"], int)


def assert_valid_user_schema(data: dict[str, Any]) -> None:
    """Assert that data matches UserRead schema."""
    assert "id" in data and isinstance(data["id"], int)
    assert "username" in data and isinstance(data["username"], str)
    # Password should never be exposed
    assert "password" not in data
    assert "hashed_password" not in data
