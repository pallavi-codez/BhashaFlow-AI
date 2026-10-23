"""Expenses router."""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud
from ..auth import get_current_shop
from ..database import get_db
from ..models import Shop
from ..schemas import ExpenseCreate, ExpenseOut

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.get("", response_model=List[ExpenseOut])
def list_expenses(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    return crud.list_expenses(db, shop.id, from_date=from_date, to_date=to_date, limit=limit)


@router.post("", response_model=ExpenseOut, status_code=201)
def create_expense(
    data: ExpenseCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    return crud.create_expense(db, shop.id, data)


@router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    deleted = crud.delete_expense(db, shop.id, expense_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Expense not found.")
    return None
