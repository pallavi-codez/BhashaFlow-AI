"""
BhashaFlow AI — Complete Real-Shop Simulation Test Suite.

Tests the full end-to-end flow for a demo shop using an isolated in-memory DB.
No real data is ever touched. All assertions check actual DB records.

Scenario:
  1. Register & authenticate demo shop
  2. Add Ramesh and Suresh as customers
  3. Rs.500 credit sale for Ramesh   (CREDIT_SALE, confirmed)
  4. Rs.100 payment from Ramesh      (PAYMENT, confirmed)
  5. Ask Ledger: "How much does Ramesh owe?" -> expect Rs.400
  6. Rs.300 cash sale                (CASH_SALE, confirmed)
  7. Rs.100 shop expense             (Expense record)
  8. Dashboard totals verified
  9. Transaction history verified
 10. Re-login persistence verified
 11. Cross-shop data isolation verified
"""
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _register(client: TestClient, phone: str, name: str, owner: str, pwd: str) -> str:
    """Register a shop and return the JWT token."""
    r = client.post("/api/auth/register", json={
        "name": name,
        "owner_name": owner,
        "phone": phone,
        "password": pwd,
        "language": "kn-IN",
    })
    assert r.status_code == 201, f"Register failed: {r.text}"
    return r.json()["access_token"]


def _login(client: TestClient, phone: str, pwd: str) -> str:
    """Login and return the JWT token."""
    r = client.post("/api/auth/login", json={"phone": phone, "password": pwd})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["access_token"]


def _add_customer(client: TestClient, token: str, name: str) -> int:
    r = client.post("/api/customers", json={"name": name}, headers=_auth_header(token))
    assert r.status_code == 201, f"Create customer '{name}' failed: {r.text}"
    return r.json()["id"]


def _create_and_confirm_txn(
    client: TestClient,
    token: str,
    txn_type: str,
    amount: float,
    customer_id=None,
    note: str = "",
    idempotency_key=None,
) -> dict:
    """Create a pending transaction then immediately confirm it. Returns confirmed txn dict."""
    payload = {
        "txn_type": txn_type,
        "amount": amount,
        "source": "manual",
    }
    if customer_id is not None:
        payload["customer_id"] = customer_id
    if note:
        payload["note"] = note
    if idempotency_key:
        payload["idempotency_key"] = idempotency_key

    r = client.post("/api/transactions", json=payload, headers=_auth_header(token))
    assert r.status_code == 201, f"Create txn failed: {r.text}"
    txn = r.json()
    txn_id = txn["id"]

    r2 = client.post(
        "/api/transactions/confirm",
        json={"transaction_id": txn_id, "idempotency_key": idempotency_key},
        headers=_auth_header(token),
    )
    assert r2.status_code == 200, f"Confirm txn failed: {r2.text}"
    confirmed = r2.json()
    assert confirmed["confirmed"] is True
    return confirmed


def _ask_ledger(client: TestClient, token: str, query: str, lang: str = "en-IN") -> dict:
    r = client.post(
        "/api/ledger/ask",
        json={"query": query, "language_code": lang},
        headers=_auth_header(token),
    )
    assert r.status_code == 200, f"Ask ledger failed: {r.text}"
    return r.json()


def _dashboard(client: TestClient, token: str) -> dict:
    r = client.get("/api/dashboard", headers=_auth_header(token))
    assert r.status_code == 200, f"Dashboard failed: {r.text}"
    return r.json()


def _list_transactions(client: TestClient, token: str, customer_id=None) -> list:
    url = "/api/transactions"
    if customer_id:
        url += f"?customer_id={customer_id}"
    r = client.get(url, headers=_auth_header(token))
    assert r.status_code == 200
    return r.json()


def _list_customers(client: TestClient, token: str) -> list:
    r = client.get("/api/customers", headers=_auth_header(token))
    assert r.status_code == 200
    return r.json()


# ── Test class ────────────────────────────────────────────────────────────────

class TestShopSimulation:
    """Full simulation: isolated in-memory DB via conftest fixtures."""

    PHONE_A = "+919876540001"  # demo shop A
    PHONE_B = "+919876540002"  # attacker shop B (cross-shop isolation test)
    PWD_A = "securepass123"
    PWD_B = "otherpass456"

    def test_01_register_shop(self, client):
        """STEP 1 -- Register the demo shop and verify token returned."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        assert token and len(token) > 20, "JWT token must be non-empty"

    def test_02_add_customers(self, client):
        """STEP 2 -- Add Ramesh and Suresh as customers."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)

        ramesh_id = _add_customer(client, token, "Ramesh")
        suresh_id = _add_customer(client, token, "Suresh")

        assert ramesh_id > 0
        assert suresh_id > 0
        assert ramesh_id != suresh_id

        customers = _list_customers(client, token)
        names = [c["name"] for c in customers]
        assert "Ramesh" in names, f"Ramesh not in customers: {names}"
        assert "Suresh" in names, f"Suresh not in customers: {names}"

    def test_03_credit_sale_ramesh_500(self, client):
        """STEP 3 -- Rs.500 credit for Ramesh; verify DB record and balance."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token, "Ramesh")

        txn = _create_and_confirm_txn(
            client, token,
            txn_type="CREDIT_SALE",
            amount=500.00,
            customer_id=ramesh_id,
            note="Ramesh credit Rs.500",
            idempotency_key="sim-credit-ramesh-500",
        )

        assert txn["txn_type"] == "CREDIT_SALE"
        assert Decimal(str(txn["amount"])) == Decimal("500.00")
        assert txn["customer_id"] == ramesh_id
        assert txn["confirmed"] is True

        # Verify customer balance via customer endpoint
        r = client.get(f"/api/customers/{ramesh_id}", headers=_auth_header(token))
        assert r.status_code == 200
        balance = Decimal(str(r.json()["outstanding_balance"]))
        assert balance == Decimal("500.00"), f"Expected Rs.500 balance, got {balance}"

    def test_04_payment_ramesh_100(self, client):
        """STEP 4 -- Rs.100 payment from Ramesh; balance must drop to Rs.400."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token, "Ramesh")

        # First create the Rs.500 credit
        _create_and_confirm_txn(
            client, token, "CREDIT_SALE", 500.00, ramesh_id,
            idempotency_key="sim-04-credit",
        )

        # Now record Rs.100 payment
        txn = _create_and_confirm_txn(
            client, token,
            txn_type="PAYMENT",
            amount=100.00,
            customer_id=ramesh_id,
            note="Ramesh payment Rs.100",
            idempotency_key="sim-04-payment",
        )

        assert txn["txn_type"] == "PAYMENT"
        assert Decimal(str(txn["amount"])) == Decimal("100.00")

        r = client.get(f"/api/customers/{ramesh_id}", headers=_auth_header(token))
        balance = Decimal(str(r.json()["outstanding_balance"]))
        assert balance == Decimal("400.00"), f"Expected Rs.400, got {balance}"

    def test_05_ask_ledger_ramesh_owes(self, client):
        """STEP 5+6 -- Ask Ledger 'How much does Ramesh owe?' -> Rs.400."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token, "Ramesh")

        _create_and_confirm_txn(client, token, "CREDIT_SALE", 500.00, ramesh_id,
                                 idempotency_key="sim-05-credit")
        _create_and_confirm_txn(client, token, "PAYMENT", 100.00, ramesh_id,
                                 idempotency_key="sim-05-payment")

        resp = _ask_ledger(client, token, "How much does Ramesh owe?")

        assert resp["clarification_needed"] is False, (
            f"Unexpected clarification: {resp.get('candidates')}"
        )
        assert resp["no_records"] is False, "no_records must be False"

        # Amount in response must be Rs.400
        assert resp["amount"] is not None, f"No amount in ledger response: {resp}"
        answer_amount = Decimal(str(resp["amount"]))
        assert answer_amount == Decimal("400.00"), (
            f"Expected Rs.400, got {answer_amount}. Full response: {resp}"
        )

    def test_06_cash_sale_300(self, client):
        """STEP 7 -- Rs.300 cash sale; no customer required."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)

        txn = _create_and_confirm_txn(
            client, token,
            txn_type="CASH_SALE",
            amount=300.00,
            note="Cash sale Rs.300",
            idempotency_key="sim-cash-300",
        )

        assert txn["txn_type"] == "CASH_SALE"
        assert Decimal(str(txn["amount"])) == Decimal("300.00")
        assert txn["customer_id"] is None

    def test_07_expense_100(self, client):
        """STEP 8 -- Rs.100 shop expense recorded via Expenses endpoint."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)

        r = client.post(
            "/api/expenses",
            json={"amount": 100.00, "category": "supplies", "note": "Shop supplies"},
            headers=_auth_header(token),
        )
        assert r.status_code == 201, f"Expense creation failed: {r.text}"
        exp = r.json()
        assert Decimal(str(exp["amount"])) == Decimal("100.00")
        assert exp["category"] == "supplies"

    def test_08_dashboard_totals(self, client):
        """STEP 9 -- Dashboard shows correct aggregates after full scenario."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token, "Ramesh")

        # Rs.500 credit for Ramesh
        _create_and_confirm_txn(client, token, "CREDIT_SALE", 500.00, ramesh_id,
                                 idempotency_key="dash-credit")
        # Rs.100 payment from Ramesh
        _create_and_confirm_txn(client, token, "PAYMENT", 100.00, ramesh_id,
                                 idempotency_key="dash-payment")
        # Rs.300 cash sale
        _create_and_confirm_txn(client, token, "CASH_SALE", 300.00,
                                 idempotency_key="dash-cash")
        # Rs.100 expense
        client.post("/api/expenses",
                    json={"amount": 100.00, "category": "supplies"},
                    headers=_auth_header(token))

        dash = _dashboard(client, token)

        assert Decimal(str(dash["total_credit_sales"])) == Decimal("500.00"), \
            f"credit_sales: {dash['total_credit_sales']}"
        assert Decimal(str(dash["total_payments_received"])) == Decimal("100.00"), \
            f"payments: {dash['total_payments_received']}"
        assert Decimal(str(dash["total_cash_sales"])) == Decimal("300.00"), \
            f"cash_sales: {dash['total_cash_sales']}"
        assert Decimal(str(dash["total_expenses"])) == Decimal("100.00"), \
            f"expenses: {dash['total_expenses']}"
        assert Decimal(str(dash["total_outstanding"])) == Decimal("400.00"), \
            f"outstanding: {dash['total_outstanding']}"

        # cash received = cash_sales + payments = 300 + 100 = 400
        assert Decimal(str(dash["total_cash_received"])) == Decimal("400.00"), \
            f"cash_received: {dash['total_cash_received']}"

        # net cash = cash_received - expenses = 400 - 100 = 300
        assert Decimal(str(dash["net_cash_movement"])) == Decimal("300.00"), \
            f"net_cash: {dash['net_cash_movement']}"

        assert dash["total_customers"] == 1   # only Ramesh was added
        assert dash["total_transactions_today"] == 3  # credit + payment + cash

    def test_09_transaction_history(self, client):
        """STEP 9b -- Transaction list returns all confirmed transactions."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token, "Ramesh")

        _create_and_confirm_txn(client, token, "CREDIT_SALE", 500.00, ramesh_id,
                                 idempotency_key="hist-credit")
        _create_and_confirm_txn(client, token, "PAYMENT", 100.00, ramesh_id,
                                 idempotency_key="hist-payment")
        _create_and_confirm_txn(client, token, "CASH_SALE", 300.00,
                                 idempotency_key="hist-cash")

        txns = _list_transactions(client, token)
        assert len(txns) == 3, f"Expected 3 transactions, got {len(txns)}"

        types = {t["txn_type"] for t in txns}
        assert "CREDIT_SALE" in types
        assert "PAYMENT"     in types
        assert "CASH_SALE"   in types

        # Verify Ramesh-only filter
        ramesh_txns = _list_transactions(client, token, customer_id=ramesh_id)
        assert len(ramesh_txns) == 2, f"Ramesh should have 2 txns, got {len(ramesh_txns)}"
        for t in ramesh_txns:
            assert t["customer_id"] == ramesh_id

    def test_10_no_duplicate_transactions(self, client):
        """STEP 9c -- Idempotency: same key must not create duplicate transactions."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token, "Ramesh")

        idem_key = "idem-test-unique-key"

        # Create first time
        r1 = client.post("/api/transactions", json={
            "txn_type": "CREDIT_SALE", "amount": 200.00,
            "customer_id": ramesh_id, "idempotency_key": idem_key,
        }, headers=_auth_header(token))
        assert r1.status_code == 201
        txn1_id = r1.json()["id"]

        # Confirm it
        client.post("/api/transactions/confirm",
                    json={"transaction_id": txn1_id, "idempotency_key": idem_key},
                    headers=_auth_header(token))

        # Attempt to create again with same key
        r2 = client.post("/api/transactions", json={
            "txn_type": "CREDIT_SALE", "amount": 200.00,
            "customer_id": ramesh_id, "idempotency_key": idem_key,
        }, headers=_auth_header(token))
        assert r2.status_code == 201  # returns existing, not new
        txn2_id = r2.json()["id"]
        assert txn1_id == txn2_id, "Duplicate transaction created despite same idempotency key!"

        # Balance must be Rs.200, not Rs.400
        r = client.get(f"/api/customers/{ramesh_id}", headers=_auth_header(token))
        balance = Decimal(str(r.json()["outstanding_balance"]))
        assert balance == Decimal("200.00"), f"Duplicate txn! Balance is {balance}, expected 200"

    def test_11_login_persistence(self, client):
        """STEP 10 -- Re-login returns new token and data persists."""
        # Register
        token1 = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token1, "Ramesh")
        _create_and_confirm_txn(client, token1, "CREDIT_SALE", 750.00, ramesh_id,
                                 idempotency_key="persist-credit")

        # Login again (simulates "log out and log back in")
        token2 = _login(client, self.PHONE_A, self.PWD_A)
        assert token2 and len(token2) > 20

        # Data still visible after re-login
        customers = _list_customers(client, token2)
        names = [c["name"] for c in customers]
        assert "Ramesh" in names, f"Ramesh not found after re-login: {names}"

        r = client.get(f"/api/customers/{ramesh_id}", headers=_auth_header(token2))
        assert r.status_code == 200
        balance = Decimal(str(r.json()["outstanding_balance"]))
        assert balance == Decimal("750.00"), f"Balance not persisted: {balance}"

        txns = _list_transactions(client, token2)
        assert len(txns) == 1

    def test_12_cross_shop_isolation(self, client):
        """STEP 11 -- Shop B cannot read Shop A's customers or transactions."""
        # Set up Shop A with data
        token_a = _register(client, self.PHONE_A, "Shop A", "Owner A", self.PWD_A)
        ramesh_id = _add_customer(client, token_a, "Ramesh")
        _create_and_confirm_txn(client, token_a, "CREDIT_SALE", 999.00, ramesh_id,
                                 idempotency_key="iso-credit-a")

        # Register Shop B
        token_b = _register(client, self.PHONE_B, "Shop B", "Owner B", self.PWD_B)

        # Shop B's customer list must be empty
        customers_b = _list_customers(client, token_b)
        assert len(customers_b) == 0, f"Shop B sees Shop A's customers! {customers_b}"

        # Shop B's transactions must be empty
        txns_b = _list_transactions(client, token_b)
        assert len(txns_b) == 0, f"Shop B sees Shop A's transactions! {txns_b}"

        # Shop B cannot GET Shop A's customer directly
        r = client.get(f"/api/customers/{ramesh_id}", headers=_auth_header(token_b))
        assert r.status_code == 404, (
            f"Shop B accessed Shop A's customer! Status: {r.status_code}"
        )

        # Shop B's dashboard shows zeros
        dash_b = _dashboard(client, token_b)
        assert Decimal(str(dash_b["total_outstanding"])) == Decimal("0.00"), \
            f"Shop B sees Shop A's outstanding balance: {dash_b['total_outstanding']}"

    def test_13_unconfirmed_txn_invisible(self, client):
        """Unconfirmed transactions must NOT appear in balances or history."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token, "Ramesh")

        # Create but do NOT confirm
        r = client.post("/api/transactions", json={
            "txn_type": "CREDIT_SALE", "amount": 500.00,
            "customer_id": ramesh_id, "idempotency_key": "unconf-test",
        }, headers=_auth_header(token))
        assert r.status_code == 201

        # Balance must be Rs.0 (unconfirmed)
        rc = client.get(f"/api/customers/{ramesh_id}", headers=_auth_header(token))
        balance = Decimal(str(rc.json()["outstanding_balance"]))
        assert balance == Decimal("0.00"), f"Unconfirmed txn affecting balance! Got {balance}"

        # Transaction list must be empty
        txns = _list_transactions(client, token)
        assert len(txns) == 0, f"Unconfirmed txn appears in list: {txns}"

    def test_14_ask_ledger_no_records(self, client):
        """Ask Ledger returns no_records=True or amount=0 when customer has zero txns."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        _add_customer(client, token, "Suresh")

        resp = _ask_ledger(client, token, "How much does Suresh owe?")
        suresh_balance = Decimal(str(resp.get("amount", "0") or "0"))
        assert suresh_balance == Decimal("0.00") or resp["no_records"] is True, (
            f"Expected Rs.0 or no_records for Suresh, got: {resp}"
        )

    def test_15_customer_outstanding_via_ledger(self, client):
        """Full scenario via Ask Ledger: Rs.500 credit - Rs.100 payment = Rs.400."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token, "Ramesh")

        _create_and_confirm_txn(client, token, "CREDIT_SALE", 500.00, ramesh_id,
                                 idempotency_key="ledger-credit")
        _create_and_confirm_txn(client, token, "PAYMENT", 100.00, ramesh_id,
                                 idempotency_key="ledger-payment")

        resp = _ask_ledger(client, token, "What is Ramesh's outstanding balance?")
        assert resp["amount"] is not None
        assert Decimal(str(resp["amount"])) == Decimal("400.00"), (
            f"Outstanding balance mismatch: {resp}"
        )

    def test_16_cash_sale_does_not_affect_customer_balance(self, client):
        """Cash sales must NOT affect any customer's outstanding balance."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token, "Ramesh")

        _create_and_confirm_txn(client, token, "CREDIT_SALE", 500.00, ramesh_id,
                                 idempotency_key="cash-iso-credit")
        _create_and_confirm_txn(client, token, "CASH_SALE", 300.00,
                                 idempotency_key="cash-iso-sale")

        r = client.get(f"/api/customers/{ramesh_id}", headers=_auth_header(token))
        balance = Decimal(str(r.json()["outstanding_balance"]))
        assert balance == Decimal("500.00"), f"Cash sale leaked into customer balance: {balance}"

    def test_17_expense_does_not_affect_customer_balance(self, client):
        """Shop expenses must NOT affect any customer's outstanding balance."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token, "Ramesh")

        _create_and_confirm_txn(client, token, "CREDIT_SALE", 500.00, ramesh_id,
                                 idempotency_key="exp-iso-credit")

        client.post("/api/expenses",
                    json={"amount": 100.00, "category": "supplies"},
                    headers=_auth_header(token))

        r = client.get(f"/api/customers/{ramesh_id}", headers=_auth_header(token))
        balance = Decimal(str(r.json()["outstanding_balance"]))
        assert balance == Decimal("500.00"), f"Expense leaked into balance: {balance}"

    def test_18_multiple_customers_independent_balances(self, client):
        """Ramesh and Suresh must have independent, non-interfering balances."""
        token = _register(client, self.PHONE_A, "Demo Kirana", "Raju", self.PWD_A)
        ramesh_id = _add_customer(client, token, "Ramesh")
        suresh_id = _add_customer(client, token, "Suresh")

        _create_and_confirm_txn(client, token, "CREDIT_SALE", 500.00, ramesh_id,
                                 idempotency_key="multi-ramesh-credit")
        _create_and_confirm_txn(client, token, "CREDIT_SALE", 200.00, suresh_id,
                                 idempotency_key="multi-suresh-credit")
        _create_and_confirm_txn(client, token, "PAYMENT", 100.00, ramesh_id,
                                 idempotency_key="multi-ramesh-payment")

        r_ramesh = client.get(f"/api/customers/{ramesh_id}", headers=_auth_header(token))
        r_suresh = client.get(f"/api/customers/{suresh_id}", headers=_auth_header(token))

        bal_ramesh = Decimal(str(r_ramesh.json()["outstanding_balance"]))
        bal_suresh = Decimal(str(r_suresh.json()["outstanding_balance"]))

        assert bal_ramesh == Decimal("400.00"), f"Ramesh balance: {bal_ramesh}"
        assert bal_suresh == Decimal("200.00"), f"Suresh balance: {bal_suresh}"

        total_outstanding = Decimal(str(_dashboard(client, token)["total_outstanding"]))
        assert total_outstanding == Decimal("600.00"), f"Total outstanding: {total_outstanding}"


# ── Shared fixture: fresh TestClient per test ─────────────────────────────────

@pytest.fixture
def client():
    """
    Returns a TestClient backed by the same in-memory DB as conftest.py.
    Each test gets a fresh empty DB via the autouse setup_db fixture.
    """
    from backend.main import app
    return TestClient(app)

