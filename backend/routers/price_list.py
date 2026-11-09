"""Price list router — manage shop's price catalog for automatic voice item pricing."""
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud
from ..auth import get_current_shop
from ..database import get_db
from ..models import Shop
from ..schemas import PriceListItemCreate, PriceListItemOut

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.get("", response_model=List[PriceListItemOut])
def list_prices(
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    """List saved items and their prices for this shop."""
    return crud.get_price_list_items(db, shop.id)


@router.post("", response_model=PriceListItemOut, status_code=201)
def set_price(
    data: PriceListItemCreate,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    """Add or update an item price in the shop's price list."""
    return crud.create_or_update_price_list_item(
        db, shop.id, data.item_name, data.unit, data.unit_price
    )
