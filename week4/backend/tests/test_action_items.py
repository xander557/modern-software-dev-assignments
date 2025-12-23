import pytest

pytestmark = pytest.mark.action_items


def test_create_and_complete_action_item(authenticated_client):
    """Test creating and completing action items."""
    payload = {"description": "Ship it"}
    r = authenticated_client.post("/action-items/", json=payload)
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["completed"] is False
    assert "user_id" in item

    r = authenticated_client.put(f"/action-items/{item['id']}/complete")
    assert r.status_code == 200
    done = r.json()
    assert done["completed"] is True

    r = authenticated_client.get("/action-items/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1


def test_action_items_require_authentication(client):
    """Test that action item endpoints require authentication."""
    r = client.get("/action-items/")
    assert r.status_code == 401

    r = client.post("/action-items/", json={"description": "Test"})
    assert r.status_code == 401


def test_action_item_user_isolation(client, test_user):
    """Test that users can only access their own action items."""
    # Create first user and action item
    client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    r = client.post("/action-items/", json={"description": "User1 Task"})
    item_id = r.json()["id"]

    # Logout and create second user
    client.post("/auth/logout")
    client.post("/auth/register", json={"username": "user2", "password": "pass2"})
    client.post("/auth/login", data={"username": "user2", "password": "pass2"})

    # Second user should not see or access first user's items
    r = client.get("/action-items/")
    assert len(r.json()) == 0

    # Second user cannot complete first user's item
    r = client.put(f"/action-items/{item_id}/complete")
    assert r.status_code == 404


def test_complete_action_item_not_found(authenticated_client):
    """Test completing non-existent action item returns 404."""
    response = authenticated_client.put("/action-items/99999/complete")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_action_item_missing_description(authenticated_client):
    """Test creating action item without description field."""
    response = authenticated_client.post("/action-items/", json={})
    assert response.status_code == 422


def test_list_action_items_empty(authenticated_client):
    """Test listing action items when user has none."""
    response = authenticated_client.get("/action-items/")
    assert response.status_code == 200
    assert response.json() == []


def test_complete_action_item_idempotency(authenticated_client):
    """Test that completing an already completed item is idempotent."""
    create_response = authenticated_client.post(
        "/action-items/", json={"description": "Task"}
    )
    item_id = create_response.json()["id"]

    # Complete once
    response1 = authenticated_client.put(f"/action-items/{item_id}/complete")
    assert response1.status_code == 200
    assert response1.json()["completed"] is True

    # Complete again - should still succeed
    response2 = authenticated_client.put(f"/action-items/{item_id}/complete")
    assert response2.status_code == 200
    assert response2.json()["completed"] is True


def test_list_action_items_shows_both_completed_and_incomplete(authenticated_client):
    """Test that listing shows both completed and incomplete items."""
    # Create two items
    r1 = authenticated_client.post("/action-items/", json={"description": "Task 1"})
    r2 = authenticated_client.post("/action-items/", json={"description": "Task 2"})

    # Complete one
    authenticated_client.put(f"/action-items/{r1.json()['id']}/complete")

    # List all
    response = authenticated_client.get("/action-items/")
    items = response.json()
    assert len(items) == 2
    assert any(item["completed"] for item in items)
    assert any(not item["completed"] for item in items)


def test_complete_action_item_wrong_user(client, test_user):
    """Test that users cannot complete other users' action items."""
    # Login as user1 and create action item
    client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    create_response = client.post("/action-items/", json={"description": "User1 Task"})
    item_id = create_response.json()["id"]

    # Logout and login as user2
    client.post("/auth/logout")
    client.post("/auth/register", json={"username": "user2", "password": "pass2"})
    client.post("/auth/login", data={"username": "user2", "password": "pass2"})

    # Try to complete user1's item
    response = client.put(f"/action-items/{item_id}/complete")
    assert response.status_code == 404
