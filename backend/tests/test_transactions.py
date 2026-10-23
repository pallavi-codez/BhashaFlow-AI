"""
Tests for transaction logic, balance calculations, and dashboard aggregations.
All tests use in-memory SQLite — no external API calls.
"""
from decimal import Decimal
import pytest
from backend import crud
from backend.models import TransactionSource, TransactionType
from backend.schemas import CustomerCreate, TransactionCreate


def make_txn(db, shop_id, customer_id, txn_type, amount, *, confirm=True, source=TransactionSource.MANUAL):
    data = TransactionCreate(
        customer_id=customer_id,
        txn_type=txn_type,
        amount=Decimal(str(amount)),
        source=source,
    )
    txn = crud.create_transaction(db, shop_id, data)
    if confirm:
        crud.confirm_transaction(db, shop_id, txn.id)
    return txn


# ── Credit sales ──────────────────────────────────────────────────────────────

class TestCreditSales:
    def test_credit_increases_balance(self, db, shop, customer):
        make_txn(db, shop.id, customer.id, TransactionType.CREDIT_SALE, 500)
        balance = crud.compute_customer_balance(db, shop.id, customer.id)
        assert balance == Decimal("500")

    def test_multiple_credits_accumulate(self, db, shop, customer):
        make_txn(db, shop.id, customer.id, TransactionType.CREDIT_SALE, 300)
        make_txn(db, shop.id, customer.id, TransactionType.CREDIT_SALE, 200)
        balance = crud.compute_customer_balance(db, shop.id, customer.id)
        assert balance == Decimal("500")

    def test_unconfirmed_credit_not_counted(self, db, shop, customer):
        make_txn(db, shop.id, customer.id, TransactionType.CREDIT_SALE, 500, confirm=False)
        balance = crud.compute_customer_balance(db, shop.id, customer.id)
        assert balance == Decimal("0")


# ── Payments ──────────────────────────────────────────────────────────────────

class TestPayments:
    def test_payment_reduces_balance(self, db, shop, customer):
        make_txn(db, shop.id, customer.id, TransactionType.CREDIT_SALE, 700)
        make_txn(db, shop.id, customer.id, TransactionType.PAYMENT,     200)
        balance = crud.compute_customer_balance(db, shop.id, customer.id)
        assert balance == Decimal("500")

    def test_full_payment_clears_balance(self, db, shop, customer):
        make_txn(db, shop.id, customer.id, TransactionType.CREDIT_SALE, 500)
        make_txn(db, shop.id, customer.id, TransactionType.PAYMENT,     500)
        balance = crud.compute_customer_balance(db, shop.id, customer.id)
        assert balance == Decimal("0")

    def test_payment_not_counted_as_sale(self, db, shop, customer):
        """Dashboard credit-sales total must NOT include payment entries."""
        import datetime
        make_txn(db, shop.id, customer.id, TransactionType.CREDIT_SALE, 500)
        make_txn(db, shop.id, customer.id, TransactionType.PAYMENT,     200)
        stats = crud.get_dashboard_stats(db, shop.id, datetime.date.today())
        assert stats["total_credit_sales"] == Decimal("500")
        assert stats["total_payments_received"] == Decimal("200")
        # Payment must not affect cash-sale total
        assert stats["total_cash_sales"] == Decimal("0")


# ── Cash sales ────────────────────────────────────────────────────────────────

class TestCashSales:
    def test_cash_sale_not_added_to_debt(self, db, shop, customer):
        make_txn(db, shop.id, None, TransactionType.CASH_SALE, 300)
        # No customer_id → no debt
        balance = crud.compute_customer_balance(db, shop.id, customer.id)
        assert balance == Decimal("0")

    def test_cash_sale_in_dashboard(self, db, shop):
        import datetime
        make_txn(db, shop.id, None, TransactionType.CASH_SALE, 400)
        stats = crud.get_dashboard_stats(db, shop.id, datetime.date.today())
        assert stats["total_cash_sales"] == Decimal("400")
        assert stats["total_credit_sales"] == Decimal("0")


# ── Expenses ──────────────────────────────────────────────────────────────────

class TestExpenses:
    def test_expense_excluded_from_sales(self, db, shop):
        import datetime
        make_txn(db, shop.id, None, TransactionType.EXPENSE, 150)
        stats = crud.get_dashboard_stats(db, shop.id, datetime.date.today())
        assert stats["total_expenses"] == Decimal("150")
        assert stats["total_cash_sales"]   == Decimal("0")
        assert stats["total_credit_sales"] == Decimal("0")

    def test_net_cash_movement(self, db, shop, customer):
        """net_cash = cash_sales + payments_received - expenses"""
        import datetime
        make_txn(db, shop.id, None,        TransactionType.CASH_SALE,   300)
        make_txn(db, shop.id, customer.id, TransactionType.CREDIT_SALE, 500)
        make_txn(db, shop.id, customer.id, TransactionType.PAYMENT,     200)
        make_txn(db, shop.id, None,        TransactionType.EXPENSE,     100)
        stats = crud.get_dashboard_stats(db, shop.id, datetime.date.today())
        # cash_received = 300 (cash) + 200 (payment) = 500
        assert stats["total_cash_received"] == Decimal("500")
        # net_cash = 500 - 100 = 400
        assert stats["net_cash_movement"] == Decimal("400")


# ── Idempotency / duplicates ───────────────────────────────────────────────────

class TestIdempotency:
    def test_duplicate_idempotency_key_returns_same_txn(self, db, shop, customer):
        data = TransactionCreate(
            customer_id=customer.id,
            txn_type=TransactionType.CREDIT_SALE,
            amount=Decimal("300"),
            idempotency_key="unique-key-abc",
        )
        t1 = crud.create_transaction(db, shop.id, data)
        t2 = crud.create_transaction(db, shop.id, data)
        assert t1.id == t2.id

    def test_confirm_idempotent(self, db, shop, customer):
        """Calling confirm twice doesn't create extra state changes."""
        data = TransactionCreate(
            customer_id=customer.id,
            txn_type=TransactionType.CREDIT_SALE,
            amount=Decimal("500"),
        )
        txn = crud.create_transaction(db, shop.id, data)
        crud.confirm_transaction(db, shop.id, txn.id)
        crud.confirm_transaction(db, shop.id, txn.id)  # second call — still safe
        balance = crud.compute_customer_balance(db, shop.id, customer.id)
        assert balance == Decimal("500")


# ── Dashboard date filtering ───────────────────────────────────────────────────

class TestDashboardDateFilter:
    def test_only_todays_transactions_counted(self, db, shop, customer):
        """Dashboard should only count today's transactions for daily totals."""
        import datetime
        make_txn(db, shop.id, customer.id, TransactionType.CREDIT_SALE, 300)
        stats = crud.get_dashboard_stats(db, shop.id, datetime.date.today())
        # Today's credit = 300
        assert stats["total_credit_sales"] == Decimal("300")
        # Previous day should show 0
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        stats_yesterday = crud.get_dashboard_stats(db, shop.id, yesterday)
        assert stats_yesterday["total_credit_sales"] == Decimal("0")


# ── Amount validation ──────────────────────────────────────────────────────────

class TestAmountValidation:
    def test_zero_amount_rejected(self):
        with pytest.raises(Exception):
            TransactionCreate(
                customer_id=1,
                txn_type=TransactionType.CREDIT_SALE,
                amount=Decimal("0"),
            )

    def test_negative_amount_rejected(self):
        with pytest.raises(Exception):
            TransactionCreate(
                customer_id=1,
                txn_type=TransactionType.CREDIT_SALE,
                amount=Decimal("-100"),
            )


# ── Outstanding total ──────────────────────────────────────────────────────────

class TestOutstandingTotal:
    def test_total_outstanding_across_customers(self, db, shop):
        c1 = crud.create_customer(db, shop.id, CustomerCreate(name="Alice"))
        c2 = crud.create_customer(db, shop.id, CustomerCreate(name="Bob"))
        make_txn(db, shop.id, c1.id, TransactionType.CREDIT_SALE, 500)
        make_txn(db, shop.id, c2.id, TransactionType.CREDIT_SALE, 300)
        make_txn(db, shop.id, c1.id, TransactionType.PAYMENT,     100)
        total = crud.compute_total_outstanding(db, shop.id)
        # (500-100) + 300 = 700
        assert total == Decimal("700")
