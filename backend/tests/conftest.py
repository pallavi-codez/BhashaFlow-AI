"""
Pytest configuration and shared fixtures.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app
from backend import crud

# Use an in-memory SQLite DB for tests
TEST_DB_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    from backend import models  # noqa
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def shop(db):
    """Create a test shop and return it."""
    return crud.create_shop(
        db,
        name="Test Shop",
        owner_name="Owner",
        phone="+919999999999",
        password_plain="testpass",
        language="kn-IN",
    )


@pytest.fixture
def auth_client(shop):
    """TestClient with Authorization header for the test shop."""
    from backend.auth import create_access_token
    token = create_access_token(shop.id)
    client = TestClient(app)
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


@pytest.fixture
def customer(db, shop):
    from backend.schemas import CustomerCreate
    return crud.create_customer(db, shop.id, CustomerCreate(name="Ramesh"))
