from .conftest import make_admin, make_category, make_customer, make_product


def _seed(client):
    admin = make_admin(client)
    cat = make_category(client, admin)
    product = make_product(client, admin, cat["id"], price="100.00", stock=10)
    customer = make_customer(client)
    return admin, customer, product


def _add_to_cart(client, customer, product_id, qty=2):
    r = client.post("/cart", json={"product_id": product_id, "quantity": qty}, headers=customer)
    assert r.status_code == 201, r.text
    return r.json()


def test_cart_add_update_remove(client):
    _, customer, product = _seed(client)
    item = _add_to_cart(client, customer, product["id"], qty=2)
    assert item["subtotal"] == "200.00"
    r = client.put(f"/cart/{item['id']}", json={"quantity": 3}, headers=customer)
    assert r.json()["quantity"] == 3
    assert client.get("/cart", headers=customer).json()[0]["quantity"] == 3
    assert client.delete(f"/cart/{item['id']}", headers=customer).status_code == 204
    assert client.get("/cart", headers=customer).json() == []


def test_cart_rejects_over_stock(client):
    _, customer, product = _seed(client)
    r = client.post("/cart", json={"product_id": product["id"], "quantity": 999}, headers=customer)
    assert r.status_code == 400


def test_order_cod_success_and_stock_reduced(client):
    admin, customer, product = _seed(client)
    _add_to_cart(client, customer, product["id"], qty=2)
    r = client.post(
        "/orders",
        json={"delivery_address": "Dhaka, Bangladesh", "phone": "01700000000", "payment_method": "cod"},
        headers=customer,
    )
    assert r.status_code == 201, r.text
    order = r.json()
    assert order["total_amount"] == "200.00"
    assert order["payment_method"] == "cod" and order["payment_status"] == "pending"
    # Cart cleared, stock reduced 10 -> 8
    assert client.get("/cart", headers=customer).json() == []
    assert client.get(f"/products/{product['id']}").json()["stock"] == 8
    # Customer sees own order; admin sees all
    assert len(client.get("/orders", headers=customer).json()) == 1
    assert len(client.get("/orders/all", headers=admin).json()) == 1


def test_order_empty_cart_rejected(client):
    _, customer, _ = _seed(client)
    r = client.post(
        "/orders",
        json={"delivery_address": "Dhaka", "phone": "01700000000", "payment_method": "cod"},
        headers=customer,
    )
    assert r.status_code == 400


def test_order_bkash_requires_trxid(client):
    _, customer, product = _seed(client)
    _add_to_cart(client, customer, product["id"], qty=1)
    base = {"delivery_address": "Dhaka, Bangladesh", "phone": "01700000000", "payment_method": "bkash"}
    # No transaction ID -> rejected
    assert client.post("/orders", json=base, headers=customer).status_code == 400
    # With sender number + transaction ID -> created
    r = client.post("/orders", json={**base, "sender_number": "01711111111", "transaction_id": "TRX123456"}, headers=customer)
    assert r.status_code == 201, r.text
    assert r.json()["payment_method"] == "bkash"


def test_admin_can_update_order_status(client):
    admin, customer, product = _seed(client)
    _add_to_cart(client, customer, product["id"], qty=1)
    order = client.post(
        "/orders",
        json={"delivery_address": "Dhaka", "phone": "01700000000", "payment_method": "cod"},
        headers=customer,
    ).json()
    r = client.patch(f"/orders/{order['id']}/status", json={"status": "confirmed"}, headers=admin)
    assert r.status_code == 200 and r.json()["status"] == "confirmed"
    assert client.patch(f"/orders/{order['id']}/status", json={"status": "confirmed"}, headers=customer).status_code == 403
