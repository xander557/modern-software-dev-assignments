import pytest

pytestmark = pytest.mark.auth


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/auth/register",
        json={"username": "newuser", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data


def test_register_duplicate_username(client, test_user):
    """Test registration with duplicate username fails."""
    response = client.post(
        "/auth/register",
        json={"username": test_user["username"], "password": "different"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user["username"]
    assert "access_token" in response.cookies


def test_login_wrong_password(client, test_user):
    """Test login with wrong password."""
    response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """Test login with nonexistent user."""
    response = client.post(
        "/auth/login",
        data={"username": "nonexistent", "password": "password"},
    )
    assert response.status_code == 401


def test_get_current_user(authenticated_client):
    """Test getting current user info."""
    response = authenticated_client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert "username" in data


def test_get_current_user_unauthenticated(client):
    """Test getting current user without authentication."""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_logout(authenticated_client):
    """Test logout."""
    response = authenticated_client.post("/auth/logout")
    assert response.status_code == 200

    # Verify we can't access protected routes after logout
    response = authenticated_client.get("/auth/me")
    assert response.status_code == 401


def test_register_empty_username(client):
    """Test registration with empty username."""
    response = client.post(
        "/auth/register", json={"username": "", "password": "pass123"}
    )
    assert response.status_code == 422


def test_register_empty_password(client):
    """Test registration with empty password."""
    response = client.post(
        "/auth/register", json={"username": "user", "password": ""}
    )
    assert response.status_code == 422


def test_register_missing_username(client):
    """Test registration without username field."""
    response = client.post("/auth/register", json={"password": "pass123"})
    assert response.status_code == 422


def test_register_missing_password(client):
    """Test registration without password field."""
    response = client.post("/auth/register", json={"username": "user"})
    assert response.status_code == 422


def test_logout_when_not_logged_in(client):
    """Test logout when not authenticated."""
    response = client.post("/auth/logout")
    assert response.status_code == 200


def test_get_current_user_response_schema(authenticated_client, test_user):
    """Test that /auth/me returns correct schema."""
    response = authenticated_client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert data["username"] == test_user["username"]
    # Password should never be exposed
    assert "password" not in data
    assert "hashed_password" not in data
