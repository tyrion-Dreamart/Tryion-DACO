async def test_login_success(client, test_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "testpass123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["access_token"]
    assert body["refresh_token"]


async def test_login_wrong_password(client, test_user):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "not-the-password"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email(client):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nadie@example.com", "password": "whatever"},
    )
    assert resp.status_code == 401


async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_with_valid_token(client, auth_headers, test_user):
    resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == test_user.email
