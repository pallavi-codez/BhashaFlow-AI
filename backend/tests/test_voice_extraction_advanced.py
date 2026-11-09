"""
Automated tests for advanced voice-to-form field extraction:
- Customer name extraction across Kannada, Hindi, and English
- Lowercase / real STT transcript handling
- Existing customer matching within authenticated shop
- Missing customer names & ambiguous speech clarification
- Spoken item names, quantities, and units
- Multiple items in a single spoken transaction
- Saved price list lookup for unit prices and line totals
- Separation of customer names, item names, quantities, and monetary amounts
"""
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from backend.models import TransactionType
from backend.services.parser import extract_amount, extract_customer_name, extract_items, parse_transaction
from backend import crud
from backend.schemas import CustomerCreate


class TestCustomerNameExtraction:
    def test_kannada_transliterated_lowercase(self):
        name, cands = extract_customer_name("ramesh ge 500 rupees udhar haaku")
        assert name == "Ramesh"

    def test_kannada_affixed_ge(self):
        name, cands = extract_customer_name("sureshge 300 rupees credit haaku")
        assert name == "Suresh"

    def test_kannada_script_with_postposition(self):
        name, cands = extract_customer_name("ರಮೇಶ್‌ಗೆ 500 ರೂಪಾಯಿ ಸಾಲ ಹಾಕಿ")
        assert name == "ರಮೇಶ್" or "ರಮೇಶ" in name

    def test_hindi_transliterated_lowercase(self):
        name, cands = extract_customer_name("ramesh ko 500 rupaye udhar likho")
        assert name == "Ramesh"

    def test_hindi_payment_ne(self):
        name, cands = extract_customer_name("suresh ne 200 rupaye jama kiye")
        assert name == "Suresh"

    def test_hindi_script_with_postposition(self):
        name, cands = extract_customer_name("रमेश को 500 रुपये उधार लिखो")
        assert name == "रमेश"

    def test_english_preposition_to(self):
        name, cands = extract_customer_name("credit 500 rupees to suresh")
        assert name == "Suresh"

    def test_english_preposition_from(self):
        name, cands = extract_customer_name("received 200 rupees from mahesh")
        assert name == "Mahesh"

    def test_english_action_paid(self):
        name, cands = extract_customer_name("ramesh paid 300 rupees today")
        assert name == "Ramesh"

    def test_existing_customer_matching_with_demo_suffix(self):
        existing = ["Ramesh [DEMO]", "Suresh [DEMO]"]
        name, cands = extract_customer_name("ramesh ge 500 udhar", existing_customers=existing)
        assert name == "Ramesh [DEMO]"

    def test_ambiguous_customer_matches(self):
        existing = ["Ramesh Kumar", "Ramesh Gowda"]
        name, cands = extract_customer_name("ramesh ge 500 udhar", existing_customers=existing)
        # Should detect multiple candidates and require clarification
        assert name is None
        assert len(cands) == 2
        assert "Ramesh Kumar" in cands and "Ramesh Gowda" in cands

    def test_customer_name_not_confused_with_items(self):
        # "rice" should never be extracted as customer name
        name, _ = extract_customer_name("2 kg rice 80 rupees cash sale")
        assert name is None


class TestItemAndQuantityExtraction:
    def test_single_item_quantity_and_unit(self):
        items = extract_items("2 kg sugar for 80 rupees")
        assert len(items) == 1
        assert items[0].name == "Sugar"
        assert items[0].quantity == Decimal("2")
        assert items[0].unit == "kg"
        assert items[0].total_price == Decimal("80.00")

    def test_multiple_items_in_single_spoken_transaction(self):
        transcript = "Ramesh ge 2 kg sugar 50 rupees, 1 packet milk 30 rupees udhar haaku"
        items = extract_items(transcript)
        assert len(items) == 2
        
        sugar_item = next(it for it in items if it.name == "Sugar")
        milk_item = next(it for it in items if it.name == "Milk")

        assert sugar_item.quantity == Decimal("2")
        assert sugar_item.unit == "kg"
        assert sugar_item.total_price == Decimal("50.00")

        assert milk_item.quantity == Decimal("1")
        assert milk_item.unit == "packet"
        assert milk_item.total_price == Decimal("30.00")

    def test_kannada_item_words_and_units(self):
        transcript = "ರಮೇಶ್‌ಗೆ 2 ಕೆಜಿ ಅಕ್ಕಿ 80 ರೂಪಾಯಿ ಮತ್ತು 1 ಲೀಟರ್ ಎಣ್ಣೆ 150 ರೂಪಾಯಿ ಸಾಲ"
        items = extract_items(transcript)
        assert len(items) == 2
        rice = next(it for it in items if it.name == "Rice")
        oil = next(it for it in items if it.name == "Oil")
        assert rice.quantity == Decimal("2")
        assert rice.unit == "kg"
        assert oil.quantity == Decimal("1")
        assert oil.unit == "litre"

    def test_saved_price_list_lookup(self):
        saved = {
            "sugar": Decimal("45.00"),
            "milk": Decimal("30.00"),
        }
        transcript = "2 kg sugar and 2 packet milk on credit"
        items = extract_items(transcript, saved_prices=saved)
        assert len(items) == 2
        sugar = next(it for it in items if it.name == "Sugar")
        milk = next(it for it in items if it.name == "Milk")

        assert sugar.unit_price == Decimal("45.00")
        assert sugar.total_price == Decimal("90.00")  # 2 * 45

        assert milk.unit_price == Decimal("30.00")
        assert milk.total_price == Decimal("60.00")  # 2 * 30

    def test_unit_price_at_rate_parsing(self):
        transcript = "5 kg rice at 40 rupees per kg credit to suresh"
        items = extract_items(transcript)
        assert len(items) == 1
        assert items[0].name == "Rice"
        assert items[0].quantity == Decimal("5")
        assert items[0].unit == "kg"
        assert items[0].unit_price == Decimal("40")
        assert items[0].total_price == Decimal("200.00")


class TestFullParseTransactionFlow:
    def test_full_multi_item_voice_transaction(self):
        transcript = "Ramesh ge 2 kg sugar 50 rupees, 1 packet milk 30 rupees udhar haaku"
        parsed = parse_transaction(transcript, "kn-IN")

        assert parsed.txn_type == TransactionType.CREDIT_SALE
        assert parsed.customer_name == "Ramesh"
        assert parsed.amount == Decimal("80.00")
        assert len(parsed.items) == 2
        assert not parsed.ambiguous

    def test_clarification_on_missing_customer_for_credit(self):
        transcript = "2 kg sugar 50 rupees udhar haaku"
        parsed = parse_transaction(transcript, "kn-IN")

        assert parsed.txn_type == TransactionType.CREDIT_SALE
        assert parsed.customer_name is None
        assert parsed.ambiguous
        assert "customer name" in parsed.ambiguity_reason.lower()

    def test_clarification_on_ambiguous_customer_names(self):
        existing = ["Ramesh Gowda", "Ramesh Kumar"]
        transcript = "ramesh ge 500 rupees udhar haaku"
        parsed = parse_transaction(transcript, "kn-IN", existing_customers=existing)

        assert parsed.ambiguous
        assert "Multiple matching customers" in parsed.ambiguity_reason
        assert len(parsed.candidate_customers) == 2

    def test_cash_sale_does_not_require_customer(self):
        transcript = "3 soap 90 rupees cash sale"
        parsed = parse_transaction(transcript, "en-IN")

        assert parsed.txn_type == TransactionType.CASH_SALE
        assert parsed.amount == Decimal("90.00")
        assert not parsed.ambiguous


class TestApiParseEndpoint:
    def test_api_parse_with_authenticated_shop_customers(self, auth_client: TestClient, db, shop):
        # Create customers for this shop
        c1 = crud.create_customer(db, shop.id, CustomerCreate(name="Ramesh [DEMO]"))
        c2 = crud.create_customer(db, shop.id, CustomerCreate(name="Suresh"))

        res = auth_client.post(
            "/api/stt/parse",
            data={
                "transcript": "ramesh ge 500 rupees udhar haaku",
                "language_code": "kn-IN",
            },
        )
        assert res.status_code == 200
        data = res.json()

        assert data["txn_type"] == "CREDIT_SALE"
        assert data["customer_name"] == "Ramesh [DEMO]"
        assert data["matched_customer_id"] == c1.id
        assert Decimal(str(data["amount"])) == Decimal("500")
        assert not data["ambiguous"]
