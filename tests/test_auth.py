def test_register_user_success(client):
    res = client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "securepassword123"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "newuser@example.com"
    assert data["role"] == "user"
    assert "id" in data


def test_register_duplicate_email(client):
    client.post(
        "/auth/register",
        json={"email": "dupuser@example.com", "password": "password123"},
    )
    res = client.post(
        "/auth/register",
        json={"email": "dupuser@example.com", "password": "password123"},
    )
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"].lower()


def test_login_success(client):
    client.post(
        "/auth/register",
        json={"email": "loginuser@example.com", "password": "correctpassword"},
    )
    res = client.post(
        "/auth/login",
        json={"email": "loginuser@example.com", "password": "correctpassword"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    client.post(
        "/auth/register",
        json={"email": "validuser@example.com", "password": "correctpassword"},
    )
    res = client.post(
        "/auth/login",
        json={"email": "validuser@example.com", "password": "wrongpassword"},
    )
    assert res.status_code == 401


def test_refresh_token_flow(client):
    client.post(
        "/auth/register",
        json={"email": "refreshuser@example.com", "password": "password123"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "refreshuser@example.com", "password": "password123"},
    ).json()
    refresh_token = login_res["refresh_token"]

    res = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_get_me_profile(client):
    client.post(
        "/auth/register",
        json={"email": "meuser@example.com", "password": "password123"},
    )
    login_res = client.post(
        "/auth/login",
        json={"email": "meuser@example.com", "password": "password123"},
    ).json()
    token = login_res["access_token"]

    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "meuser@example.com"
