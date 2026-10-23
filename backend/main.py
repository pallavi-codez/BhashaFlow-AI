"""
BhashaFlow AI — FastAPI application entry point.
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .routers import auth, customers, dashboard, expenses, languages, stt, transactions, tts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising database …")
    init_db()
    logger.info("BhashaFlow AI backend ready.")
    yield


app = FastAPI(
    title="BhashaFlow AI API",
    description="Voice-Powered Udhar Ledger for Local Grocery Shops — Gnani AI Powered",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(stt.router)
app.include_router(tts.router)
app.include_router(expenses.router)
app.include_router(languages.router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "BhashaFlow AI"}
