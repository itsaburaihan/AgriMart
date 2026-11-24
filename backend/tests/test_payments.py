from .conftest import make_admin, make_category, make_customer, make_product


def _bkash_order(client, customer, product_id):
    client.post("/cart", json={"product_id": product_id, "quantity": 1}, headers=customer)
    r = client.post(
        "/orders",
        json={
            "delivery_address": "Dhaka, Bangladesh",
            "phone": "01700000000",
            "payment_method": "bkash",
            "sender_number": "01711111111",
            "transaction_id": "TRX999",
        },
        headers=customer,
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_payment_info_shows_bkash_number(client):
    r = client.get("/payments/info")
    assert r.status_code == 200
    assert r.json()["bkash_number"] == "01736439950"


def test_admin_verifies_bkash_payment(client):
    admin = make_admin(client)
    cat = make_category(client, admin)
    product = make_product(client, admin, cat["id"], price="100.00", stock=5)
    customer = make_customer(client)
    order = _bkash_order(client, customer, product["id"])

    payments = client.get("/payments", headers=admin).json()
    assert len(payments) == 1
    payment = payments[0]
    assert payment["order_id"] == order["id"]
    assert payment["transaction_id"] == "TRX999"
    assert payment["status"] == "pending"

    r = client.patch(f"/payments/{payment['id']}/verify", json={"status": "verified"}, headers=admin)
    assert r.status_code == 200 and r.json()["status"] == "verified"
    # Order payment status follows the payment
    assert client.get(f"/orders/{order['id']}", headers=admin).json()["payment_status"] == "verified"


def test_customer_cannot_verify_payment(client):
    admin = make_admin(client)
    cat = make_category(client, admin)
    product = make_product(client, admin, cat["id"], price="100.00", stock=5)
    customer = make_customer(client)
    _bkash_order(client, customer, product["id"])
    payment = client.get("/payments", headers=admin).json()[0]
    assert client.patch(f"/payments/{payment['id']}/verify", json={"status": "verified"}, headers=customer).status_code == 403


def test_nagad_order_requires_trxid_too(client):
    admin = make_admin(client)
    cat = make_category(client, admin)
    product = make_product(client, admin, cat["id"], price="50.00", stock=5)
    customer = make_customer(client)
    client.post("/cart", json={"product_id": product["id"], "quantity": 1}, headers=customer)
    base = {"delivery_address": "Dhaka", "phone": "01700000000", "payment_method": "nagad"}
    assert client.post("/orders", json=base).status_code == 400
    r = client.post("/orders", json={**base, "sender_number": "01822222222", "transaction_id": "NAGAD1"}, headers=customer)
    assert r.status_code == 201, r.text
