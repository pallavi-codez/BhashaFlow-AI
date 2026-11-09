"""
Accounting benchmark tests for BhashaFlow AI.

Scenario:
1. ₹500 credit sale to customer
2. ₹300 cash sale (no customer)
3. ₹200 debt payment received from customer
4. ₹100 shop expense

Verification targets:
- Customer outstanding balance: ₹300.00
- Total outstanding ledger: ₹300.00
- Today's credit sales: ₹500.00
- Today's cash sales: ₹300.00
- Today's cash received: ₹500.00 (₹300 cash sale + ₹200 payment)
- Today's expenses: ₹100.00
- Today's net cash movement: ₹400.00 (₹500 cash received - ₹100 expenses)
"""
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from backend import crud
from backend.models import TransactionType


def test_standard_accounting_benchmark_flow(auth_client: TestClient, db, shop, customer):
    # 1. ₹500 Credit Sale to customer
    r1 = auth_client.post(
        "/api/transactions",
        json={
            "customer_id": customer.id,
            "txn_type": "CREDIT_SALE",
            "amount": "500.00",
            "note": "Atta and rice on credit",
        },
    )
    assert r1.status_code == 201, r1.text
    txn1_id = r1.json()["id"]
    # Confirm
    cr1 = auth_client.post("/api/transactions/confirm", json={"transaction_id": txn1_id})
    assert cr1.status_code == 200

    # Verify balance after credit sale
    bal = crud.compute_customer_balance(db, shop.id, customer.id)
    assert bal == Decimal("500.00")

    # 2. ₹300 Cash Sale (no customer)
    r2 = auth_client.post(
        "/api/transactions",
        json={
            "txn_type": "CASH_SALE",
            "amount": "300.00",
            "note": "Biscuits and soap counter cash",
        },
    )
    assert r2.status_code == 201, r2.text
    txn2_id = r2.json()["id"]
    cr2 = auth_client.post("/api/transactions/confirm", json={"transaction_id": txn2_id})
    assert cr2.status_code == 200

    # Verify balance unchanged after cash sale
    bal = crud.compute_customer_balance(db, shop.id, customer.id)
    assert bal == Decimal("500.00")

    # 3. ₹200 Debt Payment received
    r3 = auth_client.post(
        "/api/transactions",
        json={
            "customer_id": customer.id,
            "txn_type": "PAYMENT",
            "amount": "200.00",
            "note": "Partial payment via UPI/Cash",
        },
    )
    assert r3.status_code == 201, r3.text
    txn3_id = r3.json()["id"]
    cr3 = auth_client.post("/api/transactions/confirm", json={"transaction_id": txn3_id})
    assert cr3.status_code == 200

    # Verify balance reduced to exactly ₹300.00
    bal = crud.compute_customer_balance(db, shop.id, customer.id)
    assert bal == Decimal("300.00")

    # 4. ₹100 Shop Expense
    r4 = auth_client.post(
        "/api/expenses",
        json={
            "amount": "100.00",
            "category": "supplies",
            "note": "Packaging bags",
        },
    )
    assert r4.status_code == 201, r4.text

    # 5. Check Dashboard aggregates
    dash_r = auth_client.get("/api/dashboard")
    assert dash_r.status_code == 200
    stats = dash_r.json()

    assert Decimal(str(stats["total_credit_sales"])) == Decimal("500.00")
    assert Decimal(str(stats["total_cash_sales"])) == Decimal("300.00")
    assert Decimal(str(stats["total_payments_received"])) == Decimal("200.00")
    assert Decimal(str(stats["total_cash_received"])) == Decimal("500.00")
    assert Decimal(str(stats["total_expenses"])) == Decimal("100.00")
    assert Decimal(str(stats["total_outstanding"])) == Decimal("300.00")
    assert Decimal(str(stats["net_cash_movement"])) == Decimal("400.00")
    assert stats["total_transactions_today"] == 3  # 3 confirmed transactions (expenses are in expenses table)


def test_decimal_precision_accounting(auth_client: TestClient, customer):
    """Test exact decimal arithmetic with odd paise amounts (no floating point epsilon errors)."""
    # ₹19.99 credit sale
    r1 = auth_client.post(
        "/api/transactions",
        json={
            "customer_id": customer.id,
            "txn_type": "CREDIT_SALE",
            "amount": "19.99",
        },
    )
    assert r1.status_code == 201
    auth_client.post("/api/transactions/confirm", json={"transaction_id": r1.json()["id"]})

    # ₹30.01 credit sale
    r2 = auth_client.post(
        "/api/transactions",
        json={
            "customer_id": customer.id,
            "txn_type": "CREDIT_SALE",
            "amount": "30.01",
        },
    )
    assert r2.status_code == 201
    auth_client.post("/api/transactions/confirm", json={"transaction_id": r2.json()["id"]})

    # Check customer balance via API
    c_res = auth_client.get(f"/api/customers/{customer.id}")
    assert c_res.status_code == 200
    # Must be exact 50.00, not 50.00000000000001
    assert Decimal(str(c_res.json()["outstanding_balance"])) == Decimal("50.00")
