from .conftest import login, make_admin, make_customer, register


def test_register_and_login_customer(client):
    r = register(client, "a@example.com")
    assert r.status_code == 201, r.text
    assert r.json()["role"] == "customer"
    headers = login(client, "a@example.com")
    r = client.get("/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "a@example.com"


def test_register_duplicate_email_rejected(client):
    assert register(client, "dup@example.com").status_code == 201
    assert register(client, "dup@example.com").status_code == 400


def test_login_wrong_password_rejected(client):
    register(client, "b@example.com")
    r = client.post("/auth/login-json", json={"email": "b@example.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_me_without_token_rejected(client):
    assert client.get("/auth/me").status_code == 401


def test_first_admin_allowed_second_admin_blocked(client):
    admin = make_admin(client)
    assert client.get("/auth/me", headers=admin).json()["role"] == "admin"
    # Second admin registration must be blocked once an admin exists.
    assert register(client, "admin2@agrimart.com", role="admin").status_code == 403


def test_customer_cannot_create_category(client):
    customer = make_customer(client)
    r = client.post("/categories", json={"name": "Fruit"}, headers=customer)
    assert r.status_code == 403
