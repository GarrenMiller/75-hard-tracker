def test_register(auth):
    assert auth["user"]["email"] == "user@example.com"
    assert auth["token"]


def test_register_requires_valid_email(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": "not-an-email", "password": "password123", "display_name": "X"},
    )
    assert resp.status_code == 400
    assert "email" in resp.get_json()["error"].lower()


def test_register_requires_password_length(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": "a@b.com", "password": "short", "display_name": "X"},
    )
    assert resp.status_code == 400


def test_register_requires_display_name(client):
    resp = client.post(
        "/api/auth/register",
        json={"email": "a@b.com", "password": "password123", "display_name": ""},
    )
    assert resp.status_code == 400


def test_register_duplicate_email(client, auth):
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "user@example.com",
            "password": "password123",
            "display_name": "Someone Else",
        },
    )
    assert resp.status_code == 409


def test_login_success(client, auth):
    resp = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["token"]


def test_login_wrong_password(client, auth):
    resp = client.post(
        "/api/auth/login",
        json={"email": "user@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401


def test_me(client, auth):
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {auth['token']}"})
    assert resp.status_code == 200
    assert resp.get_json()["user"]["id"] == auth["user"]["id"]


def test_me_requires_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout_invalidates_token(client, auth):
    headers = {"Authorization": f"Bearer {auth['token']}"}
    resp = client.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 200
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 401
