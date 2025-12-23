def test_create_and_list_notes(authenticated_client):
    """Test creating and listing notes."""
    payload = {"title": "Test", "content": "Hello world"}
    r = authenticated_client.post("/notes/", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Test"
    assert "user_id" in data

    r = authenticated_client.get("/notes/")
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1

    r = authenticated_client.get("/notes/search/")
    assert r.status_code == 200

    r = authenticated_client.get("/notes/search/", params={"q": "Hello"})
    assert r.status_code == 200
    items = r.json()
    assert len(items) >= 1


def test_notes_require_authentication(client):
    """Test that notes endpoints require authentication."""
    r = client.get("/notes/")
    assert r.status_code == 401

    r = client.post("/notes/", json={"title": "Test", "content": "Test"})
    assert r.status_code == 401


def test_user_isolation(client, test_user):
    """Test that users can only see their own notes."""
    # Create first user and note
    client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    client.post("/notes/", json={"title": "User1 Note", "content": "Private"})

    # Get notes for first user
    r = client.get("/notes/")
    user1_notes = r.json()
    assert len(user1_notes) == 1

    # Logout and create second user
    client.post("/auth/logout")
    client.post("/auth/register", json={"username": "user2", "password": "pass2"})
    client.post("/auth/login", data={"username": "user2", "password": "pass2"})

    # Second user should not see first user's notes
    r = client.get("/notes/")
    user2_notes = r.json()
    assert len(user2_notes) == 0

    # Create note for second user
    client.post("/notes/", json={"title": "User2 Note", "content": "Also private"})
    r = client.get("/notes/")
    user2_notes = r.json()
    assert len(user2_notes) == 1
    assert user2_notes[0]["title"] == "User2 Note"
