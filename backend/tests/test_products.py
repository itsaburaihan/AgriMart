from .conftest import make_admin, make_category, make_customer, make_product


def test_product_crud_and_search(client):
    admin = make_admin(client)
    cat = make_category(client, admin)
    product = make_product(client, admin, cat["id"], name="Tomato", price="120.00")

    # Public list + search
    r = client.get("/products")
    assert r.status_code == 200 and len(r.json()) == 1
    assert client.get("/products", params={"q": "tom"}).json()[0]["name"] == "Tomato"
    assert client.get("/products", params={"q": "potato"}).json() == []
    assert client.get("/products", params={"category_id": cat["id"]}).json()[0]["id"] == product["id"]

    # Update price/stock, then delete
    r = client.put(f"/products/{product['id']}", json={"price": "150.00", "stock": 30}, headers=admin)
    assert r.status_code == 200 and r.json()["price"] == "150.00" and r.json()["stock"] == 30
    assert client.delete(f"/products/{product['id']}", headers=admin).status_code == 204
    assert client.get(f"/products/{product['id']}").status_code == 404


def test_product_create_requires_admin_and_valid_category(client):
    admin = make_admin(client)
    customer = make_customer(client)
    cat = make_category(client, admin)
    payload = {"name": "Rice", "price": "80.00", "unit": "kg", "stock": 10, "category_id": cat["id"]}
    assert client.post("/products", json=payload, headers=customer).status_code == 403
    assert client.post("/products", json={**payload, "category_id": 9999}, headers=admin).status_code == 400


def test_category_crud(client):
    admin = make_admin(client)
    cat = make_category(client, admin, name="Grains")
    assert client.get("/categories").json()[0]["slug"] == "grains"
    r = client.put(f"/categories/{cat['id']}", json={"name": "Cereals"}, headers=admin)
    assert r.status_code == 200 and r.json()["slug"] == "cereals"
