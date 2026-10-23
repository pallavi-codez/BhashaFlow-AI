"""Auth router — register + login."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud
from ..auth import create_access_token
from ..database import get_db
from ..schemas import ShopLoginRequest, ShopRegisterRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: ShopRegisterRequest, db: Session = Depends(get_db)):
    existing = crud.get_shop_by_phone(db, data.phone)
    if existing:
        raise HTTPException(status_code=409, detail="Phone number already registered.")
    shop = crud.create_shop(
        db,
        name=data.name,
        owner_name=data.owner_name,
        phone=data.phone,
        password_plain=data.password,
        language=data.language,
    )
    token = create_access_token(shop.id)
    return TokenResponse(access_token=token, shop_id=shop.id, shop_name=shop.name)


@router.post("/login", response_model=TokenResponse)
def login(data: ShopLoginRequest, db: Session = Depends(get_db)):
    shop = crud.get_shop_by_phone(db, data.phone)
    if not shop or not crud.verify_password(data.password, shop.password_hash):
        raise HTTPException(status_code=401, detail="Invalid phone or password.")
    token = create_access_token(shop.id)
    return TokenResponse(access_token=token, shop_id=shop.id, shop_name=shop.name)


@router.post("/demo", response_model=TokenResponse)
def demo_login(db: Session = Depends(get_db)):
    """Create / reuse a demo shop pre-loaded with sample data."""
    shop = crud.get_shop_by_phone(db, "+910000000000")
    if not shop:
        shop = crud.create_shop(
            db,
            name="Demo Kirana Store",
            owner_name="Demo Shopkeeper",
            phone="+910000000000",
            password_plain="demo1234",
            language="kn-IN",
            is_demo=True,
        )
        _seed_demo(db, shop.id)
    token = create_access_token(shop.id)
    return TokenResponse(access_token=token, shop_id=shop.id, shop_name=shop.name)


def _seed_demo(db: Session, shop_id: int) -> None:
    """Insert clearly-labelled synthetic demo data."""
    from decimal import Decimal
    from ..models import TransactionSource, TransactionType
    from ..schemas import CustomerCreate, TransactionCreate

    customers_data = [
        ("Ramesh [DEMO]", "+919876543210"),
        ("Suresh [DEMO]", "+919876543211"),
        ("Lakshmi [DEMO]", "+919876543212"),
        ("Ganesh [DEMO]", "+919876543213"),
        ("Meena [DEMO]",  "+919876543214"),
    ]
    customers = []
    for name, phone in customers_data:
        c = crud.create_customer(db, shop_id, CustomerCreate(name=name, phone=phone))
        customers.append(c)

    import datetime
    today = datetime.date.today()

    sample_txns = [
        (customers[0].id, TransactionType.CREDIT_SALE, Decimal("350"), "Rice and dal"),
        (customers[0].id, TransactionType.CREDIT_SALE, Decimal("500"), "Oil and spices"),
        (customers[0].id, TransactionType.PAYMENT,     Decimal("300"), "Partial payment"),
        (customers[1].id, TransactionType.CREDIT_SALE, Decimal("850"), "Groceries"),
        (customers[1].id, TransactionType.PAYMENT,     Decimal("200"), "Payment received"),
        (customers[2].id, TransactionType.CREDIT_SALE, Decimal("620"), "Monthly supplies"),
        (customers[3].id, TransactionType.CREDIT_SALE, Decimal("400"), "Vegetables"),
        (customers[4].id, TransactionType.CREDIT_SALE, Decimal("150"), "Biscuits and snacks"),
        (None,            TransactionType.CASH_SALE,   Decimal("800"), "Cash sale — multiple items"),
        (None,            TransactionType.EXPENSE,      Decimal("250"), "Shop supplies expense"),
    ]

    for cust_id, txn_type, amount, note in sample_txns:
        txn_data = TransactionCreate(
            customer_id=cust_id,
            txn_type=txn_type,
            amount=amount,
            note=f"[DEMO] {note}",
            source=TransactionSource.DEMO,
        )
        txn = crud.create_transaction(db, shop_id, txn_data)
        crud.confirm_transaction(db, shop_id, txn.id)
