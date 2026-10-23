"""Transactions router — create (pending), confirm, list."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud
from ..auth import get_current_shop
from ..database import get_db
from ..models import Shop, TransactionType
from ..schemas import TransactionConfirm, TransactionCreate, TransactionOut

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _txn_to_out(txn, db: Session, shop_id: int) -> TransactionOut:
    customer_name = None
    if txn.customer_id:
        c = crud.get_customer(db, shop_id, txn.customer_id)
        customer_name = c.name if c else None
    return TransactionOut(
        id=txn.id, shop_id=txn.shop_id, customer_id=txn.customer_id,
        customer_name=customer_name, txn_type=txn.txn_type, amount=txn.amount,
        note=txn.note, source=txn.source, transcript=txn.transcript,
        confirmed=txn.confirmed, created_at=txn.created_at,
    )


@router.post("", response_model=TransactionOut, status_code=201)
def create_transaction(
    data: TransactionCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    """
    Creates an UNCONFIRMED transaction.
    Frontend must display a confirmation screen and call POST /confirm before saving.
    Idempotent via idempotency_key.
    """
    # Validate customer belongs to this shop
    if data.customer_id:
        c = crud.get_customer(db, shop.id, data.customer_id)
        if not c:
            raise HTTPException(status_code=404, detail="Customer not found in this shop.")

    # Validate: payment cannot exceed outstanding balance
    if data.txn_type == TransactionType.PAYMENT and data.customer_id:
        outstanding = crud.compute_customer_balance(db, shop.id, data.customer_id)
        if data.amount > outstanding:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "overpayment",
                    "message": (
                        f"Payment ₹{data.amount} exceeds outstanding balance ₹{outstanding}. "
                        "Please confirm if you want to record an overpayment."
                    ),
                    "outstanding": str(outstanding),
                },
            )

    txn = crud.create_transaction(db, shop.id, data)
    return _txn_to_out(txn, db, shop.id)


@router.post("/confirm", response_model=TransactionOut)
def confirm_transaction(
    data: TransactionConfirm,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    """
    Explicitly confirm a pending transaction. Idempotent.
    This is the ONLY path that makes a transaction permanent.
    """
    txn = crud.confirm_transaction(db, shop.id, data.transaction_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return _txn_to_out(txn, db, shop.id)


@router.get("", response_model=List[TransactionOut])
def list_transactions(
    customer_id: Optional[int] = None,
    txn_type: Optional[TransactionType] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    txns = crud.list_transactions(
        db, shop.id, customer_id=customer_id,
        txn_type=txn_type, from_date=from_date, to_date=to_date,
        limit=limit, offset=offset,
    )
    return [_txn_to_out(t, db, shop.id) for t in txns]


@router.get("/{txn_id}", response_model=TransactionOut)
def get_transaction(
    txn_id: int,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    txn = crud.get_transaction(db, shop.id, txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return _txn_to_out(txn, db, shop.id)
