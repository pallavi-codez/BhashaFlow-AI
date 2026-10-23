"""
Pydantic schemas — request / response contracts.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .models import TransactionSource, TransactionType


# ── Auth ──────────────────────────────────────────────────────────────────────

class ShopRegisterRequest(BaseModel):
    name:       str = Field(..., min_length=2, max_length=200)
    owner_name: str = Field(..., min_length=2, max_length=200)
    phone:      str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    password:   str = Field(..., min_length=6)
    language:   str = Field("kn-IN")


class ShopLoginRequest(BaseModel):
    phone:    str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    shop_id:      int
    shop_name:    str


class ShopOut(BaseModel):
    id:         int
    name:       str
    owner_name: str
    phone:      str
    language:   str
    is_demo:    bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Customer ──────────────────────────────────────────────────────────────────

class CustomerCreate(BaseModel):
    name:  str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{10,15}$")
    notes: Optional[str] = None


class CustomerOut(BaseModel):
    id:              int
    name:            str
    phone:           Optional[str]
    notes:           Optional[str]
    outstanding_balance: Decimal = Decimal("0")
    created_at:      datetime

    class Config:
        from_attributes = True


# ── Transaction ───────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    customer_id:      Optional[int]   = None
    txn_type:         TransactionType
    amount:           Decimal         = Field(..., gt=0, decimal_places=2)
    note:             Optional[str]   = None
    source:           TransactionSource = TransactionSource.MANUAL
    transcript:       Optional[str]   = None
    idempotency_key:  Optional[str]   = None   # client-generated UUID

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be greater than zero")
        return v


class TransactionConfirm(BaseModel):
    """Confirm a pending (unconfirmed) transaction by id."""
    transaction_id:  int
    idempotency_key: Optional[str] = None


class TransactionOut(BaseModel):
    id:              int
    shop_id:         int
    customer_id:     Optional[int]
    customer_name:   Optional[str]
    txn_type:        TransactionType
    amount:          Decimal
    note:            Optional[str]
    source:          TransactionSource
    transcript:      Optional[str]
    confirmed:       bool
    created_at:      datetime

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    date:                    str
    total_credit_sales:      Decimal   # udhar given today
    total_cash_sales:        Decimal   # cash sales today
    total_payments_received: Decimal   # debt collected today
    total_cash_received:     Decimal   # cash_sales + payments_received
    total_expenses:          Decimal
    total_outstanding:       Decimal   # all-time: credit_sales - payments
    net_cash_movement:       Decimal   # cash_received - expenses
    total_customers:         int
    total_transactions_today: int


# ── STT ───────────────────────────────────────────────────────────────────────

class STTResponse(BaseModel):
    success:     bool
    transcript:  Optional[str]
    request_id:  Optional[str]
    language_code: str
    error:       Optional[str] = None


# ── TTS ───────────────────────────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text:     str = Field(..., min_length=1, max_length=2000)
    language: str = Field("kn-IN")
    voice:    str = Field("Kaveri")
    model:    str = Field("timbre-v2.5")
    speed:    float = Field(1.0, ge=0.5, le=2.0)


# ── Parser ────────────────────────────────────────────────────────────────────

class ParsedTransaction(BaseModel):
    txn_type:      Optional[TransactionType] = None
    customer_name: Optional[str]             = None
    amount:        Optional[Decimal]         = None
    note:          Optional[str]             = None
    confidence:    float                     = 0.0   # 0-1
    ambiguous:     bool                      = False
    ambiguity_reason: Optional[str]          = None
