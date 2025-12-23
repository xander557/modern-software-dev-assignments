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
