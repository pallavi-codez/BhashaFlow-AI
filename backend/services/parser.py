"""
Deterministic multilingual transaction parser for BhashaFlow AI.

Supports Indian languages including:
- Kannada (kn-IN)
- Hindi (hi-IN)
- English (en-IN)
- Tamil (ta-IN)
- Telugu (te-IN)
- Malayalam (ml-IN)
- Marathi (mr-IN)
- Bengali (bn-IN)
- Gujarati (gu-IN)
- Punjabi (pa-IN)
- Odia (or-IN)
- Assamese (as-IN)
- Urdu (ur-IN)

Rules applied in order:
1. Indic numeral normalization (Devanagari, Kannada, Tamil, Telugu, Bengali, Gujarati, Punjabi, Odia, Urdu digits)
2. Amount extraction (digits, currency symbols, and Indic number words)
3. Multilingual keyword matching for transaction type (credit/payment/cash/expense)
4. Multilingual customer name extraction (proper nouns & postposition markers)
5. Strict ambiguity check: never silently guesses invalid or missing fields.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from ..models import TransactionType
from ..schemas import ParsedTransaction

# ── Indic Numerals Normalization ───────────────────────────────────────────────

_INDIC_DIGIT_MAP = str.maketrans({
    # Devanagari (Hindi, Marathi)
    "०": "0", "१": "1", "२": "2", "३": "3", "४": "4",
    "५": "5", "६": "6", "७": "7", "८": "8", "९": "9",
    # Kannada
    "೦": "0", "೧": "1", "೨": "2", "೩": "3", "೪": "4",
    "೫": "5", "೬": "6", "೭": "7", "೮": "8", "೯": "9",
    # Tamil
    "௦": "0", "௧": "1", "௨": "2", "௩": "3", "௪": "4",
    "௫": "5", "௬": "6", "௭": "7", "௮": "8", "௯": "9",
    # Telugu
    "౦": "0", "౧": "1", "౨": "2", "౩": "3", "౪": "4",
    "౫": "5", "౬": "6", "౭": "7", "౮": "8", "౯": "9",
    # Bengali / Assamese
    "০": "0", "১": "1", "২": "2", "৩": "3", "৪": "4",
    "৫": "5", "৬": "6", "৭": "7", "৮": "8", "৯": "9",
    # Gujarati
    "૦": "0", "૧": "1", "૨": "2", "૩": "3", "૪": "4",
    "૫": "5", "૬": "6", "૭": "7", "૮": "8", "૯": "9",
    # Gurmukhi (Punjabi)
    "੦": "0", "੧": "1", "੨": "2", "੩": "3", "੪": "4",
    "੫": "5", "੬": "6", "੭": "7", "੮": "8", "੯": "9",
    # Odia
    "୦": "0", "୧": "1", "୨": "2", "୩": "3", "୪": "4",
    "୫": "5", "୬": "6", "୭": "7", "୮": "8", "୯": "9",
    # Perso-Arabic (Urdu)
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
    "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
})


def normalize_indic_digits(text: str) -> str:
    """Convert any Indic script numerals in text to standard ASCII digits 0-9."""
    return text.translate(_INDIC_DIGIT_MAP)


# ── Amount extraction ──────────────────────────────────────────────────────────

# Number words → digits (English, Hindi, Kannada transliterations and native scripts)
_WORD_NUMBERS: dict[str, int] = {
    # English
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
    "idu": 500,
    # Hindi transliterations & words
    "ek": 1, "do": 2, "teen": 3, "chaar": 4, "paanch": 5, "panch": 5,
    "chhe": 6, "saat": 7, "aath": 8, "nau": 9, "das": 10,
    "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14, "pandrah": 15,
    "solah": 16, "satrah": 17, "atharah": 18, "unnis": 19, "bees": 20,
    "tees": 30, "chaalis": 40, "pachaas": 50, "saath": 60, "sattar": 70,
    "assi": 80, "nabbe": 90, "sau": 100, "hazaar": 1000, "hazar": 1000,
    # Devanagari script words
    "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5,
    "छह": 6, "सात": 7, "आठ": 8, "नौ": 9, "दस": 10,
    "सौ": 100, "हज़ार": 1000, "हजार": 1000, "पचास": 50,
    # Kannada script words
    "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ನಾಲ್ಕು": 4, "ಐದು": 5,
    "ನೂರು": 100, "ಐನೂರು": 500, "ಸಾವಿರ": 1000,
}

_AMOUNT_DIGIT_RE = re.compile(
    r"(?:[₹$Rs\.]\s*)?(\d[\d,]*(?:\.\d{1,2})?)\s*(?:rupees?|rs\.?|rupaya|rupaye|roobai|taka|tanka|roopa|/-)?",
    re.IGNORECASE,
)


def _words_to_number(text: str) -> Optional[Decimal]:
    """Convert an English/Indic number-word sequence to a Decimal."""
    words = text.lower().split()
    total = Decimal(0)
    current = Decimal(0)
    found_any = False
    for word in words:
        clean_word = word.strip(".,;:!?")
        if clean_word in _WORD_NUMBERS:
            found_any = True
            val = Decimal(_WORD_NUMBERS[clean_word])
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
    """Extract the first monetary amount from text, supporting Indic numerals and words."""
    norm_text = normalize_indic_digits(text)
    # Try digit pattern first
    m = _AMOUNT_DIGIT_RE.search(norm_text)
    if m:
        raw = m.group(1).replace(",", "")
        try:
            val = Decimal(raw)
            if val > 0:
                return val
        except InvalidOperation:
            pass
    # Try word-based
    return _words_to_number(norm_text)


# ── Multilingual transaction type detection ───────────────────────────────────

_CREDIT_KEYWORDS = [
    # English
    "credit", "udhar", "udhaar", "gave", "give", "taken", "took", "lent",
    "haaku", "haak", "credit sale", "on credit", "gave credit",
    # Kannada
    "saal kudidaare", "haakidaare", "thogondaare", "kudidru", "saala", "saal",
    "ಉದ್ಧಾರ", "ಉದ್ರಿ", "ಸಾಲ", "ಹಾಕು", "ಹಾಕಿ", "ಕೊಡು",
    # Hindi
    "udhaari", "khate me", "likho", "likh do", "baaki", "baki",
    "उधार", "उधारी", "खाते में", "लिख दो", "लिखो", "बाकी",
    # Tamil
    "kadan", "kadanaaga", "podu", "ezhuthu", "கடன்", "கடனாக", "எழுது",
    # Telugu
    "appu", "appuga", "raayi", "bhaaki", "అప్పు", "అప్పుగా", "రాయి",
    # Malayalam
    "kadam", "kadamaayi", "ezhuthu", "കടം", "കടമായി",
    # Marathi
    "udhari", "liha", "navavar", "उधारी", "लिहा", "नावावर",
    # Bengali / Assamese
    "dhare", "lekho", "বাকি", "ধারে", "ধার", "লেখ", "বাকী", "লিখা",
    # Gujarati
    "lakho", "ઉધાર", "લખો",
    # Punjabi
    "ਉਧਾਰ", "ਲਿਖੋ",
    # Odia
    "udhara", "lekha", "ଉଧାର", "ଲେଖ",
    # Urdu
    "qarz", "ادھار", "قرض", "لکھو",
]

_PAYMENT_KEYWORDS = [
    # English
    "paid", "payment", "received", "collected", "returned", "pay", "repaid", "settled",
    # Kannada
    "kattu", "kattidru", "kotta", "kodutta", "kattidaare", "hana kotta", "hana kodutta",
    "ಪಾವತಿ", "ಕೊಟ್ಟರು", "ಕೊಟ್ಟ", "ಪಾವತಿಸಿದರು",
    # Hindi
    "jama", "diya", "chukaaya", "bhugtan", "vasool", "aaye", "wapas diya",
    "जमा", "दिया", "चुकाया", "भुगतान", "वसूल", "जमा किए",
    # Tamil
    "panam koduthaar", "seluthinaar", "koduthaar", "பணம் கொடுத்தார்", "செலுத்தினார்",
    # Telugu
    "ichendu", "kattinadu", "chellinchaaru", "చెల్లించారు", "ఇచ్చారు",
    # Malayalam
    "thannu", "nalki", "koduthu", "തന്നു", "നൽകി",
    # Marathi
    "dile", "patavile", "भरले", "दिले",
    # Bengali / Assamese
    "dilo", "porishodh", "joma", "জমা", "দিল", "পরিশোধ", "দিলে",
    # Gujarati
    "apya", "આપ્યા",
    # Punjabi
    "ditte", "ਜਮ੍ਹਾ", "ਦਿੱਤੇ",
    # Odia
    "dela", "ଜମା", "ଦେଲା",
    # Urdu
    "ada kiya", "ada kiye", "diye", "ادا کیا", "جمع", "دیئے",
]

_CASH_KEYWORDS = [
    # English
    "cash", "cash sale", "sold", "sale", "nakad", "nakad sale", "cash paid",
    # Kannada
    "nagadu", "rokkha", "ನಗದು", "ರೊಕ್ಕ",
    # Hindi
    "nagad", "rokad", "roker", "नकद", "रोकड़", "नगद",
    # Tamil
    "rokkam", "ரொக்கம்", "ரொக்க விற்பனை",
    # Telugu
    "నగదు",
    # Marathi
    "rokh", "रोख", "रोकड",
    # Bengali
    "nogod", "নগদ",
    # Urdu
    "naqd", "نقد",
]

_EXPENSE_KEYWORDS = [
    # English
    "expense", "expenses", "bought", "purchase", "shop supplies", "spent",
    # Kannada
    "kharchu", "kharcha", "ಖರ್ಚು",
    # Hindi
    "kharch", "vyay", "खर्च", "खर्चा", "दुकान का खर्च",
    # Tamil
    "selavu", "செலவு",
    # Telugu
    "kharche", "ఖర్చు",
    # Marathi
    "खर्च",
    # Bengali
    "khoroch", "খরচ",
    # Urdu
    "خرچ",
]


def detect_transaction_type(text: str) -> tuple[Optional[TransactionType], float]:
    """
    Returns (type, confidence).
    Confidence: 1.0 if strong match, 0.9 if unique clear keyword, lower if tied/unclear.
    """
    t = text.lower()

    scores: dict[TransactionType, int] = {
        TransactionType.CREDIT_SALE: 0,
        TransactionType.PAYMENT:     0,
        TransactionType.CASH_SALE:   0,
        TransactionType.EXPENSE:     0,
    }

    for kw in _CREDIT_KEYWORDS:
        if kw in t:
            scores[TransactionType.CREDIT_SALE] += 2 if len(kw) > 4 else 1
    for kw in _PAYMENT_KEYWORDS:
        if kw in t:
            scores[TransactionType.PAYMENT] += 2 if len(kw) > 4 else 1
    for kw in _CASH_KEYWORDS:
        if kw in t:
            scores[TransactionType.CASH_SALE] += 2 if len(kw) > 4 else 1
    for kw in _EXPENSE_KEYWORDS:
        if kw in t:
            scores[TransactionType.EXPENSE] += 2 if len(kw) > 4 else 1

    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]

    if best_score == 0:
        return None, 0.0

    sorted_scores = sorted(scores.values(), reverse=True)
    if sorted_scores[0] > sorted_scores[1]:
        conf = 1.0 if best_score >= 2 else 0.9
    else:
        conf = 0.5
    return best_type, conf


# ── Multilingual Name extraction ───────────────────────────────────────────────

_SKIP_WORDS = {
    "the", "a", "an", "and", "or", "at", "in", "on", "for", "to", "from",
    "by", "with", "is", "was", "has", "have", "had", "will", "would", "can",
    "could", "should", "today", "yesterday", "rupees", "rs", "inr",
    "credit", "payment", "cash", "sale", "expense", "udhar", "paid",
    "bought", "sold", "taken", "gave",
    # Indian postpositions transliterated
    "ge", "gu", "na", "ni", "de", "da", "ke", "ka", "ku", "ki", "ko", "ne",
    "ra", "ru", "la", "nu", "haaku", "thogondaare", "kotta", "kodutta", "likho",
}

_ROMAN_NAME_PATTERN = re.compile(r"\b([A-Z][a-z]{1,20})\b")

# Regex for Indic script customer names preceding common postpositions
# E.g. "रमेश को", "सुरेश ने", "రమేష్ కి", "ரமேஷ் கு", "رمیش کو"
_INDIC_POSTPOSITION_RE = re.compile(
    r"([\u0900-\u0D7F\u0600-\u06FF]{2,20})\s+(?:ge|gu|ko|ne|ka|ki|ku|ke|la|nu|को|ने|का|की|ಗೆ|கு|కి|کے|کو)(?:\s+|$|[.,;!?])",
    re.UNICODE,
)


def extract_customer_name(text: str) -> Optional[str]:
    """
    Extract the customer name from text.
    Handles:
    1. Capitalized proper nouns in English/transliteration (e.g. 'Ramesh', 'Suresh')
    2. Names marked by Indian language postpositions in Indic scripts (e.g. 'रमेश को')
    """
    # Try Indic script with postposition first
    m_indic = _INDIC_POSTPOSITION_RE.search(text)
    if m_indic:
        name = m_indic.group(1).strip()
        if name.lower() not in _SKIP_WORDS and len(name) >= 2:
            return name

    # Try capitalized Roman tokens
    for m in _ROMAN_NAME_PATTERN.finditer(text):
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

    clean_text = transcript.strip()
    txn_type, type_conf = detect_transaction_type(clean_text)
    amount = extract_amount(clean_text)
    customer_name = extract_customer_name(clean_text)

    ambiguous = False
    reasons = []

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
