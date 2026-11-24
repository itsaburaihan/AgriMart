import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def register(client, email, password="password123", role="customer", name="Test User"):
    return client.post("/auth/register", json={"name": name, "email": email, "password": password, "role": role})


def login(client, email, password="password123"):
    r = client.post("/auth/login-json", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_admin(client):
    r = register(client, "admin@agrimart.com", role="admin", name="Farmer")
    assert r.status_code == 201, r.text
    return login(client, "admin@agrimart.com")


def make_customer(client, email="customer@agrimart.com"):
    r = register(client, email, name="Customer")
    assert r.status_code == 201, r.text
    return login(client, email)


def make_category(client, admin_headers, name="Vegetables"):
    r = client.post("/categories", json={"name": name, "description": "Fresh veg"}, headers=admin_headers)
    assert r.status_code == 201, r.text
    return r.json()


def make_product(client, admin_headers, category_id, name="Tomato", price="120.00", stock=50):
    r = client.post(
        "/products",
        json={"name": name, "description": "Fresh", "price": price, "unit": "kg", "stock": stock, "category_id": category_id},
        headers=admin_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()
