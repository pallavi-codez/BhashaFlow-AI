"""Customers router."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud
from ..auth import get_current_shop
from ..database import get_db
from ..models import Shop
from ..schemas import CustomerCreate, CustomerOut

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("", response_model=List[CustomerOut])
def list_customers(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    customers = crud.list_customers(db, shop.id, search=search)
    results = []
    for c in customers:
        balance = crud.compute_customer_balance(db, shop.id, c.id)
        out = CustomerOut(
            id=c.id, name=c.name, phone=c.phone, notes=c.notes,
            outstanding_balance=balance, created_at=c.created_at,
        )
        results.append(out)
    return results


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    existing = crud.get_customer_by_name(db, shop.id, data.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Customer '{data.name}' already exists.")
    c = crud.create_customer(db, shop.id, data)
    balance = crud.compute_customer_balance(db, shop.id, c.id)
    return CustomerOut(id=c.id, name=c.name, phone=c.phone, notes=c.notes,
                       outstanding_balance=balance, created_at=c.created_at)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    c = crud.get_customer(db, shop.id, customer_id)
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found.")
    balance = crud.compute_customer_balance(db, shop.id, c.id)
    return CustomerOut(id=c.id, name=c.name, phone=c.phone, notes=c.notes,
                       outstanding_balance=balance, created_at=c.created_at)
