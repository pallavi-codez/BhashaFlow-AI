"""
Parser regression tests for multilingual (Kannada, Hindi, English) customer-name extraction.

Covers:
1. Kannada speech with an English customer name ("Ramesh ge ₹500 udhar haaku").
2. Kannada speech with a Kannada-script customer name ("ಸುರೇಶ ₹೧೦೦ ಕೊಟ್ಟ").
3. Hindi speech with an English customer name ("Ramesh ko ₹500 udhar diya").
4. Hindi speech with a Hindi-script customer name ("सुरेश ने ₹100 दिया").
5. English speech with an English customer name ("Credit ₹500 to Ramesh").
6. Existing customer matching using authenticated shop records (exact match, base name, demo strip).
7. Unknown customer names (returns parsed token, not empty/None).
8. Ambiguous customer names (returns ambiguous=True, candidates list).
9. Shop customer isolation (never matches another shop's customer not in existing_customers).
10. Kannada and Arabic numeral normalization.
"""

from decimal import Decimal

import pytest

from backend.services.parser import (
    TransactionType,
    _indic_name_matches_latin,
    extract_customer_name,
    parse_transaction,
)


# ---------------------------------------------------------------------------
# Unit tests for _indic_name_matches_latin()
# ---------------------------------------------------------------------------

class TestIndicToLatinMatching:
    def test_suresh_kannada_matches_latin(self):
        assert _indic_name_matches_latin("ಸುರೇಶ", "Suresh") is True

    def test_ramesh_kannada_matches_latin(self):
        assert _indic_name_matches_latin("ರಮೇಶ", "Ramesh") is True

    def test_suresh_hindi_matches_latin(self):
        assert _indic_name_matches_latin("सुरेश", "Suresh") is True

    def test_ramesh_hindi_matches_latin(self):
        assert _indic_name_matches_latin("रमेश", "Ramesh") is True

    def test_no_cross_match_wrong_name(self):
        assert _indic_name_matches_latin("ರಮೇಶ", "Suresh") is False

    def test_suresh_does_not_match_ramesh(self):
        assert _indic_name_matches_latin("ಸುರೇಶ", "Ramesh") is False


# ---------------------------------------------------------------------------
# Unit tests for extract_customer_name()
# ---------------------------------------------------------------------------

class TestExtractCustomerName:
    def test_kannada_suresh_matches_latin_customer(self):
        """ಸುರೇಶ ₹100 ಕೊಟ್ಟ matches Latin-stored 'Suresh'."""
        name, candidates = extract_customer_name(
            "ಸುರೇಶ ₹100 ಕೊಟ್ಟ", existing_customers=["Suresh"]
        )
        assert name == "Suresh"
        assert candidates == ["Suresh"]

    def test_kannada_ramesh_matches_latin_customer(self):
        name, candidates = extract_customer_name(
            "ರಮೇಶ ₹300 ಕೊಟ್ಟ", existing_customers=["Ramesh"]
        )
        assert name == "Ramesh"

    def test_hindi_suresh_matches_latin_customer(self):
        """सुरेश ने ₹100 दिया matches Latin-stored 'Suresh'."""
        name, candidates = extract_customer_name(
            "सुरेश ने ₹100 दिया", existing_customers=["Suresh"]
        )
        assert name == "Suresh"

    def test_kannada_speech_with_english_name(self):
        """Ramesh ge ₹500 udhar haaku matches Latin-stored 'Ramesh'."""
        name, candidates = extract_customer_name(
            "Ramesh ge ₹500 udhar haaku", existing_customers=["Ramesh"]
        )
        assert name == "Ramesh"

    def test_hindi_speech_with_english_name(self):
        """Ramesh ko ₹500 udhar diya matches Latin-stored 'Ramesh'."""
        name, candidates = extract_customer_name(
            "Ramesh ko ₹500 udhar diya", existing_customers=["Ramesh"]
        )
        assert name == "Ramesh"

    def test_english_speech_with_english_name(self):
        """Credit ₹500 to Ramesh matches Latin-stored 'Ramesh'."""
        name, candidates = extract_customer_name(
            "Credit ₹500 to Ramesh", existing_customers=["Ramesh"]
        )
        assert name == "Ramesh"

    def test_unknown_kannada_customer_returns_indic_name(self):
        """When not in shop DB, return the Kannada name rather than None."""
        name, candidates = extract_customer_name(
            "ಸುರೇಶ ₹100 ಕೊಟ್ಟ", existing_customers=[]
        )
        assert name is not None, "Expected Indic name to be returned, got None"
        assert "ಸುರೇಶ" in (name or "")

    def test_unknown_hindi_customer_returns_indic_name(self):
        """When not in shop DB, return the Hindi name rather than None."""
        name, candidates = extract_customer_name(
            "सुरेश ने ₹100 दिया", existing_customers=[]
        )
        assert name is not None
        assert "सुरेश" in (name or "")

    def test_ambiguous_kannada_customers_returns_candidates(self):
        """Multiple customers matching returns ambiguous list."""
        name, candidates = extract_customer_name(
            "ರಮೇಶ ₹200 ಉಧಾರ",
            existing_customers=["Ramesh Kumar", "Ramesh Patel"],
        )
        assert len(candidates) >= 1

    def test_shop_customer_isolation_never_matches_absent_customer(self):
        """If Shop A has Suresh, but Shop B only has Ramesh, Suresh must NOT match Ramesh."""
        name, candidates = extract_customer_name(
            "ಸುರೇಶ ₹100 ಕೊಟ್ಟ", existing_customers=["Ramesh"]
        )
        # Should not resolve to Ramesh
        assert name != "Ramesh"

    def test_no_customer_name_in_transcript(self):
        """Pure amount+type transcript without a name returns None."""
        name, candidates = extract_customer_name(
            "₹100 cash sale", existing_customers=["Ramesh"]
        )
        assert name is None


# ---------------------------------------------------------------------------
# Integration tests for parse_transaction()
# ---------------------------------------------------------------------------

class TestParseTransactionMultilingual:
    def test_kannada_payment_suresh(self):
        """ಸುರೇಶ ₹೧೦೦ ಕೊಟ್ಟ — Kannada name + Kannada numerals + payment keyword."""
        result = parse_transaction(
            "ಸುರೇಶ ₹೧೦೦ ಕೊಟ್ಟ",
            language="kn-IN",
            existing_customers=["Suresh"],
            saved_prices={},
        )
        assert result.amount == Decimal("100.00"), f"Expected ₹100, got {result.amount}"
        assert result.customer_name == "Suresh", f"Expected 'Suresh', got {result.customer_name!r}"
        assert result.txn_type == TransactionType.PAYMENT, f"Expected PAYMENT, got {result.txn_type}"

    def test_kannada_numerals_normalized(self):
        """Kannada numeral ₹೫೦೦ should normalize to 500."""
        result = parse_transaction(
            "Ramesh ge ₹೫೦೦ udhar haaku",
            language="kn-IN",
            existing_customers=["Ramesh"],
            saved_prices={},
        )
        assert result.amount == Decimal("500.00"), f"Expected ₹500, got {result.amount}"

    def test_cross_script_ramesh_kannada(self):
        """ರಮೇಶ ₹300 ಕೊಟ್ಟ extracts Ramesh from shop customer list."""
        result = parse_transaction(
            "ರಮೇಶ ₹300 ಕೊಟ್ಟ",
            language="kn-IN",
            existing_customers=["Ramesh"],
            saved_prices={},
        )
        assert result.customer_name == "Ramesh", f"Expected 'Ramesh', got {result.customer_name!r}"
        assert result.amount == Decimal("300.00")

    def test_hindi_speech_with_hindi_name_suresh(self):
        """सुरेश ने ₹100 दिया matches Latin customer Suresh."""
        result = parse_transaction(
            "सुरेश ने ₹100 दिया",
            language="hi-IN",
            existing_customers=["Suresh"],
            saved_prices={},
        )
        assert result.customer_name == "Suresh"
        assert result.amount == Decimal("100.00")
        assert result.txn_type == TransactionType.PAYMENT

    def test_kannada_speech_with_english_name(self):
        """Ramesh ge ₹500 udhar haaku in kn-IN."""
        result = parse_transaction(
            "Ramesh ge ₹500 udhar haaku",
            language="kn-IN",
            existing_customers=["Ramesh"],
            saved_prices={},
        )
        assert result.customer_name == "Ramesh"
        assert result.amount == Decimal("500.00")
        assert result.txn_type == TransactionType.CREDIT_SALE

    def test_hindi_speech_with_english_name(self):
        """Ramesh ko ₹500 udhar diya in hi-IN."""
        result = parse_transaction(
            "Ramesh ko ₹500 udhar diya",
            language="hi-IN",
            existing_customers=["Ramesh"],
            saved_prices={},
        )
        assert result.customer_name == "Ramesh"
        assert result.amount == Decimal("500.00")
        assert result.txn_type == TransactionType.CREDIT_SALE

    def test_english_speech_with_english_name(self):
        """Credit ₹500 to Ramesh in en-IN."""
        result = parse_transaction(
            "Credit ₹500 to Ramesh",
            language="en-IN",
            existing_customers=["Ramesh"],
            saved_prices={},
        )
        assert result.customer_name == "Ramesh"
        assert result.amount == Decimal("500.00")
        assert result.txn_type == TransactionType.CREDIT_SALE

    def test_unknown_customer_returns_indic_name_not_empty(self):
        """When customer not in DB, return Indic name token for UI display."""
        result = parse_transaction(
            "ಸುರೇಶ ₹100 ಕೊಟ್ಟ",
            language="kn-IN",
            existing_customers=[],
            saved_prices={},
        )
        assert result.customer_name is not None, "Expected Indic name returned to UI"
        assert "ಸುರೇಶ" in result.customer_name

    def test_kannada_credit_keyword(self):
        """ಉಧಾರ should map to CREDIT_SALE."""
        result = parse_transaction(
            "ರಮೇಶ ₹200 ಉಧಾರ",
            language="kn-IN",
            existing_customers=["Ramesh"],
            saved_prices={},
        )
        assert result.amount == Decimal("200.00")
        assert result.txn_type == TransactionType.CREDIT_SALE

    def test_ambiguous_customers_flagged(self):
        """Two customers with same first name: Ramesh Kumar, Ramesh Patel."""
        result = parse_transaction(
            "Ramesh ₹200 udhar",
            language="en-IN",
            existing_customers=["Ramesh Kumar", "Ramesh Patel"],
            saved_prices={},
        )
        assert result.ambiguous is True or len(result.candidate_customers) >= 2

    def test_cash_sale_no_customer(self):
        """Pure cash sale without customer name."""
        result = parse_transaction(
            "₹500 cash sale",
            language="en-IN",
            existing_customers=["Ramesh"],
            saved_prices={},
        )
        assert result.amount == Decimal("500.00")
        assert result.txn_type == TransactionType.CASH_SALE
        assert result.customer_name is None
