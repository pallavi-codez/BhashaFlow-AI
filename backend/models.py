"""
SQLAlchemy ORM models.

Financial rules:
- All amounts stored as Numeric(12, 2) — exact decimal, never float.
- Outstanding balance is COMPUTED from ledger entries on read, never stored.
- All monetary DB writes go through transactions for atomicity.
"""
from __future__ import annotations

import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer,
    Numeric, String, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


# ── Enums ─────────────────────────────────────────────────────────────────────

class TransactionType(str, enum.Enum):
    CREDIT_SALE = "CREDIT_SALE"    # udhar given   → increases customer debt
    PAYMENT     = "PAYMENT"        # debt received → decreases customer debt
    CASH_SALE   = "CASH_SALE"      # no debt change
    EXPENSE     = "EXPENSE"        # shop expense, not a sale


class TransactionSource(str, enum.Enum):
    VOICE  = "voice"
    MANUAL = "manual"
    DEMO   = "demo"


# ── Models ────────────────────────────────────────────────────────────────────

class Shop(Base):
    __tablename__ = "shops"

    id:           Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    name:         Mapped[str]      = mapped_column(String(200), nullable=False)
    owner_name:   Mapped[str]      = mapped_column(String(200), nullable=False)
    phone:        Mapped[str]      = mapped_column(String(20), unique=True, nullable=False)
    password_hash:Mapped[str]      = mapped_column(String(200), nullable=False)
    language:     Mapped[str]      = mapped_column(String(10), default="en-IN")
    is_demo:      Mapped[bool]     = mapped_column(Boolean, default=False)
    created_at:   Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at:   Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    customers:    Mapped[list["Customer"]]    = relationship(back_populates="shop", cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="shop", cascade="all, delete-orphan")
    expenses:     Mapped[list["Expense"]]     = relationship(back_populates="shop", cascade="all, delete-orphan")
    price_list_items: Mapped[list["PriceListItem"]] = relationship(back_populates="shop", cascade="all, delete-orphan")


class Customer(Base):
    __tablename__ = "customers"

    id:         Mapped[int]            = mapped_column(Integer, primary_key=True, index=True)
    shop_id:    Mapped[int]            = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    name:       Mapped[str]            = mapped_column(String(200), nullable=False)
    phone:      Mapped[str | None]     = mapped_column(String(20), nullable=True)
    notes:      Mapped[str | None]     = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime]       = mapped_column(DateTime, server_default=func.now())

    shop:         Mapped["Shop"]           = relationship(back_populates="customers")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="customer")

    __table_args__ = (
        UniqueConstraint("shop_id", "name", name="uq_customer_name_per_shop"),
    )


class Transaction(Base):
    """
    Single immutable ledger entry.
    Balances are always derived from SUM of entries — never from a cached field.
    """
    __tablename__ = "transactions"

    id:            Mapped[int]                 = mapped_column(Integer, primary_key=True, index=True)
    shop_id:       Mapped[int]                 = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    customer_id:   Mapped[int | None]          = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    txn_type:      Mapped[TransactionType]     = mapped_column(Enum(TransactionType), nullable=False)
    amount:        Mapped[Decimal]             = mapped_column(Numeric(12, 2), nullable=False)
    note:          Mapped[str | None]          = mapped_column(Text, nullable=True)
    source:        Mapped[TransactionSource]   = mapped_column(Enum(TransactionSource), default=TransactionSource.MANUAL)
    transcript:    Mapped[str | None]          = mapped_column(Text, nullable=True)  # original STT text
    items_data:    Mapped[str | None]          = mapped_column(Text, nullable=True)  # JSON-serialized items
    idempotency_key: Mapped[str | None]        = mapped_column(String(64), unique=True, nullable=True)
    confirmed:     Mapped[bool]                = mapped_column(Boolean, default=False)  # True = user confirmed
    created_at:    Mapped[datetime]            = mapped_column(DateTime, server_default=func.now())

    shop:     Mapped["Shop"]          = relationship(back_populates="transactions")
    customer: Mapped["Customer | None"] = relationship(back_populates="transactions")


class Expense(Base):
    """
    Shop expenses (rent, supplies, utilities, transport, tea/snacks, misc).
    """
    __tablename__ = "expenses"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    shop_id:    Mapped[int]      = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    amount:     Mapped[Decimal]  = mapped_column(Numeric(12, 2), nullable=False)
    category:   Mapped[str]      = mapped_column(String(100), default="supplies")
    note:       Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shop: Mapped["Shop"] = relationship(back_populates="expenses")


class PriceListItem(Base):
    """
    Shop's saved price list for standard grocery items.
    Allows automatic extraction of unit prices and line totals from spoken item names.
    """
    __tablename__ = "price_list_items"

    id:         Mapped[int]     = mapped_column(Integer, primary_key=True, index=True)
    shop_id:    Mapped[int]     = mapped_column(ForeignKey("shops.id", ondelete="CASCADE"), nullable=False)
    item_name:  Mapped[str]     = mapped_column(String(200), nullable=False)
    unit:       Mapped[str]     = mapped_column(String(50), default="kg")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    shop: Mapped["Shop"] = relationship(back_populates="price_list_items")

    __table_args__ = (
        UniqueConstraint("shop_id", "item_name", name="uq_shop_item_price"),
    )
