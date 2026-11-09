"""
Ask Your Ledger router — natural-language queries answered from immutable database records.
Never generates hallucinated numbers. Strictly isolated by authenticated shop.
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_shop
from ..database import get_db
from ..models import Shop
from ..schemas import AskLedgerRequest, AskLedgerResponse
from ..services.ledger_assistant import answer_ledger_query

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ledger", tags=["ledger"])


@router.post("/ask", response_model=AskLedgerResponse)
def ask_ledger(
    req: AskLedgerRequest,
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    """
    Ask a natural-language question about shop finances or customer ledgers.
    Answered deterministically from real database records for this shop only.
    """
    logger.info("Ask Your Ledger: shop=%d query=%r", shop.id, req.query)
    return answer_ledger_query(
        db=db,
        shop=shop,
        query=req.query,
        language_code=req.language_code or "en-IN",
    )
