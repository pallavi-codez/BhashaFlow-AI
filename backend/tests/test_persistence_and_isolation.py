"""
Tests for multi-tenant shop isolation, session restoration, overpayment confirmation, and persistence.
"""
from decimal import Decimal
from fastapi.testclient import TestClient

from backend import crud
from backend.auth import create_access_token
from backend.config import Settings
from backend.schemas import CustomerCreate


def test_multi_tenant_shop_isolation(db, shop, customer):
    """Ensure data from Shop A cannot be viewed, accessed, or modified by Shop B."""
    # Create Shop B
    shop_b = crud.create_shop(
        db,
        name="Shop B Fresh Mart",
        owner_name="Owner B",
        phone="+918888888888",
        password_plain="passwordB",
    )
    token_b = create_access_token(shop_b.id)
    from backend.main import app
    client_b = TestClient(app)
    client_b.headers = {"Authorization": f"Bearer {token_b}"}

    # 1. Shop B lists customers -> should be empty
    r = client_b.get("/api/customers")
    assert r.status_code == 200
    assert len(r.json()) == 0

    # 2. Shop B attempts to get Shop A's customer -> 404
    r_cust = client_b.get(f"/api/customers/{customer.id}")
    assert r_cust.status_code == 404

    # 3. Shop B attempts to create transaction for Shop A's customer -> 404
    r_txn = client_b.post(
        "/api/transactions",
        json={
            "customer_id": customer.id,
            "txn_type": "CREDIT_SALE",
            "amount": "100.00",
        },
    )
    assert r_txn.status_code == 404

    # 4. Shop B creates its own customer and expense
    c_b = crud.create_customer(db, shop_b.id, CustomerCreate(name="Customer B"))
    r_exp_b = client_b.post(
        "/api/expenses",
        json={"amount": "250.00", "category": "rent", "note": "Shop B rent"},
    )
    assert r_exp_b.status_code == 201

    # Shop A client should not see Shop B's expense
    token_a = create_access_token(shop.id)
    client_a = TestClient(app)
    client_a.headers = {"Authorization": f"Bearer {token_a}"}
    r_exp_a = client_a.get("/api/expenses")
    assert len(r_exp_a.json()) == 0


def test_session_restoration_and_token_response(db, shop):
    """Test GET /api/auth/me and TokenResponse payload structure."""
    from backend.main import app
    client = TestClient(app)

    # 1. Unauthenticated request to /me -> 403 or 401
    unauth_r = client.get("/api/auth/me")
    assert unauth_r.status_code in (401, 403)

    # 2. Authenticated request to /me
    token = create_access_token(shop.id)
    client.headers = {"Authorization": f"Bearer {token}"}
    me_r = client.get("/api/auth/me")
    assert me_r.status_code == 200
    me_data = me_r.json()
    assert me_data["id"] == shop.id
    assert me_data["name"] == "Test Shop"
    assert me_data["phone"] == "+919999999999"
    assert "is_demo" in me_data
    assert "language" in me_data

    # 3. Normal login returns is_demo and language
    login_r = client.post(
        "/api/auth/login",
        json={"phone": "+919999999999", "password": "testpass"},
    )
    assert login_r.status_code == 200
    login_data = login_r.json()
    assert login_data["is_demo"] is False
    assert login_data["language"] == "kn-IN"

    # 4. Demo login returns is_demo = True
    demo_r = client.post("/api/auth/demo")
    assert demo_r.status_code == 200
    demo_data = demo_r.json()
    assert demo_data["is_demo"] is True


def test_overpayment_confirmation_flow(auth_client: TestClient, db, shop, customer):
    """Verify that payment exceeding debt raises 422 until explicitly confirmed."""
    # Give customer ₹100 credit
    r1 = auth_client.post(
        "/api/transactions",
        json={
            "customer_id": customer.id,
            "txn_type": "CREDIT_SALE",
            "amount": "100.00",
        },
    )
    auth_client.post("/api/transactions/confirm", json={"transaction_id": r1.json()["id"]})

    # Attempt to record payment of ₹150 without allow_overpayment -> 422
    err_r = auth_client.post(
        "/api/transactions",
        json={
            "customer_id": customer.id,
            "txn_type": "PAYMENT",
            "amount": "150.00",
            "allow_overpayment": False,
        },
    )
    assert err_r.status_code == 422
    detail = err_r.json()["detail"]
    assert detail["error"] == "overpayment"
    assert Decimal(str(detail["outstanding"])) == Decimal("100.00")

    # Now attempt with allow_overpayment = True -> should succeed
    ok_r = auth_client.post(
        "/api/transactions",
        json={
            "customer_id": customer.id,
            "txn_type": "PAYMENT",
            "amount": "150.00",
            "allow_overpayment": True,
        },
    )
    assert ok_r.status_code == 201
    txn_id = ok_r.json()["id"]
    confirm_r = auth_client.post("/api/transactions/confirm", json={"transaction_id": txn_id})
    assert confirm_r.status_code == 200

    # Customer balance is now negative (-₹50.00 advance/credit balance)
    bal = crud.compute_customer_balance(db, shop.id, customer.id)
    assert bal == Decimal("-50.00")


def test_sqlite_path_anchored_to_project_root():
    """Verify Settings resolves relative SQLite paths to absolute paths anchored to project root."""
    settings = Settings()
    assert settings.database_url.startswith("sqlite:///")
    assert "bhashaflow.db" in settings.database_url
    # Ensure it is not a relative path like sqlite:///./bhashaflow.db
    assert not settings.database_url.startswith("sqlite:///./")
