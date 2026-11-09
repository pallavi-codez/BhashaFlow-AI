"""
Tests for Ask Your Ledger feature:
- Verifies endpoint /api/ledger/ask with authenticated client.
- Tests the 6 required example questions with deterministic calculations:
    1. How much does Ramesh owe?
    2. How much credit did I give today?
    3. Who owes me more than ₹1,000?
    4. How much cash did I collect today?
    5. What were my expenses today?
    6. How much did I sell today?
- Tests strict tenant isolation across different shops.
- Tests unconfirmed transactions exclusion.
- Tests ambiguous customer resolution and non-existent customer handling.
"""
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from backend import crud
from backend.models import Customer, Expense, Shop, Transaction, TransactionType


def test_ask_ledger_six_example_questions(auth_client: TestClient, db, shop, customer):
    """
    Controlled fixture:
    - Customer 1 (Ramesh): Credit sale ₹500, Payment ₹100 -> owes ₹400
    - Customer 2 (Suresh): Credit sale ₹1,500 -> owes ₹1,500 (> ₹1,000)
    - Counter cash sale: ₹300
    - Expense: ₹150
    """
    # Customer 2 (Suresh)
    from backend.schemas import CustomerCreate
    suresh = crud.create_customer(db, shop.id, CustomerCreate(name="Suresh", phone="9876543210"))

    # 1. Ramesh: Credit sale ₹500 (confirmed)
    t1 = crud.create_transaction(
        db,
        shop.id,
        crud.TransactionCreate(
            customer_id=customer.id,
            txn_type=TransactionType.CREDIT_SALE,
            amount=Decimal("500.00"),
            note="Rice and dal on credit",
        ),
    )
    crud.confirm_transaction(db, shop.id, t1.id)

    # 2. Ramesh: Payment ₹100 (confirmed)
    t2 = crud.create_transaction(
        db,
        shop.id,
        crud.TransactionCreate(
            customer_id=customer.id,
            txn_type=TransactionType.PAYMENT,
            amount=Decimal("100.00"),
            note="Partial payment received",
        ),
    )
    crud.confirm_transaction(db, shop.id, t2.id)

    # 3. Suresh: Credit sale ₹1500 (confirmed)
    t3 = crud.create_transaction(
        db,
        shop.id,
        crud.TransactionCreate(
            customer_id=suresh.id,
            txn_type=TransactionType.CREDIT_SALE,
            amount=Decimal("1500.00"),
            note="Oil tin and spices on credit",
        ),
    )
    crud.confirm_transaction(db, shop.id, t3.id)

    # 4. Counter Cash Sale ₹300 (confirmed)
    t4 = crud.create_transaction(
        db,
        shop.id,
        crud.TransactionCreate(
            txn_type=TransactionType.CASH_SALE,
            amount=Decimal("300.00"),
            note="Counter snacks and biscuits",
        ),
    )
    crud.confirm_transaction(db, shop.id, t4.id)

    # 5. Shop Expense ₹150
    crud.create_expense(
        db,
        shop.id,
        crud.ExpenseCreate(
            amount=Decimal("150.00"),
            category="supplies",
            note="Packaging bags and cleaning supplies",
        ),
    )

    # ── 1. How much does Ramesh owe? ───────────────────────────────────────────
    res1 = auth_client.post("/api/ledger/ask", json={"query": "How much does Ramesh owe?"})
    assert res1.status_code == 200, res1.text
    data1 = res1.json()
    assert data1["intent"] == "customer_balance"
    assert Decimal(data1["amount"]) == Decimal("400.00")
    assert "Ramesh owes ₹400.00" in data1["answer"]
    assert data1["no_records"] is False

    # ── 2. How much credit did I give today? ──────────────────────────────────
    # Total credit today = 500 + 1500 = 2000
    res2 = auth_client.post("/api/ledger/ask", json={"query": "How much credit did I give today?"})
    assert res2.status_code == 200, res2.text
    data2 = res2.json()
    assert data2["intent"] == "credit_sales"
    assert Decimal(data2["amount"]) == Decimal("2000.00")
    assert "₹2,000.00" in data2["answer"]
    assert len(data2["details"]) == 2

    # ── 3. Who owes me more than ₹1,000? ──────────────────────────────────────
    # Only Suresh owes ₹1500 (> 1000)
    res3 = auth_client.post("/api/ledger/ask", json={"query": "Who owes me more than ₹1,000?"})
    assert res3.status_code == 200, res3.text
    data3 = res3.json()
    assert data3["intent"] == "debtors_above_threshold"
    assert Decimal(data3["amount"]) == Decimal("1500.00")
    assert len(data3["details"]) == 1
    assert data3["details"][0]["name"] == "Suresh"
    assert Decimal(data3["details"][0]["amount"]) == Decimal("1500.00")

    # ── 4. How much cash did I collect today? ─────────────────────────────────
    # Cash collected = Cash Sale (300) + Payment Received (100) = 400
    res4 = auth_client.post("/api/ledger/ask", json={"query": "How much cash did I collect today?"})
    assert res4.status_code == 200, res4.text
    data4 = res4.json()
    assert data4["intent"] == "cash_collected"
    assert Decimal(data4["amount"]) == Decimal("400.00")
    assert "₹400.00" in data4["answer"]
    assert "₹300.00 from cash sales" in data4["answer"]
    assert "₹100.00 from debt repayments" in data4["answer"]

    # ── 5. What were my expenses today? ───────────────────────────────────────
    res5 = auth_client.post("/api/ledger/ask", json={"query": "What were my expenses today?"})
    assert res5.status_code == 200, res5.text
    data5 = res5.json()
    assert data5["intent"] == "expenses"
    assert Decimal(data5["amount"]) == Decimal("150.00")
    assert "₹150.00" in data5["answer"]

    # ── 6. How much did I sell today? ─────────────────────────────────────────
    # Strict accounting rule: Total sales = Credit sales (2000) + Cash sales (300) = 2300.
    # Payments against old debt (100) are NOT new sales!
    res6 = auth_client.post("/api/ledger/ask", json={"query": "How much did I sell today?"})
    assert res6.status_code == 200, res6.text
    data6 = res6.json()
    assert data6["intent"] == "total_sales"
    assert Decimal(data6["amount"]) == Decimal("2300.00")
    assert "₹2,300.00" in data6["answer"]


def test_ask_ledger_tenant_isolation(auth_client: TestClient, db, shop, customer):
    """
    Shop A and Shop B must remain strictly isolated.
    Records from Shop B must never appear in Shop A's queries.
    """
    # Create Shop B and its customer & transactions
    shop_b = crud.create_shop(
        db,
        name="Other Kirana Store",
        owner_name="Other Owner",
        phone="+918888888888",
        password_plain="otherpass",
    )
    from backend.schemas import CustomerCreate
    cust_b = crud.create_customer(db, shop_b.id, CustomerCreate(name="ShopBCustomer"))

    t_b = crud.create_transaction(
        db,
        shop_b.id,
        crud.TransactionCreate(
            customer_id=cust_b.id,
            txn_type=TransactionType.CREDIT_SALE,
            amount=Decimal("9999.00"),
            note="Huge credit in Shop B",
        ),
    )
    crud.confirm_transaction(db, shop_b.id, t_b.id)

    # Shop A asks "Who owes me more than ₹1,000?"
    # Shop A has no debtors yet
    res = auth_client.post("/api/ledger/ask", json={"query": "Who owes me more than ₹1,000?"})
    assert res.status_code == 200
    data = res.json()
    assert data["no_records"] is True
    assert Decimal(data["amount"]) == Decimal("0.00")
    assert len(data["details"]) == 0

    # Shop A asks "How much credit did I give today?"
    res_credit = auth_client.post("/api/ledger/ask", json={"query": "How much credit did I give today?"})
    assert res_credit.status_code == 200
    data_credit = res_credit.json()
    assert Decimal(data_credit["amount"]) == Decimal("0.00")

    # Shop A asks "How much does ShopBCustomer owe?"
    res_cust = auth_client.post("/api/ledger/ask", json={"query": "How much does ShopBCustomer owe?"})
    assert res_cust.status_code == 200
    data_cust = res_cust.json()
    assert data_cust["no_records"] is True
    assert "No customer found" in data_cust["answer"]


def test_ask_ledger_ambiguous_customer_names(auth_client: TestClient, db, shop):
    """
    When multiple customers match the requested name (e.g. Ramesh Kumar and Ramesh Patel),
    the assistant should flag clarification_needed=True and return the candidate names safely.
    """
    from backend.schemas import CustomerCreate
    crud.create_customer(db, shop.id, CustomerCreate(name="Ramesh Kumar", phone="9111111111"))
    crud.create_customer(db, shop.id, CustomerCreate(name="Ramesh Patel", phone="9222222222"))

    res = auth_client.post("/api/ledger/ask", json={"query": "How much does Ramesh owe?"})
    assert res.status_code == 200
    data = res.json()
    assert data["clarification_needed"] is True
    assert "Ramesh Kumar" in data["candidates"]
    assert "Ramesh Patel" in data["candidates"]
    assert "Found 2 customers matching 'Ramesh'" in data["answer"]


def test_ask_ledger_unconfirmed_transactions_ignored(auth_client: TestClient, db, shop, customer):
    """
    Unconfirmed transactions must NOT be aggregated into sales or credit given.
    """
    # Create unconfirmed credit sale of 750
    crud.create_transaction(
        db,
        shop.id,
        crud.TransactionCreate(
            customer_id=customer.id,
            txn_type=TransactionType.CREDIT_SALE,
            amount=Decimal("750.00"),
            note="Unconfirmed pending voice sale",
        ),
    )

    res = auth_client.post("/api/ledger/ask", json={"query": "How much credit did I give today?"})
    assert res.status_code == 200
    data = res.json()
    # Should be 0 because transaction was never confirmed
    assert Decimal(data["amount"]) == Decimal("0.00")
    assert data["no_records"] is True


def test_ask_ledger_multilingual_indic_queries(auth_client: TestClient, db, shop, customer):
    """
    Test Indic language questions (Kannada, Hindi, etc.) for:
    - Customer balance: "ರಮೇಶ್ ಎಷ್ಟು ಹಣ ಕೊಡಬೇಕು?", "रमेश पर कितना उधार बाकी है?"
    - Credit sales: "ಇಂದು ಎಷ್ಟು ಉದ್ಧಾರ ಕೊಟ್ಟೆ?", "आज कितना उधार दिया?"
    - Expenses: "ಇವತ್ತಿನ ಖರ್ಚು ಎಷ್ಟು?", "आज का खर्च कितना हुआ?"
    """
    # 1. Confirmed credit sale to Ramesh: ₹450
    t1 = crud.create_transaction(
        db,
        shop.id,
        crud.TransactionCreate(
            customer_id=customer.id,
            txn_type=TransactionType.CREDIT_SALE,
            amount=Decimal("450.00"),
            note="Milk and sugar on credit",
        ),
    )
    crud.confirm_transaction(db, shop.id, t1.id)

    # 2. Confirmed expense: ₹80
    crud.create_expense(
        db,
        shop.id,
        crud.ExpenseCreate(
            amount=Decimal("80.00"),
            category="tea",
            note="Morning tea & snacks",
        ),
    )

    # Kannada: Ramesh debt
    res_kn_debt = auth_client.post("/api/ledger/ask", json={"query": "ರಮೇಶ್ ಎಷ್ಟು ಹಣ ಕೊಡಬೇಕು?", "language_code": "kn-IN"})
    assert res_kn_debt.status_code == 200
    d_kn_debt = res_kn_debt.json()
    assert d_kn_debt["intent"] == "customer_balance"
    assert Decimal(d_kn_debt["amount"]) == Decimal("450.00")
    assert "₹450.00" in d_kn_debt["answer"]

    # Hindi: Ramesh debt
    res_hi_debt = auth_client.post("/api/ledger/ask", json={"query": "रमेश पर कितना उधार बाकी है?", "language_code": "hi-IN"})
    assert res_hi_debt.status_code == 200
    d_hi_debt = res_hi_debt.json()
    assert d_hi_debt["intent"] == "customer_balance"
    assert Decimal(d_hi_debt["amount"]) == Decimal("450.00")
    assert "₹450.00" in d_hi_debt["answer"]

    # Kannada: Credit sales today
    res_kn_credit = auth_client.post("/api/ledger/ask", json={"query": "ಇಂದು ಎಷ್ಟು ಉದ್ಧಾರ ಕೊಟ್ಟೆ?", "language_code": "kn-IN"})
    assert res_kn_credit.status_code == 200
    d_kn_credit = res_kn_credit.json()
    assert d_kn_credit["intent"] == "credit_sales"
    assert Decimal(d_kn_credit["amount"]) == Decimal("450.00")

    # Hindi: Credit sales today
    res_hi_credit = auth_client.post("/api/ledger/ask", json={"query": "आज कितना उधार दिया?", "language_code": "hi-IN"})
    assert res_hi_credit.status_code == 200
    d_hi_credit = res_hi_credit.json()
    assert d_hi_credit["intent"] == "credit_sales"
    assert Decimal(d_hi_credit["amount"]) == Decimal("450.00")

    # Hindi: Expenses today
    res_hi_exp = auth_client.post("/api/ledger/ask", json={"query": "आज का खर्च कितना हुआ?", "language_code": "hi-IN"})
    assert res_hi_exp.status_code == 200
    d_hi_exp = res_hi_exp.json()
    assert d_hi_exp["intent"] == "expenses"
    assert Decimal(d_hi_exp["amount"]) == Decimal("80.00")


def test_voice_queries_never_save_transactions(auth_client: TestClient, db, shop, customer):
    """
    Critical requirement:
    Asking questions via text or voice transcripts must NEVER create, confirm, or save
    any transactions or change customer records.
    """
    initial_txn_count = len(crud.list_transactions(db, shop.id))
    initial_cust_count = len(crud.list_customers(db, shop.id))
    initial_expense_count = len(crud.list_expenses(db, shop.id))

    # Ask multiple queries mimicking voice transcripts
    queries = [
        "How much does Ramesh owe?",
        "ರಮೇಶ್ ಎಷ್ಟು ಹಣ ಕೊಡಬೇಕು?",
        "रमेश पर कितना उधार बाकी है?",
        "How much credit did I give today?",
        "What were my expenses today?",
        "Who owes me more than ₹1,000?",
        "Ramesh paid 500 rupees",  # Even if query sounds like a payment command, Ask Ledger must only QUERY!
    ]

    for q in queries:
        res = auth_client.post("/api/ledger/ask", json={"query": q})
        assert res.status_code == 200

    # Ensure zero side effects in the database
    assert len(crud.list_transactions(db, shop.id)) == initial_txn_count
    assert len(crud.list_customers(db, shop.id)) == initial_cust_count
    assert len(crud.list_expenses(db, shop.id)) == initial_expense_count


def test_language_preference_persistence(auth_client: TestClient, db, shop):
    """
    Test PATCH /api/auth/language updates shop preference in database,
    and GET /api/auth/me returns the updated language.
    """
    # 1. Update to Hindi
    res1 = auth_client.patch("/api/auth/language", json={"language": "hi-IN"})
    assert res1.status_code == 200
    assert res1.json()["language"] == "hi-IN"

    # Verify persisted in DB via /me
    me1 = auth_client.get("/api/auth/me")
    assert me1.status_code == 200
    assert me1.json()["language"] == "hi-IN"

    # 2. Update to Kannada
    res2 = auth_client.patch("/api/auth/language", json={"language": "kn-IN"})
    assert res2.status_code == 200
    assert res2.json()["language"] == "kn-IN"

    me2 = auth_client.get("/api/auth/me")
    assert me2.status_code == 200
    assert me2.json()["language"] == "kn-IN"


def test_first_visit_default_english_on_registration(client=None):
    """
    New shop registration default language must be English (en-IN).
    """
    from backend.main import app
    c = TestClient(app)
    res = c.post(
        "/api/auth/register",
        json={
            "name": "New English Store",
            "owner_name": "Shopkeeper",
            "phone": "+917777777777",
            "password": "securepassword123",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["language"] == "en-IN"

