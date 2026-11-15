def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_register_success(client):
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123!",
        "full_name": "Test User"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies

def test_register_duplicate_email(client):
    client.post("/api/auth/register", json={
        "email": "dup@example.com", "username": "user1", "password": "TestPass123!"
    })
    response = client.post("/api/auth/register", json={
        "email": "dup@example.com", "username": "user2", "password": "TestPass123!"
    })
    assert response.status_code == 400

def test_login_success(client):
    client.post("/api/auth/register", json={
        "email": "login@example.com", "username": "loginuser", "password": "TestPass123!"
    })
    response = client.post("/api/auth/login", json={
        "email": "login@example.com", "password": "TestPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in response.cookies

def test_login_wrong_password(client):
    client.post("/api/auth/register", json={
        "email": "wrong@example.com", "username": "wronguser", "password": "TestPass123!"
    })
    response = client.post("/api/auth/login", json={
        "email": "wrong@example.com", "password": "WrongPassword!"
    })
    assert response.status_code == 401

def test_get_profile(client):
    reg = client.post("/api/auth/register", json={
        "email": "profile@example.com", "username": "profileuser", "password": "TestPass123!"
    })
    token = reg.cookies.get("access_token")
    response = client.get("/api/student/profile", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "profile@example.com"
