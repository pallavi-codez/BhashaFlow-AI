"""
Pydantic schemas — request / response contracts.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import TransactionSource, TransactionType


# ── Auth ──────────────────────────────────────────────────────────────────────

class ShopRegisterRequest(BaseModel):
    name:       str = Field(..., min_length=2, max_length=200)
    owner_name: str = Field(..., min_length=2, max_length=200)
    phone:      str = Field(..., pattern=r"^\+?[0-9]{10,15}$")
    password:   str = Field(..., min_length=6)
    language:   str = Field("en-IN")


class ShopLoginRequest(BaseModel):
    phone:    str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    shop_id:      int
    shop_name:    str
    is_demo:      bool = False
    language:     str = "en-IN"


class ShopLanguageUpdateRequest(BaseModel):
    language: str = Field(..., min_length=2, max_length=10)


class ShopOut(BaseModel):
    id:         int
    name:       str
    owner_name: str
    phone:      str
    language:   str
    is_demo:    bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


# ── Item ───────────────────────────────────────────────────────────────────────

class ParsedItem(BaseModel):
    name:        str
    quantity:    Optional[Decimal] = None
    unit:        Optional[str]     = None
    unit_price:  Optional[Decimal] = None
    total_price: Optional[Decimal] = None


# ── Transaction ───────────────────────────────────────────────────────────────

class TransactionCreate(BaseModel):
    customer_id:       Optional[int]   = None
    txn_type:          TransactionType
    amount:            Decimal         = Field(..., gt=0, decimal_places=2)
    items:             Optional[list[ParsedItem]] = None
    note:              Optional[str]   = None
    source:            TransactionSource = TransactionSource.MANUAL
    transcript:        Optional[str]   = None
    idempotency_key:   Optional[str]   = None   # client-generated UUID
    allow_overpayment: bool            = False

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
    items:           Optional[list[ParsedItem]] = None
    note:            Optional[str]
    source:          TransactionSource
    transcript:      Optional[str]
    confirmed:       bool
    created_at:      datetime

    model_config = ConfigDict(from_attributes=True)


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
    txn_type:            Optional[TransactionType] = None
    customer_name:       Optional[str]             = None
    matched_customer_id: Optional[int]             = None
    candidate_customers: list[str]                 = Field(default_factory=list)
    amount:              Optional[Decimal]         = None
    items:               list[ParsedItem]          = Field(default_factory=list)
    note:                Optional[str]             = None
    confidence:          float                     = 0.0   # 0-1
    ambiguous:           bool                      = False
    ambiguity_reason:    Optional[str]             = None


# ── Expense ───────────────────────────────────────────────────────────────────

class ExpenseCreate(BaseModel):
    amount:   Decimal       = Field(..., gt=0, decimal_places=2)
    category: str           = Field("supplies", max_length=100)
    note:     Optional[str] = None


class ExpenseOut(BaseModel):
    id:         int
    shop_id:    int
    amount:     Decimal
    category:   str
    note:       Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Price List ────────────────────────────────────────────────────────────────

class PriceListItemCreate(BaseModel):
    item_name:  str     = Field(..., min_length=1, max_length=200)
    unit:       str     = Field("kg", max_length=50)
    unit_price: Decimal = Field(..., gt=0)


class PriceListItemOut(BaseModel):
    id:         int
    shop_id:    int
    item_name:  str
    unit:       str
    unit_price: Decimal
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Ask Your Ledger ───────────────────────────────────────────────────────────

class AskLedgerRequest(BaseModel):
    query:         str = Field(..., min_length=1, max_length=500)
    language_code: Optional[str] = "en-IN"


class LedgerQueryDetailItem(BaseModel):
    id:     Optional[int]     = None
    name:   Optional[str]     = None
    amount: Optional[Decimal] = None
    type:   Optional[str]     = None
    date:   Optional[str]     = None
    extra:  Optional[str]     = None


class AskLedgerResponse(BaseModel):
    query:                str
    intent:               str
    answer:               str
    amount:               Optional[Decimal]               = None
    details:              list[LedgerQueryDetailItem]     = Field(default_factory=list)
    clarification_needed: bool                            = False
    candidates:           list[str]                       = Field(default_factory=list)
    no_records:           bool                            = False
