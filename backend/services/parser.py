"""
Deterministic transaction parser.

Rules applied in order:
1. Regex for amount (supports Indian number words + digits + ₹ prefix)
2. Keyword matching for transaction type (Kannada + English keywords)
3. Name extraction heuristic (capitalized token or known list)
4. Confidence + ambiguity flags

Never guesses silently: sets ambiguous=True when a field cannot be reliably extracted.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from ..models import TransactionType
from ..schemas import ParsedTransaction

# ── Amount extraction ──────────────────────────────────────────────────────────

# Indian number words → digits
_WORD_NUMBERS: dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000, "lakh": 100000, "lac": 100000,
    # Kannada transliterations
    "ondu": 1, "eradu": 2, "mooru": 3, "naalu": 4, "aidu": 5,
    "aaru": 6, "yelu": 7, "entu": 8, "ombattu": 9,
    "hatthu": 10, "nooru": 100, "saavira": 1000,
    "inooru": 200, "munooru": 300, "nanooru": 400, "ainooru": 500,
    "arunooru": 600, "erunooru": 700, "ennooru": 800, "thombattu": 900,
    "idu": 500,  # informal "idu" sometimes means 500
}

_AMOUNT_DIGIT_RE = re.compile(
    r"(?:₹\s*)?(\d[\d,]*(?:\.\d{1,2})?)\s*(?:rupees?|rs\.?|/-)?",
    re.IGNORECASE,
)

def _words_to_number(text: str) -> Optional[Decimal]:
    """Convert an English/Kannada number-word sequence to a Decimal."""
    words = text.lower().split()
    total = Decimal(0)
    current = Decimal(0)
    found_any = False
    for word in words:
        if word in _WORD_NUMBERS:
            found_any = True
            val = Decimal(_WORD_NUMBERS[word])
            if val >= 100:
                if current == 0:
                    current = Decimal(1)
                current *= val
                if val >= 1000:
                    total += current
                    current = Decimal(0)
            else:
                current += val
    if found_any:
        return total + current
    return None


def extract_amount(text: str) -> Optional[Decimal]:
    """Extract the first monetary amount from text."""
    # Try digit pattern first
    m = _AMOUNT_DIGIT_RE.search(text)
    if m:
        raw = m.group(1).replace(",", "")
        try:
            return Decimal(raw)
        except InvalidOperation:
            pass
    # Try word-based
    return _words_to_number(text)


# ── Transaction type detection ─────────────────────────────────────────────────

_CREDIT_KEYWORDS = [
    # English
    "credit", "udhar", "udhaar", "gave", "give", "taken", "took", "lent",
    "haaku", "haak", "credit sale", "on credit",
    # Kannada transliterations
    "saal kudidaare", "haakidaare", "thogondaare", "kudidru",
]
_PAYMENT_KEYWORDS = [
    # English
    "paid", "payment", "received", "collected", "returned", "pay", "repaid",
    "kattu", "kattidru", "kotta", "kodutta", "kattidaare",
    # Kannada
    "hana kotta", "hana kodutta",
]
_CASH_KEYWORDS = [
    "cash", "cash sale", "sold", "sale", "nakad",
    "nakad sale", "cash paid",
]
_EXPENSE_KEYWORDS = [
    "expense", "expenses", "bought", "purchase", "shop supplies",
    "spent", "kharchu", "kharcha",
]


def _best_match(text_lower: str, keywords: list[str]) -> bool:
    return any(kw in text_lower for kw in keywords)


def detect_transaction_type(text: str) -> tuple[Optional[TransactionType], float]:
    """Returns (type, confidence). confidence < 0.7 ⟹ ambiguous."""
    t = text.lower()

    scores: dict[TransactionType, int] = {
        TransactionType.CREDIT_SALE: 0,
        TransactionType.PAYMENT:     0,
        TransactionType.CASH_SALE:   0,
        TransactionType.EXPENSE:     0,
    }

    for kw in _CREDIT_KEYWORDS:
        if kw in t:
            scores[TransactionType.CREDIT_SALE] += 2 if len(kw) > 5 else 1
    for kw in _PAYMENT_KEYWORDS:
        if kw in t:
            scores[TransactionType.PAYMENT] += 2 if len(kw) > 5 else 1
    for kw in _CASH_KEYWORDS:
        if kw in t:
            scores[TransactionType.CASH_SALE] += 2 if len(kw) > 5 else 1
    for kw in _EXPENSE_KEYWORDS:
        if kw in t:
            scores[TransactionType.EXPENSE] += 2 if len(kw) > 5 else 1

    best_type = max(scores, key=lambda k: scores[k])
    best_score  = scores[best_type]

    if best_score == 0:
        return None, 0.0

    # Confidence: 1.0 if strong match, 0.9 if unique clear keyword, lower if tied or low score
    sorted_scores = sorted(scores.values(), reverse=True)
    if sorted_scores[0] > sorted_scores[1]:
        conf = 1.0 if best_score >= 2 else 0.9
    else:
        conf = 0.5
    return best_type, conf


# ── Name extraction ────────────────────────────────────────────────────────────

# Prepositions / conjunctions to skip
_SKIP_WORDS = {
    "the", "a", "an", "and", "or", "at", "in", "on", "for", "to", "from",
    "by", "with", "is", "was", "has", "have", "had", "will", "would", "can",
    "could", "should", "today", "yesterday", "rupees", "rs", "inr",
    "credit", "payment", "cash", "sale", "expense", "udhar", "paid",
    "bought", "sold", "taken", "gave",
    # Kannada common words transliterated
    "ge", "gu", "na", "ni", "de", "da", "ke", "ka", "ku", "ra", "ru",
    "haaku", "thogondaare", "kotta", "kodutta",
}

_NAME_PATTERN = re.compile(r"\b([A-Z][a-z]{1,20})\b")


def extract_customer_name(text: str) -> Optional[str]:
    """Find the first capitalised proper noun that isn't a stop-word."""
    for m in _NAME_PATTERN.finditer(text):
        word = m.group(1)
        if word.lower() not in _SKIP_WORDS:
            return word
    return None


# ── Main parse function ────────────────────────────────────────────────────────

def parse_transaction(transcript: str, language: str = "en-IN") -> ParsedTransaction:
    """
    Parse a voice transcript into a structured transaction.

    Always sets ambiguous=True + ambiguity_reason when a required field is missing.
    Never silently guesses.
    """
    if not transcript or not transcript.strip():
        return ParsedTransaction(
            ambiguous=True,
            ambiguity_reason="Transcript is empty.",
            confidence=0.0,
        )

    txn_type, type_conf = detect_transaction_type(transcript)
    amount              = extract_amount(transcript)
    customer_name       = extract_customer_name(transcript)

    ambiguous = False
    reasons   = []

    if txn_type is None:
        ambiguous = True
        reasons.append("Could not determine transaction type (credit/payment/cash/expense).")
    elif type_conf < 0.7:
        ambiguous = True
        reasons.append(f"Transaction type is unclear (confidence {type_conf:.0%}).")

    if amount is None:
        ambiguous = True
        reasons.append("Could not extract a valid rupee amount.")
    elif amount <= 0:
        ambiguous = True
        reasons.append("Amount must be greater than zero.")

    # Credit sales and payments need a customer name
    if txn_type in (TransactionType.CREDIT_SALE, TransactionType.PAYMENT) and not customer_name:
        ambiguous = True
        reasons.append("Customer name not found. Please provide the customer's name.")

    confidence = type_conf * (1.0 if amount is not None else 0.3)

    return ParsedTransaction(
        txn_type=txn_type,
        customer_name=customer_name,
        amount=amount,
        note=None,
        confidence=confidence,
        ambiguous=ambiguous,
        ambiguity_reason="; ".join(reasons) if reasons else None,
    )
