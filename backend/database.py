"""
SQLAlchemy engine & session factory.
Uses SQLite for local MVP; change DATABASE_URL to postgres:// for production.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,
    future=True,
)

# Enable SQLite foreign key enforcement
if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a DB session and closes after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables (run once on startup) and migrate columns if necessary."""
    from . import models  # noqa: F401 — import to register models
    Base.metadata.create_all(bind=engine)
    
    # Safe migration for existing SQLite database
    try:
        with engine.connect() as conn:
            tables = [r[0] for r in conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            if "transactions" in tables:
                cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(transactions)").fetchall()]
                if "items_data" not in cols:
                    conn.exec_driver_sql("ALTER TABLE transactions ADD COLUMN items_data TEXT")
                    conn.commit()
    except Exception:
        pass
