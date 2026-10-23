"""Dashboard router."""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud
from ..auth import get_current_shop
from ..database import get_db
from ..models import Shop
from ..schemas import DashboardStats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardStats)
def get_dashboard(
    target_date: Optional[date] = None,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    stats = crud.get_dashboard_stats(db, shop.id, target_date)
    return DashboardStats(**stats)
