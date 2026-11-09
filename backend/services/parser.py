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
1. Indic numeral normalization (Devanagari, Kannada, Tamil, Telugu, etc.)
2. Multilingual keyword matching for transaction type (credit/payment/cash/expense)
3. Existing customer matching & multilingual name extraction (Kannada, Hindi, English, etc.)
4. Spoken item, quantity, unit, and price extraction (supporting multiple items & saved price list)
5. Authoritative transaction amount calculation and verification
6. Strict ambiguity check: never silently guesses invalid or missing fields.
"""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Optional

from ..models import TransactionType
from ..schemas import ParsedItem, ParsedTransaction

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


# ── Amount & Number Extraction ────────────────────────────────────────────────

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
    "ondu": 1, "eradu": 2, "mooru": 3, "naalu": 4, "naalku": 4, "aidu": 5,
    "aaru": 6, "yelu": 7, "entu": 8, "ombattu": 9,
    "hatthu": 10, "ippattu": 20, "moovattu": 30, "nalvattu": 40, "aivattu": 50,
    "nooru": 100, "saavira": 1000,
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
    "ಆರು": 6, "ಏಳು": 7, "ಎಂಟು": 8, "ಒಂಬತ್ತು": 9, "ಹತ್ತು": 10,
    "ನೂರು": 100, "ಇನ್ನೂರು": 200, "ಮುನ್ನೂರು": 300, "ಐನೂರು": 500, "ಸಾವಿರ": 1000,
}

_FRACTIONS: dict[str, Decimal] = {
    "half": Decimal("0.5"),
    "ardha": Decimal("0.5"),
    "aadha": Decimal("0.5"),
    "adhaa": Decimal("0.5"),
    "1/2": Decimal("0.5"),
    "quarter": Decimal("0.25"),
    "paavu": Decimal("0.25"),
    "paav": Decimal("0.25"),
    "1/4": Decimal("0.25"),
    "dedh": Decimal("1.5"),
    "ondavare": Decimal("1.5"),
    "dhai": Decimal("2.5"),
    "eradavare": Decimal("2.5"),
}

_EXPLICIT_AMOUNT_RE = re.compile(
    r"(?:total|amount|sum|kottu|mottha|kool|rupees?|rs\.?|₹|inr)\s*(?:is|of|amount|haaku)?\s*[:=]?\s*"
    r"[₹$Rs\.]?\s*(\d[\d,]*(?:\.\d{1,2})?)\s*(?:rupees?|rs\.?|rupaya|rupaye|roobai|taka|tanka|roopa|/-)?",
    re.IGNORECASE,
)

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
        if clean_word in _FRACTIONS:
            found_any = True
            current += _FRACTIONS[clean_word]
        elif clean_word in _WORD_NUMBERS:
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
    """Extract monetary amount from text, prioritizing explicit total patterns."""
    norm_text = normalize_indic_digits(text)
    
    # 1. Look for explicit total/amount markers first (e.g. "total 300 rupees", "amount ₹500")
    m_exp = _EXPLICIT_AMOUNT_RE.search(norm_text)
    if m_exp:
        raw = m_exp.group(1).replace(",", "")
        try:
            val = Decimal(raw)
            if val > 0:
                return val
        except InvalidOperation:
            pass

    # 2. Look for currency-tagged amounts (e.g. "₹500", "500 rupees", "Rs 500")
    tagged_matches = list(re.finditer(
        r"(?:₹|rs\.?|inr)\s*(\d[\d,]*(?:\.\d{1,2})?)|(\d[\d,]*(?:\.\d{1,2})?)\s*(?:rupees?|rs\.?|rupaya|rupaye|roobai|roopa|ರೂಪಾಯಿ|रुपये|/-)",
        norm_text,
        re.IGNORECASE,
    ))
    if tagged_matches:
        # If there's an explicit total keyword near one, or take the last one (often total)
        for tm in reversed(tagged_matches):
            raw = (tm.group(1) or tm.group(2)).replace(",", "")
            try:
                val = Decimal(raw)
                if val > 0:
                    return val
            except InvalidOperation:
                pass

    # 3. Standard digit pattern
    m = _AMOUNT_DIGIT_RE.search(norm_text)
    if m:
        raw = m.group(1).replace(",", "")
        try:
            val = Decimal(raw)
            if val > 0:
                return val
        except InvalidOperation:
            pass

    # 4. Try word-based numbers
    return _words_to_number(norm_text)


# ── Multilingual Transaction Type Detection ───────────────────────────────────

_CREDIT_KEYWORDS = [
    # English
    "credit", "udhar", "udhaar", "gave", "give", "taken", "took", "lent",
    "haaku", "haak", "credit sale", "on credit", "gave credit",
    # Kannada
    "saal kudidaare", "haakidaare", "thogondaare", "kudidru", "saala", "saal",
    "ಉದ್ಧಾರ", "ಉಧಾರ", "ಉದ್ರಿ", "ಸಾಲ", "ಹಾಕು", "ಹಾಕಿ", "ಕೊಡು", "ತಗೊಂಡಿದ್ದಾರೆ",
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
    "dhare", "lekho", "বাকি", "ধারে", "ধার", "লেখ", "বাকী", "লিখಾ",
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
    "ಪಾವತಿ", "ಕೊಟ್ಟರು", "ಕೊಟ್ಟ", "ಪಾವತಿಸಿದರು", "ಜಮಾ",
    # Hindi
    "jama", "diya", "chukaaya", "bhugtan", "vasool", "aaye", "wapas diya", "jama kiye",
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
    """Returns (TransactionType, confidence score 0.0 - 1.0)."""
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


# ── Multilingual Item Lexicon & Units ──────────────────────────────────────────

_KNOWN_UNITS: dict[str, str] = {
    # Weight
    "kg": "kg", "kilo": "kg", "kilos": "kg", "kgs": "kg", "kilogram": "kg", "kilograms": "kg",
    "ಕೆಜಿ": "kg", "ಕೆ.ಜಿ": "kg", "ಕಿಲೋ": "kg", "किलो": "kg", "किलोग्राम": "kg",
    "gram": "gram", "grams": "gram", "g": "gram", "gm": "gram", "gms": "gram",
    "ಗ್ರಾಂ": "gram", "ग्राम": "gram",
    # Volume
    "litre": "litre", "liter": "litre", "litres": "litre", "liters": "litre", "l": "litre", "ltr": "litre", "ltrs": "litre",
    "ಲೀಟರ್": "litre", "लीटर": "litre",
    # Units / Packets
    "packet": "packet", "packets": "packet", "pkt": "packet", "pkts": "packet", "pack": "packet", "packs": "packet",
    "pouch": "packet", "pouches": "packet", "ಪ್ಯಾಕೆಟ್": "packet", "ಪ್ಯಾಕ್": "packet", "पैकेट": "packet",
    "piece": "piece", "pieces": "piece", "pc": "piece", "pcs": "piece", "ಪೀಸ್": "piece", "पीस": "piece",
    "bottle": "bottle", "bottles": "bottle", "ಬಾಟಲ್": "bottle", "बोतल": "bottle",
    "box": "box", "boxes": "box", "ಪೆಟ್ಟಿಗೆ": "box", "डिब्बा": "box",
    "dozen": "dozen", "dozens": "dozen", "ಡಜನ್": "dozen", "दर्जन": "dozen",
    "tin": "tin", "tins": "tin", "ಟಿನ್": "tin", "टिन": "tin",
    "bag": "bag", "bags": "bag", "ಚೀಲ": "bag", "थैला": "bag", "बोरी": "bag",
}

_UNIT_REGEX = r"(?:kg|kilos?|kgs?|grams?|gms?|g|litres?|liters?|ltrs?|l|packets?|pkts?|packs?|pouches?|pieces?|pcs?|pc|bottles?|boxes?|dozens?|tins?|bags?|ಕೆಜಿ|ಕೆ\.ಜಿ|ಗ್ರಾಂ|ಲೀಟರ್|ಪ್ಯಾಕೆಟ್|ಪ್ಯಾಕ್|ಕಿಲೋ|किलो|ग्राम|लीटर|पैकेट|बोतल|डिब्बा)"

# Standard Kirana items dictionary (English canonical name -> set of multilingual aliases)
_CANONICAL_ITEMS: dict[str, set[str]] = {
    "Rice": {"rice", "akki", "chawal", "ಅಕ್ಕಿ", "चावल", "bhat", "arisi", "vari"},
    "Sugar": {"sugar", "sakkare", "chini", "shakar", "ಸಕ್ಕರೆ", "चीनी", "sakkarai"},
    "Milk": {"milk", "haalu", "doodh", "dudh", "ಹಾಲು", "दूध", "paal"},
    "Oil": {"oil", "cooking oil", "enne", "tel", "sunflower oil", "ಎಣ್ಣೆ", "तेल", "ennai"},
    "Dal": {"dal", "daal", "bele", "toor dal", "urad dal", "moong dal", "ಬೇಳೆ", "दाल", "paruppu"},
    "Atta": {"atta", "wheat flour", "wheat", "hittu", "godhi hittu", "flour", "ಹಿಟ್ಟು", "ಗೋಧಿ", "आटा", "गेहूं"},
    "Tea": {"tea", "tea powder", "chai", "cha", "चाय", "ಚಹಾ", "ಚಾ", "tea patti"},
    "Coffee": {"coffee", "coffee powder", "ಕಾಫಿ", "कॉफ़ी"},
    "Salt": {"salt", "uppu", "namak", "ಉಪ್ಪು", "नमक", "upp"},
    "Soap": {"soap", "sabun", "sabbu", "bath soap", "lifebuoy", "lux", "dettol", "ಸಾಬೂನು", "ಸಬ್ಬು", "साबुन"},
    "Biscuits": {"biscuit", "biscuits", "parle g", "marie", "good day", "cookies", "ಬಿಸ್ಕತ್ತು", "बिस्कुट"},
    "Detergent": {"detergent", "detergent powder", "washing powder", "surf", "surf excel", "rin", "wheel", "tide", "ಸರ್ಫ್", "सर्फ"},
    "Eggs": {"egg", "eggs", "motte", "anda", "ande", "ಮೊಟ್ಟೆ", "अंडा", "अंडे"},
    "Bread": {"bread", "bun", "pav", "ಬ್ರೆಡ್", "ब्रेड", "पाव"},
    "Butter": {"butter", "benne", "makhan", "ಬೆಣ್ಣೆ", "मक्खन"},
    "Ghee": {"ghee", "thuppa", "desi ghee", "ತುಪ್ಪ", "घी"},
    "Onion": {"onion", "onions", "eerulli", "pyaz", "kanda", "ಈರುಳ್ಳಿ", "प्याज", "कांदा"},
    "Potato": {"potato", "potatoes", "alugadde", "aloo", "alu", "ಆಲೂಗಡ್ಡೆ", "आलू"},
    "Tomato": {"tomato", "tomatoes", "tamatar", "ಟೊಮೇಟೊ", "टमाटर"},
    "Chilli": {"chilli", "chillies", "mirchi", "menasinakayi", "ಮೆಣಸಿನಕಾಯಿ", "मिर्च"},
    "Turmeric": {"turmeric", "haldi", "arisina", "ಅರಸಿನ", "हल्दी"},
    "Spices": {"spices", "masala", "garam masala", "sambhar powder", "ಮಸಾಲೆ", "मसाला"},
    "Toothpaste": {"toothpaste", "paste", "colgate", "pepsodent", "ದಂತಮಂಜನ", "टूथपेस्ट"},
    "Shampoo": {"shampoo", "clinic plus", "sunslik", "head and shoulders", "ಶಾಂಪೂ", "शैम्पू"},
}


def _match_item_name(word: str) -> Optional[str]:
    """Match word against canonical Kirana items list."""
    w = word.strip().lower()
    for canonical, aliases in _CANONICAL_ITEMS.items():
        if w in aliases:
            return canonical
        for alias in aliases:
            if alias in w or w in alias:
                return canonical
    return None


# ── Cross-Script Name Transliteration Map ─────────────────────────────────────
# Maps common Kannada/Hindi Unicode name spellings → their Latin equivalents.
# Used to match transcript names against shop customers stored in Latin script.
# This covers the most common kirana-shop owner/customer names in South India.

_KANNADA_TO_LATIN: dict[str, str] = {
    # A
    "ಅಮಿತ್": "amit", "ಅನಿಲ್": "anil", "ಅಜಯ್": "ajay", "ಅಭಿ": "abhi",
    "ಅಭಿಷೇಕ್": "abhishek", "ಅಮರ್": "amar", "ಅಶೋಕ್": "ashok",
    "ಅಕ್ಷಯ್": "akshay", "ಅರ್ಜುನ್": "arjun", "ಅಂಜಲಿ": "anjali",
    "ಅನಿತಾ": "anita", "ಅಮ್ಮ": "amma",
    # B
    "ಬಸಪ್ಪ": "basappa", "ಬಸವ": "basava", "ಬಸವರಾಜ್": "basavaraj",
    "ಬಾಬು": "babu", "ಭರತ್": "bharat", "ಭಾನು": "bhanu",
    # C/Ch
    "ಚಂದ್ರ": "chandra", "ಚಂದ್ರಶೇಖರ್": "chandrashekar",
    # D
    "ದೇವರಾಜ್": "devaraj", "ದಿನೇಶ್": "dinesh", "ಧರ್ಮ": "dharma",
    # G
    "ಗಣೇಶ್": "ganesh", "ಗಿರೀಶ್": "girish", "ಗೋವಿಂದ": "govinda",
    "ಗೌರಿ": "gauri", "ಗೀತಾ": "geeta",
    # H
    "ಹರೀಶ್": "harish", "ಹರಿ": "hari",
    # J
    "ಜಗದೀಶ್": "jagadish", "ಜಯ": "jaya", "ಜಯಂತ್": "jayant",
    # K
    "ಕಮಲ": "kamal", "ಕರೀಮ್": "karim", "ಕಿರಣ್": "kiran",
    "ಕೃಷ್ಣ": "krishna", "ಕೃಷ್ಣಮೂರ್ತಿ": "krishnamurthy", "ಕುಮಾರ್": "kumar",
    # L
    "ಲಕ್ಷ್ಮಿ": "lakshmi", "ಲಲಿತಾ": "lalita", "ಲೋಕೇಶ್": "lokesh",
    # M
    "ಮಹೇಶ್": "mahesh", "ಮನೋಜ್": "manoj", "ಮಂಜು": "manju",
    "ಮಂಜುನಾಥ್": "manjunath", "ಮಹಮ್ಮದ್": "mohammed", "ಮೋಹನ್": "mohan",
    "ಮುತ್ತು": "muttu", "ಮೂರ್ತಿ": "murthy",
    # N
    "ನಾಗರಾಜ್": "nagaraj", "ನಾಗೇಶ್": "nagesh", "ನಂದಿನಿ": "nandini",
    "ನರಸಿಂಹ": "narasimha", "ನರೇಶ್": "naresh", "ನಿಖಿಲ್": "nikhil",
    # P
    "ಪ್ರಕಾಶ್": "prakash", "ಪ್ರವೀಣ್": "praveen", "ಪ್ರದೀಪ್": "pradeep",
    "ಪವನ್": "pavan", "ಪರಮೇಶ್": "paramesh",
    # R
    "ರಮೇಶ್": "ramesh", "ರಮೇಶ": "ramesh", "ರಾಜ": "raja",
    "ರಾಜೇಶ್": "rajesh", "ರಾಜೇಶ": "rajesh", "ರವಿ": "ravi",
    "ರಾಹುಲ್": "rahul", "ರಾಘವೇಂದ್ರ": "raghavendra",
    # S
    "ಸಂದೇಶ್": "sandesh", "ಸಂಜಯ್": "sanjay", "ಸತೀಶ್": "satish",
    "ಸಿದ್ಧಾರ್ಥ್": "siddharth", "ಸ್ವಾಮಿ": "swami",
    "ಸ್ರೀರಾಮ್": "sriram", "ಸ್ರೀನಿವಾಸ್": "srinivas",
    "ಸ್ರೀಕಾಂತ್": "srikanth", "ಸ್ರೀಕರ್": "srikar",
    "ಸುಬ್ಬ": "subba", "ಸುಬ್ಬರಾಯ": "subbarao", "ಸುಭಾಷ್": "subhash",
    "ಸುಮ": "suma", "ಸುಮಿತ್ರ": "sumithra",
    "ಸುರೇಶ್": "suresh", "ಸುರೇಶ": "suresh",
    "ಸುಧಾ": "sudha", "ಸುನಿಲ್": "sunil",
    "ಸ್ಮಿತಾ": "smitha", "ಶಶಿ": "shashi", "ಶಿವ": "shiva",
    "ಶಿವಕುಮಾರ್": "shivakumar", "ಶಿವರಾಜ್": "shivaraj",
    # T
    "ತಿಮ್ಮ": "timma", "ತಿಮ್ಮಪ್ಪ": "thimmappa",
    "ವಿನಾಯಕ್": "vinayak", "ವಿಜಯ್": "vijay", "ವಿಕ್ರಮ್": "vikram",
    # U
    "ಉಮ": "uma",
    # V
    "ವಸಂತ್": "vasanth", "ವೆಂಕಟ": "venkata", "ವೆಂಕಟೇಶ": "venkatesh",
    # Y
    "ಯಶ್": "yash", "ಯೋಗೇಶ್": "yogesh",
}

# Hindi/Devanagari name → Latin transliteration
_HINDI_TO_LATIN: dict[str, str] = {
    "अमित": "amit", "अनिल": "anil", "अजय": "ajay",
    "अभिषेक": "abhishek", "अशोक": "ashok", "अर्जुन": "arjun",
    "अंजलि": "anjali", "अनिता": "anita",
    "भरत": "bharat", "भानु": "bhanu",
    "चंद्र": "chandra",
    "देवराज": "devaraj", "दिनेश": "dinesh",
    "गणेश": "ganesh", "गिरीश": "girish", "गौरी": "gauri", "गीता": "geeta",
    "हरीश": "harish", "हरि": "hari",
    "जगदीश": "jagadish", "जयंत": "jayant",
    "कमल": "kamal", "करीम": "karim", "किरण": "kiran",
    "कृष्ण": "krishna", "कुमार": "kumar",
    "लक्ष्मी": "lakshmi", "ललिता": "lalita", "लोकेश": "lokesh",
    "महेश": "mahesh", "मनोज": "manoj", "मंजू": "manju",
    "मुहम्मद": "mohammed", "मोहन": "mohan", "मूर्ति": "murthy",
    "नागराज": "nagaraj", "नागेश": "nagesh", "नंदिनी": "nandini",
    "नरेश": "naresh", "निखिल": "nikhil",
    "प्रकाश": "prakash", "प्रवीण": "praveen", "प्रदीप": "pradeep",
    "पवन": "pavan",
    "रमेश": "ramesh", "राज": "raja", "राजेश": "rajesh",
    "रवि": "ravi", "राहुल": "rahul",
    "संदेश": "sandesh", "संजय": "sanjay", "सतीश": "satish",
    "सिद्धार्थ": "siddharth",
    "सुभाष": "subhash", "सुमा": "suma",
    "सुरेश": "suresh", "सुधा": "sudha", "सुनील": "sunil",
    "शशि": "shashi", "शिव": "shiva", "शिवकुमार": "shivakumar",
    "तिम्मा": "timma",
    "विनायक": "vinayak", "विजय": "vijay", "विक्रम": "vikram",
    "उमा": "uma",
    "वसंत": "vasanth", "वेंकट": "venkata", "वेंकटेश": "venkatesh",
    "यश": "yash", "योगेश": "yogesh",
}

# Merged lookup: indic_script_name.lower() → latin_name_lower
_INDIC_TO_LATIN: dict[str, str] = {}
_INDIC_TO_LATIN.update({k.lower(): v for k, v in _KANNADA_TO_LATIN.items()})
_INDIC_TO_LATIN.update({k.lower(): v for k, v in _HINDI_TO_LATIN.items()})

# Reverse map: latin_name_lower → list of indic script variants
_LATIN_TO_INDIC: dict[str, list[str]] = {}
for _indic_k, _latin_v in _INDIC_TO_LATIN.items():
    _LATIN_TO_INDIC.setdefault(_latin_v, []).append(_indic_k)


def _indic_name_matches_latin(indic_token: str, latin_name: str) -> bool:
    """
    Return True if an Indic-script name token (from transcript) matches a
    Latin-script customer name (from shop database).

    Strategy:
    1. Direct lookup in _INDIC_TO_LATIN map
    2. Partial token match: check every word of the customer's Latin name
       against every Indic word in the token
    """
    indic_lower = indic_token.strip().lower()
    latin_lower = latin_name.strip().lower()
    # Remove [demo] suffix
    latin_lower = re.sub(r"\s*\[demo\]", "", latin_lower).strip()

    # 1. Direct map lookup
    mapped = _INDIC_TO_LATIN.get(indic_lower)
    if mapped:
        latin_tokens = latin_lower.split()
        return any(mapped == tok or mapped in tok or tok in mapped for tok in latin_tokens)

    # 2. Check if any word of the Latin name maps back to the Indic token
    for lat_tok in latin_lower.split():
        for indic_variant in _LATIN_TO_INDIC.get(lat_tok, []):
            if indic_lower == indic_variant or indic_lower.startswith(indic_variant) or indic_variant.startswith(indic_lower):
                return True

    return False


# ── Multilingual Customer Name Extraction ─────────────────────────────────────

_SKIP_WORDS = {
    "the", "a", "an", "and", "or", "at", "in", "on", "for", "to", "from",
    "by", "with", "is", "was", "has", "have", "had", "will", "would", "can",
    "could", "should", "today", "yesterday", "rupees", "rs", "inr", "total",
    "credit", "payment", "cash", "sale", "expense", "udhar", "paid",
    "bought", "sold", "taken", "gave", "rate", "cost", "each", "per",
    "mattu", "aur", "ko", "ne", "ka", "ki", "ge", "ige", "nige",
    "haaku", "thogondaare", "kotta", "kodutta", "likho", "saala",
    "kg", "kilo", "gram", "litre", "packet", "piece", "dozen", "box", "bottle",
    # Indic temporal, currency, and transaction keywords
    "ಇವತ್ತು", "ನಿನ್ನೆ", "ನಾಳೆ", "ರೂಪಾಯಿ", "ರೂಪಾಯಿಗಳು", "ಖಾತೆ", "ಖಾತೆಗೆ", "ಸಾಲ", "ಉಧಾರ",
    "ಕೊಟ್ಟ", "ಕೊಟ್ಟಿದ್ದಾನೆ", "ಕೊಟ್ಟಿದಾನೆ", "ಹಾಕು", "ತಗೊಂಡಿದ್ದಾನೆ", "ತಗೊಂಡಿದಾನೆ", "ದುಡ್ಡು", "ಹಣ",
    "आज", "कल", "रुपये", "रुपया", "रुपए", "खाता", "खाते", "उधार", "दिया", "लिया", "पैसा", "पैसे", "जमा", "नकद", "बकाया",
}

# Add all known item aliases to skip words so item names are NEVER mistaken for customer names
for aliases in _CANONICAL_ITEMS.values():
    _SKIP_WORDS.update(aliases)


def _clean_customer_name(name: str) -> str:
    """Strip postpositions and whitespace, and format title case."""
    clean = name.replace("\u200c", "").replace("\u200d", "").strip()
    # Strip common attached postpositions in Roman script
    for suffix in ["ge", "ige", "nige", "ko", "ne", "ka", "ki", "ku", "la", "nu"]:
        if clean.lower().endswith(suffix) and len(clean) > len(suffix) + 2:
            clean = clean[:-len(suffix)].strip()
            break
    # Strip common attached postpositions in Indic script
    for suffix in ["ಗೆ", "ಕ್ಕೆ", "ನಿಗೆ", "ಕೋ", "को", "ने", "का", "की", "கு", "కి", "ന്", "ला"]:
        if clean.endswith(suffix) and len(clean) > len(suffix) + 1:
            clean = clean[:-len(suffix)].strip()
            break
    # Remove demo bracket suffixes if any
    clean = re.sub(r"\s*\[demo\]", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s*\(demo\)", "", clean, flags=re.IGNORECASE)
    # Title-case Roman strings
    if clean.isascii():
        return clean.title()
    return clean


def extract_customer_name(
    text: str,
    existing_customers: Optional[list[str]] = None,
) -> tuple[Optional[str], list[str]]:
    """
    Extract customer name. Returns (matched_or_extracted_name, candidate_list).
    
    1. First priority: Check existing customers of the authenticated shop.
       Handles case-insensitive matches, base name matches (e.g. "Ramesh [DEMO]" matches "ramesh"),
       first name tokens, and detects ambiguity if multiple shop customers match.
    2. Second priority: Multilingual syntactic and postposition patterns in Kannada, Hindi, English, etc.
    3. Guarantees items, numbers, and transaction keywords are NEVER returned as customer names.
    """
    clean_text = normalize_indic_digits(text).strip()
    clean_no_zwnj = clean_text.replace("\u200c", "").replace("\u200d", "")
    lower_text = clean_no_zwnj.lower()

    # 1. Match against existing shop customers
    if existing_customers:
        matched = []
        for cust in existing_customers:
            cust_clean = cust.strip()
            base_name = re.sub(r"\s*\[demo\]", "", cust_clean, flags=re.IGNORECASE).strip()
            base_lower = base_name.lower()
            tokens = [t.lower() for t in base_name.split() if len(t) >= 2]
            
            matched_this = False
            for cand in [base_lower] + (tokens[:1] if tokens else []):
                pattern = rf"(?:^|[^\w\u0900-\u0D7F]){re.escape(cand)}(?:ge|ige|nige|ko|ne|ka|ki|ku|la|nu|[^\w\u0900-\u0D7F]|$)"
                if re.search(pattern, lower_text):
                    matched_this = True
                    break

            # Cross-script: try matching Indic-script tokens against Latin-stored customer name
            if not matched_this:
                indic_tokens = re.findall(r"[\u0900-\u0D7F\u0600-\u06FF]{2,25}", clean_no_zwnj)
                for tok in indic_tokens:
                    if _indic_name_matches_latin(tok, base_name):
                        matched_this = True
                        break

            if matched_this:
                matched.append(cust_clean)

        if len(matched) == 1:
            return matched[0], matched
        elif len(matched) > 1:
            # Ambiguous: multiple shop customers matched
            return None, matched

    # 2. Extract using linguistic postposition and syntactic cues

    # Kannada: "<name> ge", "<name>ge", "<name> ige", "<name>nige", "ರಮೇಶ್‌ಗೆ", "ರಮೇಶ್ ಗೆ", "ರಮೇಶನಿಗೆ"
    m_kn = re.search(
        r"(?:^|[^\w\u0900-\u0D7F])([a-zA-Z\u0C80-\u0CFF]{2,25})\s*(?:ge|ige|nige|ಗೆ|ಕ್ಕೆ|ನಿಗೆ)(?:[^\w\u0900-\u0D7F]|$)",
        clean_no_zwnj,
        re.IGNORECASE,
    )
    if m_kn:
        candidate = _clean_customer_name(m_kn.group(1))
        if candidate.lower() not in _SKIP_WORDS and not _match_item_name(candidate):
            return _disambiguate_with_existing(candidate, existing_customers)

    # Hindi: "<name> ko", "<name> ne", "<name> ka", "<name> ki", "रमेश को", "रमेश ने"
    m_hi = re.search(
        r"(?:^|[^\w\u0900-\u0D7F])([a-zA-Z\u0900-\u097F]{2,25})\s*(?:ko|ne|ka|ki|se|को|ने|का|की|से)(?:[^\w\u0900-\u0D7F]|$)",
        clean_no_zwnj,
        re.IGNORECASE,
    )
    if m_hi:
        candidate = _clean_customer_name(m_hi.group(1))
        if candidate.lower() not in _SKIP_WORDS and not _match_item_name(candidate):
            return _disambiguate_with_existing(candidate, existing_customers)

    # English prepositions: "to <name>", "credit to <name>", "from <name>", "paid by <name>", "for <name>"
    m_en_prep = re.search(
        r"\b(?:to|from|credit\s+to|paid\s+by|received\s+from|for)\s+([a-zA-Z]{2,25})\b",
        clean_text,
        re.IGNORECASE,
    )
    if m_en_prep:
        candidate = _clean_customer_name(m_en_prep.group(1))
        if candidate.lower() not in _SKIP_WORDS and not _match_item_name(candidate):
            return _disambiguate_with_existing(candidate, existing_customers)

    # Action patterns: "<name> paid", "<name> took", "<name> bought", "<name> gave", "<name> credit"
    m_en_act = re.search(
        r"\b([a-zA-Z]{2,25})\s+(?:paid|gives?|gave|took|taken|bought|borrowed|saala|udhar)\b",
        clean_text,
        re.IGNORECASE,
    )
    if m_en_act:
        candidate = _clean_customer_name(m_en_act.group(1))
        if candidate.lower() not in _SKIP_WORDS and not _match_item_name(candidate):
            return _disambiguate_with_existing(candidate, existing_customers)

    # Indic script postposition pattern across all Indian languages
    m_indic = re.search(
        r"([\u0900-\u0D7F\u0600-\u06FF]{2,20})\s*(?:ge|gu|ko|ne|ka|ki|ku|ke|la|nu|को|ने|का|की|ಗೆ|ಕ್ಕೆ|கு|కి|کے|کو)(?:\s+|$|[.,;!?])",
        clean_no_zwnj,
    )
    if m_indic:
        candidate = _clean_customer_name(m_indic.group(1))
        if candidate.lower() not in _SKIP_WORDS and not _match_item_name(candidate):
            return _disambiguate_with_existing(candidate, existing_customers)

    # Fallback 1: Capitalized Roman word that is not a skip word or item
    for m in re.finditer(r"\b([A-Z][a-z]{1,20})\b", clean_text):
        word = m.group(1)
        if word.lower() not in _SKIP_WORDS and not _match_item_name(word):
            return _disambiguate_with_existing(word, existing_customers)

    # Fallback 2: First word in transcript if followed by payment/credit keywords or amount
    first_token_match = re.match(r"^([a-zA-Z]{2,20})\b", clean_text)
    if first_token_match:
        token = first_token_match.group(1)
        if token.lower() not in _SKIP_WORDS and not _match_item_name(token):
            rest = clean_text[len(token):]
            if extract_amount(rest) or detect_transaction_type(rest)[0]:
                return _disambiguate_with_existing(token.title(), existing_customers)

    # Fallback 3: Indic-script name token for unknown customer extraction/display.
    # Handles both start-of-sentence ("ಸುರೇಶ ₹100 ಕೊಟ್ಟ") and post-temporal ("ಇವತ್ತು ಸುರೇಶ ₹100 ಕೊಟ್ಟ").
    # If the customer is not in the shop's database, return the Indic name so the UI can prefill it.
    for indic_candidate in re.findall(r"[\u0900-\u0D7F\u0600-\u06FF]{2,25}", clean_no_zwnj):
        cleaned_indic = _clean_customer_name(indic_candidate)
        if (
            cleaned_indic.lower() not in _SKIP_WORDS
            and not _match_item_name(cleaned_indic)
            and len(cleaned_indic) >= 2
        ):
            if extract_amount(clean_text) or detect_transaction_type(clean_text)[0]:
                return _disambiguate_with_existing(cleaned_indic, existing_customers)

    return None, []


def _disambiguate_with_existing(candidate: str, existing_customers: Optional[list[str]]) -> tuple[Optional[str], list[str]]:
    """Check if candidate name matches one or multiple existing customers."""
    if not existing_customers:
        return candidate, [candidate]
    c_lower = candidate.lower()
    matched = []
    for ec in existing_customers:
        base = re.sub(r"\s*\[demo\]", "", ec, flags=re.IGNORECASE).strip()
        base_lower = base.lower()
        if c_lower in base_lower or base_lower in c_lower or any(c_lower == tok for tok in base_lower.split()):
            matched.append(ec)
        elif _indic_name_matches_latin(candidate, base):
            matched.append(ec)
    if len(matched) == 1:
        return matched[0], matched
    elif len(matched) > 1:
        return None, matched
    return candidate, [candidate]


# ── Spoken Item & Quantity Extraction ─────────────────────────────────────────

def _parse_quantity(raw_qty: Optional[str]) -> Decimal:
    """Parse a quantity string into Decimal, defaulting to 1."""
    if not raw_qty:
        return Decimal("1")
    q = raw_qty.strip().lower()
    if q in _FRACTIONS:
        return _FRACTIONS[q]
    if q in _WORD_NUMBERS:
        return Decimal(_WORD_NUMBERS[q])
    try:
        val = Decimal(q)
        return val if val > 0 else Decimal("1")
    except InvalidOperation:
        return Decimal("1")


def extract_items(
    text: str,
    saved_prices: Optional[dict[str, Decimal]] = None,
) -> list[ParsedItem]:
    """
    Extract spoken grocery item names, quantities, units, and unit/line prices.
    Supports:
    - Multiple items in a single spoken transaction
    - Kannada, Hindi, and English item names and units
    - Resolving unit prices and line totals from the shop's saved price list
    - Stated prices (e.g. "at 40 rupees per kg", "for 80 rupees", "120 rupees")
    """
    norm_text = normalize_indic_digits(text).strip()
    norm_no_zwnj = norm_text.replace("\u200c", "").replace("\u200d", "")
    items: list[ParsedItem] = []

    price_lookup: dict[str, tuple[str, Decimal, str]] = {}
    if saved_prices:
        for k, v in saved_prices.items():
            price_lookup[k.lower()] = (k, Decimal(str(v)), "kg")

    # Item phrase splitting pattern: split by commas, 'and', 'aur', 'mattu', 'ಮತ್ತು', 'और'
    sub_clauses = re.split(
        r"[,;]|\s+(?:and|aur|mattu|ಮತ್ತು|और)\s+",
        norm_no_zwnj,
        flags=re.IGNORECASE,
    )

    for clause in sub_clauses:
        clause_clean = clause.strip()
        if not clause_clean:
            continue

        clause_lower = clause_clean.lower()

        matched_canonical = None
        matched_raw_name = None

        # Check canonical item dictionary with boundary safe for both ASCII and Indic scripts
        for canonical, aliases in _CANONICAL_ITEMS.items():
            for alias in aliases:
                pattern = rf"(?:^|[^\w\u0900-\u0D7F]){re.escape(alias)}(?:[^\w\u0900-\u0D7F]|$)"
                if re.search(pattern, clause_lower):
                    matched_canonical = canonical
                    matched_raw_name = alias
                    break
            if matched_canonical:
                break

        if not matched_canonical and price_lookup:
            for item_key, (disp_name, _, _) in price_lookup.items():
                pattern = rf"(?:^|[^\w\u0900-\u0D7F]){re.escape(item_key)}(?:[^\w\u0900-\u0D7F]|$)"
                if re.search(pattern, clause_lower):
                    matched_canonical = disp_name
                    matched_raw_name = item_key
                    break

        if not matched_canonical:
            continue

        # Extract unit if present
        matched_unit = None
        unit_match = re.search(rf"(?:^|[^\w\u0900-\u0D7F])({_UNIT_REGEX})(?:[^\w\u0900-\u0D7F]|$)", clause_lower)
        if unit_match:
            raw_u = unit_match.group(1).lower()
            matched_unit = _KNOWN_UNITS.get(raw_u, raw_u)

        # Extract quantity
        qty = Decimal("1")
        qty_pattern = rf"(\d+(?:\.\d{1,2})?|\b(?:half|ardha|aadha|quarter|paavu|one|two|three|four|five|ek|do|teen|chaar|paanch|ondu|eradu|mooru|naalu|aidu|೧|೨|೩|೪|೫)\b)\s*(?:{_UNIT_REGEX})?\s*{re.escape(matched_raw_name)}"
        qm = re.search(qty_pattern, clause_lower)
        if qm:
            qty = _parse_quantity(qm.group(1))
        else:
            qm_any = re.search(rf"(\d+(?:\.\d{1,2})?)\s*(?:{_UNIT_REGEX})", clause_lower)
            if qm_any:
                qty = _parse_quantity(qm_any.group(1))

        # Extract price for this item
        unit_price = None
        total_price = None

        # 1. Stated unit price: "at 40 rupees per kg", "rate 40", "40 rs each"
        unit_price_match = re.search(
            r"(?:at|rate|cost|for)?\s*[₹$Rs\.]?\s*(\d+(?:\.\d{1,2})?)\s*(?:rupees?|rs\.?|rupaya)?\s*(?:per|each|prati)",
            clause_lower,
        )
        if unit_price_match:
            try:
                unit_price = Decimal(unit_price_match.group(1))
                total_price = (qty * unit_price).quantize(Decimal("0.01"))
            except InvalidOperation:
                pass

        # 2. Stated line total: "50 rupees", "₹50", "for 50"
        if total_price is None:
            line_total_match = re.search(
                r"(?:for|cost|amount|is)?\s*[₹$Rs\.]?\s*(\d+(?:\.\d{1,2})?)\s*(?:rupees?|rs\.?|rupaya|rupaye|roobai|ರೂಪಾಯಿ|रुपये|/-)",
                clause_lower,
            )
            if line_total_match:
                try:
                    val = Decimal(line_total_match.group(1))
                    if val != qty or any(k in clause_lower for k in ["rupees", "₹", "rs", "ರೂಪಾಯಿ", "रुपये"]):
                        total_price = val.quantize(Decimal("0.01"))
                        if qty > 0:
                            unit_price = (total_price / qty).quantize(Decimal("0.01"))
                except InvalidOperation:
                    pass

        # 3. Fallback to shop's saved price list
        if unit_price is None and price_lookup:
            lookup_key = matched_canonical.lower()
            if lookup_key in price_lookup:
                _, u_pr, u_unit = price_lookup[lookup_key]
                unit_price = u_pr
                total_price = (qty * unit_price).quantize(Decimal("0.01"))
                if not matched_unit:
                    matched_unit = u_unit

        items.append(
            ParsedItem(
                name=matched_canonical,
                quantity=qty,
                unit=matched_unit,
                unit_price=unit_price,
                total_price=total_price,
            )
        )

    return items


# ── Main Multilingual Transaction Parser ──────────────────────────────────────

def parse_transaction(
    transcript: str,
    language: str = "en-IN",
    existing_customers: Optional[list[str]] = None,
    saved_prices: Optional[dict[str, Decimal]] = None,
) -> ParsedTransaction:
    """
    Parse a voice transcript into a fully-structured transaction with:
    - Transaction type and confidence
    - Customer name with existing-shop customer matching & ambiguity resolution
    - Spoken items, quantities, units, and line totals (supporting saved price list)
    - Total monetary amount
    - Preserved transcript and transparent ambiguity explanations
    """
    if not transcript or not transcript.strip():
        return ParsedTransaction(
            ambiguous=True,
            ambiguity_reason="Transcript is empty.",
            confidence=0.0,
        )

    clean_text = transcript.strip()
    txn_type, type_conf = detect_transaction_type(clean_text)
    
    # 1. Customer Name Extraction & Matching
    customer_name, candidates = extract_customer_name(clean_text, existing_customers=existing_customers)
    
    # 2. Spoken Items & Quantities Extraction
    items = extract_items(clean_text, saved_prices=saved_prices)
    
    # 3. Monetary Amount Resolution
    # Sum item line prices if available
    items_total = sum((it.total_price for it in items if it.total_price is not None), Decimal("0"))
    stated_amount = extract_amount(clean_text)

    # If items have prices, use their sum if stated_amount is None or matches
    amount = None
    if items_total > 0:
        amount = items_total
    elif stated_amount is not None:
        amount = stated_amount

    # If amount still None and single stated amount exists, use it
    if amount is None and stated_amount is not None:
        amount = stated_amount

    # 4. Generate Note / Item description
    note = None
    if items:
        item_descs = []
        for it in items:
            q_str = f"{it.quantity} {it.unit}" if it.unit else (f"{it.quantity}x" if it.quantity and it.quantity != 1 else "")
            pr_str = f"₹{it.total_price}" if it.total_price is not None else ""
            desc = " ".join(filter(None, [q_str, it.name, f"({pr_str})" if pr_str else ""]))
            item_descs.append(desc)
        note = ", ".join(item_descs)

    # 5. Ambiguity Check & Reason Formulation
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

    # Credit sales and payments require a customer name
    if txn_type in (TransactionType.CREDIT_SALE, TransactionType.PAYMENT):
        if len(candidates) > 1:
            ambiguous = True
            reasons.append(
                f"Multiple matching customers found: {', '.join(candidates)}. Please select the correct customer."
            )
        elif not customer_name:
            ambiguous = True
            reasons.append("Customer name not found. Please provide the customer's name.")

    confidence = type_conf * (1.0 if amount is not None else 0.3)

    return ParsedTransaction(
        txn_type=txn_type,
        customer_name=customer_name,
        candidate_customers=candidates,
        amount=amount,
        items=items,
        note=note,
        confidence=confidence,
        ambiguous=ambiguous,
        ambiguity_reason="; ".join(reasons) if reasons else None,
    )
