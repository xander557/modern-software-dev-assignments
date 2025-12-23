import pytest

pytestmark = pytest.mark.notes


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


def test_get_note_by_id_success(authenticated_client):
    """Test retrieving a specific note by ID."""
    create_response = authenticated_client.post(
        "/notes/", json={"title": "Test Note", "content": "Test content"}
    )
    note_id = create_response.json()["id"]

    response = authenticated_client.get(f"/notes/{note_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Test Note"
    assert data["content"] == "Test content"
    assert "user_id" in data


def test_get_note_not_found(authenticated_client):
    """Test retrieving non-existent note returns 404."""
    response = authenticated_client.get("/notes/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_note_requires_authentication(client):
    """Test that getting a note requires authentication."""
    response = client.get("/notes/1")
    assert response.status_code == 401


def test_get_note_wrong_user(client, test_user):
    """Test that users cannot access other users' notes."""
    # Login as user1 and create a note
    client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    create_response = client.post("/notes/", json={"title": "Private", "content": "Data"})
    note_id = create_response.json()["id"]

    # Logout and login as user2
    client.post("/auth/logout")
    client.post("/auth/register", json={"username": "user2", "password": "pass2"})
    client.post("/auth/login", data={"username": "user2", "password": "pass2"})

    # User2 should not see user1's note
    response = client.get(f"/notes/{note_id}")
    assert response.status_code == 404


def test_search_notes_no_matches(authenticated_client, sample_notes):
    """Test search with no matches returns empty list."""
    response = authenticated_client.get("/notes/search/", params={"q": "nonexistent"})
    assert response.status_code == 200
    assert response.json() == []


def test_create_note_missing_fields(authenticated_client):
    """Test creating note with missing required fields."""
    response = authenticated_client.post("/notes/", json={"title": "Only title"})
    assert response.status_code == 422


def test_list_notes_empty(authenticated_client):
    """Test listing notes when user has none."""
    response = authenticated_client.get("/notes/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_note_invalid_id_type(authenticated_client):
    """Test that invalid ID types return 422 validation error."""
    response = authenticated_client.get("/notes/invalid")
    assert response.status_code == 422
