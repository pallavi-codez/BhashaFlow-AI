"""
CRUD — database operations.
All monetary arithmetic uses Python Decimal; SQL aggregations use NUMERIC columns.
Balances are always computed from ledger entries, never from a cached column.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Customer, Expense, Shop, Transaction, TransactionSource, TransactionType
from .schemas import CustomerCreate, ExpenseCreate, TransactionCreate


# ── Password hashing ──────────────────────────────────────────────────────────

import bcrypt


def hash_password(plain: str) -> str:
    pwd_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


# ── Shop ──────────────────────────────────────────────────────────────────────

def get_shop_by_phone(db: Session, phone: str) -> Optional[Shop]:
    return db.scalars(select(Shop).where(Shop.phone == phone)).first()


def get_shop_by_id(db: Session, shop_id: int) -> Optional[Shop]:
    return db.get(Shop, shop_id)


def create_shop(
    db: Session,
    name: str,
    owner_name: str,
    phone: str,
    password_plain: str,
    language: str = "kn-IN",
    is_demo: bool = False,
) -> Shop:
    shop = Shop(
        name=name,
        owner_name=owner_name,
        phone=phone,
        password_hash=hash_password(password_plain),
        language=language,
        is_demo=is_demo,
    )
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop


# ── Customer ──────────────────────────────────────────────────────────────────

def get_customer(db: Session, shop_id: int, customer_id: int) -> Optional[Customer]:
    return db.scalars(
        select(Customer).where(Customer.id == customer_id, Customer.shop_id == shop_id)
    ).first()


def get_customer_by_name(db: Session, shop_id: int, name: str) -> Optional[Customer]:
    return db.scalars(
        select(Customer).where(
            Customer.shop_id == shop_id,
            func.lower(Customer.name) == name.lower(),
        )
    ).first()


def list_customers(db: Session, shop_id: int, search: Optional[str] = None) -> list[Customer]:
    q = select(Customer).where(Customer.shop_id == shop_id)
    if search:
        q = q.where(Customer.name.ilike(f"%{search}%"))
    return list(db.scalars(q.order_by(Customer.name)).all())


def create_customer(db: Session, shop_id: int, data: CustomerCreate) -> Customer:
    customer = Customer(shop_id=shop_id, name=data.name, phone=data.phone, notes=data.notes)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def get_or_create_customer(db: Session, shop_id: int, name: str) -> Customer:
    existing = get_customer_by_name(db, shop_id, name)
    if existing:
        return existing
    from .schemas import CustomerCreate as CC
    return create_customer(db, shop_id, CC(name=name))


# ── Balance computation ────────────────────────────────────────────────────────

def compute_customer_balance(db: Session, shop_id: int, customer_id: int) -> Decimal:
    """
    Outstanding = SUM(CREDIT_SALE amounts) - SUM(PAYMENT amounts)
    for confirmed transactions only.
    Never uses a cached balance field.
    """
    credit_q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.shop_id    == shop_id,
        Transaction.customer_id == customer_id,
        Transaction.txn_type   == TransactionType.CREDIT_SALE,
        Transaction.confirmed  == True,  # noqa: E712
    )
    payment_q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
        Transaction.shop_id    == shop_id,
        Transaction.customer_id == customer_id,
        Transaction.txn_type   == TransactionType.PAYMENT,
        Transaction.confirmed  == True,  # noqa: E712
    )
    credits  = db.scalar(credit_q) or Decimal("0")
    payments = db.scalar(payment_q) or Decimal("0")
    return Decimal(str(credits)) - Decimal(str(payments))


def compute_total_outstanding(db: Session, shop_id: int) -> Decimal:
    """Sum of all customer outstanding balances for the shop."""
    credits = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.shop_id  == shop_id,
            Transaction.txn_type == TransactionType.CREDIT_SALE,
            Transaction.confirmed == True,  # noqa: E712
        )
    ) or Decimal("0")
    payments = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.shop_id  == shop_id,
            Transaction.txn_type == TransactionType.PAYMENT,
            Transaction.confirmed == True,  # noqa: E712
        )
    ) or Decimal("0")
    return Decimal(str(credits)) - Decimal(str(payments))


# ── Transaction ───────────────────────────────────────────────────────────────

def get_transaction(db: Session, shop_id: int, txn_id: int) -> Optional[Transaction]:
    return db.scalars(
        select(Transaction).where(Transaction.id == txn_id, Transaction.shop_id == shop_id)
    ).first()


def get_transaction_by_idempotency_key(db: Session, key: str) -> Optional[Transaction]:
    if not key:
        return None
    return db.scalars(select(Transaction).where(Transaction.idempotency_key == key)).first()


def create_transaction(db: Session, shop_id: int, data: TransactionCreate) -> Transaction:
    """
    Creates an UNCONFIRMED transaction.
    The caller must explicitly call confirm_transaction() after user review.
    Idempotency: if a transaction with the same idempotency_key already exists,
    return the existing record without creating a duplicate.
    """
    if data.idempotency_key:
        existing = get_transaction_by_idempotency_key(db, data.idempotency_key)
        if existing:
            return existing

    txn = Transaction(
        shop_id=shop_id,
        customer_id=data.customer_id,
        txn_type=data.txn_type,
        amount=data.amount,
        note=data.note,
        source=data.source,
        transcript=data.transcript,
        idempotency_key=data.idempotency_key,
        confirmed=False,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


def confirm_transaction(db: Session, shop_id: int, txn_id: int) -> Optional[Transaction]:
    """
    Mark a pending transaction as confirmed.
    Idempotent: calling multiple times on an already-confirmed txn is safe.
    """
    txn = get_transaction(db, shop_id, txn_id)
    if txn is None:
        return None
    if not txn.confirmed:
        txn.confirmed = True
        db.commit()
        db.refresh(txn)
    return txn


def list_transactions(
    db: Session,
    shop_id: int,
    customer_id: Optional[int] = None,
    txn_type: Optional[TransactionType] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Transaction]:
    q = select(Transaction).where(
        Transaction.shop_id   == shop_id,
        Transaction.confirmed == True,  # noqa: E712
    )
    if customer_id:
        q = q.where(Transaction.customer_id == customer_id)
    if txn_type:
        q = q.where(Transaction.txn_type == txn_type)
    if from_date:
        q = q.where(Transaction.created_at >= datetime(from_date.year, from_date.month, from_date.day))
    if to_date:
        next_day = to_date + timedelta(days=1)
        q = q.where(Transaction.created_at < datetime(next_day.year, next_day.month, next_day.day))
    q = q.order_by(Transaction.created_at.desc()).limit(limit).offset(offset)
    return list(db.scalars(q).all())


# ── Dashboard aggregations ────────────────────────────────────────────────────

def _sum_today(db: Session, shop_id: int, txn_type: TransactionType, target_date: date) -> Decimal:
    start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    end   = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, 999999)
    result = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.shop_id   == shop_id,
            Transaction.txn_type  == txn_type,
            Transaction.confirmed == True,  # noqa: E712
            Transaction.created_at >= start,
            Transaction.created_at <= end,
        )
    )
    return Decimal(str(result or 0))


def _sum_expenses_today(db: Session, shop_id: int, target_date: date) -> Decimal:
    start = datetime(target_date.year, target_date.month, target_date.day, 0, 0, 0)
    end   = datetime(target_date.year, target_date.month, target_date.day, 23, 59, 59, 999999)
    txn_expenses = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.shop_id   == shop_id,
            Transaction.txn_type  == TransactionType.EXPENSE,
            Transaction.confirmed == True,  # noqa: E712
            Transaction.created_at >= start,
            Transaction.created_at <= end,
        )
    ) or 0
    direct_expenses = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.shop_id == shop_id,
            Expense.created_at >= start,
            Expense.created_at <= end,
        )
    ) or 0
    return Decimal(str(txn_expenses)) + Decimal(str(direct_expenses))


def get_dashboard_stats(db: Session, shop_id: int, target_date: Optional[date] = None) -> dict:
    today = target_date or date.today()

    credit_today  = _sum_today(db, shop_id, TransactionType.CREDIT_SALE, today)
    cash_today    = _sum_today(db, shop_id, TransactionType.CASH_SALE,   today)
    payment_today = _sum_today(db, shop_id, TransactionType.PAYMENT,     today)
    expense_today = _sum_expenses_today(db, shop_id, today)

    # Today's cash received = cash sales + debt payments received today
    cash_received = cash_today + payment_today
    # Net cash movement = cash received - expenses
    net_cash = cash_received - expense_today

    # Count confirmed transactions today
    start = datetime(today.year, today.month, today.day, 0, 0, 0)
    end   = datetime(today.year, today.month, today.day, 23, 59, 59, 999999)
    txn_count = db.scalar(
        select(func.count(Transaction.id)).where(
            Transaction.shop_id   == shop_id,
            Transaction.confirmed == True,  # noqa: E712
            Transaction.created_at >= start,
            Transaction.created_at <= end,
        )
    ) or 0

    customer_count = db.scalar(
        select(func.count(Customer.id)).where(Customer.shop_id == shop_id)
    ) or 0

    total_outstanding = compute_total_outstanding(db, shop_id)

    return {
        "date":                     today.isoformat(),
        "total_credit_sales":       credit_today,
        "total_cash_sales":         cash_today,
        "total_payments_received":  payment_today,
        "total_cash_received":      cash_received,
        "total_expenses":           expense_today,
        "total_outstanding":        total_outstanding,
        "net_cash_movement":        net_cash,
        "total_customers":          customer_count,
        "total_transactions_today": txn_count,
    }


# ── Expense CRUD ──────────────────────────────────────────────────────────────

def create_expense(db: Session, shop_id: int, data: ExpenseCreate) -> Expense:
    expense = Expense(
        shop_id=shop_id,
        amount=data.amount,
        category=data.category or "supplies",
        note=data.note,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


def list_expenses(
    db: Session,
    shop_id: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 50,
) -> list[Expense]:
    q = select(Expense).where(Expense.shop_id == shop_id)
    if from_date:
        q = q.where(Expense.created_at >= datetime(from_date.year, from_date.month, from_date.day))
    if to_date:
        next_day = to_date + timedelta(days=1)
        q = q.where(Expense.created_at < datetime(next_day.year, next_day.month, next_day.day))
    q = q.order_by(Expense.created_at.desc()).limit(limit)
    return list(db.scalars(q).all())


def delete_expense(db: Session, shop_id: int, expense_id: int) -> bool:
    expense = db.scalars(select(Expense).where(Expense.id == expense_id, Expense.shop_id == shop_id)).first()
    if not expense:
        return False
    db.delete(expense)
    db.commit()
    return True
