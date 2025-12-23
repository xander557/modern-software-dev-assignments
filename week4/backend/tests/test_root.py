"""Tests for root endpoint."""

import pytest

pytestmark = pytest.mark.api


def test_root_endpoint_returns_json(client):
    """Test that root endpoint returns JSON when frontend disabled."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "status" in data
    assert data["status"] == "ok"
    assert data["message"] == "Modern Software Dev API"
