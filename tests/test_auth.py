from app.utils import hash_password, verify_password

def test_password_hashing():
    pwd = "secretpassword123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_login_success(client):
    response = client.post(
        "/login",
        data={"username": "testadmin", "password": "admin123"},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/dashboard"

def test_login_fail(client):
    response = client.post(
        "/login",
        data={"username": "testadmin", "password": "wrongpassword"},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

def test_logout(client):
    response = client.get("/logout", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
