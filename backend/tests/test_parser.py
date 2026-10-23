"""
Tests for the deterministic transaction parser.
"""
from decimal import Decimal
import pytest
from backend.services.parser import parse_transaction, extract_amount, detect_transaction_type
from backend.models import TransactionType


class TestAmountExtraction:
    def test_digit_amount(self):
        assert extract_amount("500 rupees") == Decimal("500")

    def test_rupee_symbol(self):
        assert extract_amount("₹350 credit") == Decimal("350")

    def test_comma_amount(self):
        assert extract_amount("1,000 rupees") == Decimal("1000")

    def test_five_hundred_words(self):
        amt = extract_amount("five hundred rupees")
        assert amt == Decimal("500")

    def test_two_hundred_fifty_words(self):
        amt = extract_amount("two hundred fifty rupees")
        assert amt == Decimal("250")

    def test_kannada_ainooru(self):
        # "ainooru" = 500 in Kannada transliteration
        amt = extract_amount("ainooru rupees")
        assert amt == Decimal("500")

    def test_no_amount_returns_none(self):
        assert extract_amount("Ramesh took groceries today") is None


class TestTypeDetection:
    def test_credit_keyword(self):
        txn_type, conf = detect_transaction_type("Ramesh ge 500 rupees udhar haaku")
        assert txn_type == TransactionType.CREDIT_SALE
        assert conf >= 0.7

    def test_payment_keyword(self):
        txn_type, conf = detect_transaction_type("Ramesh paid 200 rupees today")
        assert txn_type == TransactionType.PAYMENT

    def test_cash_sale_keyword(self):
        txn_type, conf = detect_transaction_type("Sold groceries for 300 in cash")
        assert txn_type == TransactionType.CASH_SALE

    def test_expense_keyword(self):
        txn_type, conf = detect_transaction_type("Bought shop supplies for 100 rupees")
        assert txn_type == TransactionType.EXPENSE

    def test_no_keyword_returns_none(self):
        txn_type, conf = detect_transaction_type("hello world")
        assert txn_type is None
        assert conf == 0.0


class TestParseTransaction:
    def test_full_credit_sentence(self):
        result = parse_transaction("Ramesh ge 500 rupees udhar haaku", "kn-IN")
        assert result.txn_type == TransactionType.CREDIT_SALE
        assert result.amount == Decimal("500")
        assert result.customer_name == "Ramesh"
        assert not result.ambiguous

    def test_payment_sentence(self):
        result = parse_transaction("Ramesh paid 200 rupees today", "en-IN")
        assert result.txn_type == TransactionType.PAYMENT
        assert result.amount == Decimal("200")
        assert result.customer_name == "Ramesh"
        assert not result.ambiguous

    def test_cash_sale_no_customer(self):
        result = parse_transaction("Sold groceries for 300 rupees in cash", "en-IN")
        assert result.txn_type == TransactionType.CASH_SALE
        assert result.amount == Decimal("300")
        # Cash sale doesn't need a customer — should NOT be marked ambiguous just for missing name
        assert result.txn_type == TransactionType.CASH_SALE

    def test_missing_amount_ambiguous(self):
        result = parse_transaction("Ramesh ge udhar haaku", "kn-IN")
        assert result.ambiguous
        assert "amount" in result.ambiguity_reason.lower()

    def test_missing_name_in_credit_ambiguous(self):
        result = parse_transaction("500 rupees credit given", "en-IN")
        assert result.ambiguous
        assert result.customer_name is None

    def test_empty_transcript_ambiguous(self):
        result = parse_transaction("", "en-IN")
        assert result.ambiguous

    def test_no_type_ambiguous(self):
        result = parse_transaction("Ramesh 500 rupees", "en-IN")
        # No type keyword
        assert result.ambiguous

    def test_expense_sentence(self):
        result = parse_transaction("Bought shop supplies for 100 rupees expense", "en-IN")
        assert result.txn_type == TransactionType.EXPENSE
        assert result.amount == Decimal("100")


class TestMultilingualParsing:
    def test_hindi_credit(self):
        result = parse_transaction("Ramesh ko 500 rupaye udhar likho", "hi-IN")
        assert result.txn_type == TransactionType.CREDIT_SALE
        assert result.amount == Decimal("500")
        assert result.customer_name == "Ramesh"
        assert not result.ambiguous

    def test_hindi_devanagari_numerals_and_script(self):
        result = parse_transaction("रमेश को ५०० रुपये उधार लिखो", "hi-IN")
        assert result.txn_type == TransactionType.CREDIT_SALE
        assert result.amount == Decimal("500")
        assert result.customer_name == "रमेश"
        assert not result.ambiguous

    def test_hindi_payment(self):
        result = parse_transaction("Ramesh ne 300 rupaye jama kiye", "hi-IN")
        assert result.txn_type == TransactionType.PAYMENT
        assert result.amount == Decimal("300")
        assert result.customer_name == "Ramesh"
        assert not result.ambiguous

    def test_kannada_indic_numerals(self):
        result = parse_transaction("Ramesh ge ೫೦೦ rupees udhar haaku", "kn-IN")
        assert result.txn_type == TransactionType.CREDIT_SALE
        assert result.amount == Decimal("500")
        assert result.customer_name == "Ramesh"
        assert not result.ambiguous

    def test_tamil_credit(self):
        result = parse_transaction("Ramesh ku 450 roobai kadan podu", "ta-IN")
        assert result.txn_type == TransactionType.CREDIT_SALE
        assert result.amount == Decimal("450")
        assert result.customer_name == "Ramesh"
        assert not result.ambiguous

    def test_telugu_credit(self):
        result = parse_transaction("Ramesh ki 600 rupayalu appu raayi", "te-IN")
        assert result.txn_type == TransactionType.CREDIT_SALE
        assert result.amount == Decimal("600")
        assert result.customer_name == "Ramesh"
        assert not result.ambiguous

    def test_urdu_credit(self):
        result = parse_transaction("رمیش کو 500 روپے ادھار لکھو", "ur-IN")
        assert result.txn_type == TransactionType.CREDIT_SALE
        assert result.amount == Decimal("500")
        assert result.customer_name == "رمیش"
        assert not result.ambiguous

    def test_marathi_payment(self):
        result = parse_transaction("Ramesh la 250 rupaye jama", "mr-IN")
        assert result.txn_type == TransactionType.PAYMENT
        assert result.amount == Decimal("250")
        assert result.customer_name == "Ramesh"
        assert not result.ambiguous
