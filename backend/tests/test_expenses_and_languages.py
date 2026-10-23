"""
Tests for Expenses and Languages endpoints.
"""
from decimal import Decimal
import pytest
from backend import crud
from backend.languages import SUPPORTED_LANGUAGES


def test_list_languages(auth_client):
    response = auth_client.get("/api/languages")
    assert response.status_code == 200
    langs = response.json()
    assert len(langs) == len(SUPPORTED_LANGUAGES)
    codes = [l["code"] for l in langs]
    assert "kn-IN" in codes
    assert "hi-IN" in codes
    assert "ur-IN" in codes
    urdu = next(l for l in langs if l["code"] == "ur-IN")
    assert urdu["text_direction"] == "rtl"


def test_get_single_language(auth_client):
    response = auth_client.get("/api/languages/kn-IN")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Kannada"
    assert data["native_name"] == "ಕನ್ನಡ"
    assert data["stt_supported"] is True
    assert data["tts_supported"] is True


def test_expense_crud_and_dashboard_integration(auth_client, db, shop):
    # Record an expense
    res = auth_client.post(
        "/api/expenses",
        json={"amount": "250.00", "category": "supplies", "note": "Packing bags and tape"},
    )
    assert res.status_code == 201
    expense_id = res.json()["id"]
    assert Decimal(res.json()["amount"]) == Decimal("250.00")

    # List expenses
    res_list = auth_client.get("/api/expenses")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # Check dashboard reflection
    dash_res = auth_client.get("/api/dashboard")
    assert dash_res.status_code == 200
    stats = dash_res.json()
    assert Decimal(stats["total_expenses"]) >= Decimal("250.00")

    # Delete expense
    del_res = auth_client.delete(f"/api/expenses/{expense_id}")
    assert del_res.status_code == 204
