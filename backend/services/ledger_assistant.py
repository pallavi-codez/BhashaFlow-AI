"""
Deterministic natural-language financial query processor for "Ask Your Ledger".

Rules enforced:
- Strictly restricted to the authenticated shop.
- Exact Python Decimal arithmetic — no float rounding errors.
- Authoritative accounting rules:
    * Total sales = credit sales + cash sales.
    * Payments against old debt are NOT new sales.
    * Cash collected = cash sales + payments received.
    * Net cash movement = cash collected - expenses.
    * Outstanding balance = credit sales - payments received.
- Multilingual intent & entity extraction (Kannada, Hindi, Tamil, Telugu, English, etc.).
- Deterministic database aggregation (no hallucinated LLM figures).
- Timezone-aware date parsing (default Asia/Kolkata).
- If no records match or query is unsupported, states so truthfully.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import crud
from ..models import Customer, Expense, Shop, Transaction, TransactionType
from ..schemas import AskLedgerResponse, LedgerQueryDetailItem
from .parser import normalize_indic_digits

DEFAULT_TIMEZONE = ZoneInfo("Asia/Kolkata")

# Canonical cross-script mapping for common Indian shop customer names
INDIC_NAME_MAP = {
    # Kannada
    "ರಮೇಶ್": "ramesh", "ರಮೇಶ": "ramesh", "ರಮೇಶ್‌": "ramesh",
    "ಸುರೇಶ್": "suresh", "ಸುರೇಶ": "suresh", "ಸುರೇಶ್‌": "suresh",
    "ಲಕ್ಷ್ಮಿ": "lakshmi", "ಲಕ್ಷ್ಮೀ": "lakshmi",
    "ಗಣೇಶ್": "ganesh", "ಗಣೇಶ": "ganesh", "ಗಣೇಶ್‌": "ganesh",
    "ಮೀನಾ": "meena",
    # Devanagari (Hindi / Marathi)
    "रमेश": "ramesh",
    "सुरेश": "suresh",
    "लक्ष्मी": "lakshmi",
    "गणेश": "ganesh",
    "मीना": "meena",
    # Tamil
    "ரமேஷ்": "ramesh",
    "சுரேஷ்": "suresh",
    # Telugu
    "రమేష్": "ramesh",
    "సురేష్": "suresh",
}


def _canonical_name(name: str) -> str:
    """Normalize name for cross-script matching against DB records."""
    clean = re.sub(r"\s*\[demo\]", "", name, flags=re.IGNORECASE).strip().lower()
    clean = re.sub(r"[\u200c\u200d]", "", clean)
    return INDIC_NAME_MAP.get(clean, clean)


def _clean_query_cand(name: str) -> str:
    """Strip linguistic postpositions from candidate customer name."""
    clean = name.replace("\u200c", "").replace("\u200d", "").strip()
    # Strip common attached postpositions in Indic scripts
    for suffix in ["ಗೆ", "ಕ್ಕೆ", "ನಿಗೆ", "ಕೋ", "को", "ने", "का", "की", "கு", "க்கு", "కి", "ന്", "ला"]:
        if clean.endswith(suffix) and len(clean) > len(suffix) + 1:
            clean = clean[:-len(suffix)].strip()
            break
    # Strip common attached postpositions in Latin script
    for suffix in ["ge", "ige", "nige", "ko", "ne", "ka", "ki", "ku", "la", "nu"]:
        if clean.lower().endswith(suffix) and len(clean) > len(suffix) + 2:
            clean = clean[:-len(suffix)].strip()
            break
    return clean.strip(" \t\n\r?.,!;:'\"-")


def _get_shop_today(tz_name: str = "Asia/Kolkata") -> date:
    """Get today's date in the shop's timezone."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = DEFAULT_TIMEZONE
    return datetime.now(tz).date()


def _parse_date_range(text: str, shop_today: date) -> tuple[Optional[date], Optional[date], str]:
    """Parse date phrase from text into (start_date, end_date, label)."""
    t = text.lower()
    if (
        "yesterday" in t or "ninne" in t or "kal" in t
        or "ನಿನ್ನೆ" in t or "कल" in t or "நேற்று" in t or "నిన్న" in t
    ):
        y = shop_today - timedelta(days=1)
        return y, y, "yesterday"

    if (
        "this week" in t or "ee vara" in t or "is hafte" in t
        or "ಈ ವಾರ" in t or "इस हफ्ते" in t or "இந்த வாரம்" in t or "ఈ వారం" in t
    ):
        start = shop_today - timedelta(days=shop_today.weekday())
        return start, shop_today, "this week"

    if (
        "this month" in t or "ee tingalu" in t or "is mahine" in t
        or "ಈ ತಿಂಗಳು" in t or "इस महीने" in t or "இந்த மாதம்" in t or "ఈ నెల" in t
    ):
        start = date(shop_today.year, shop_today.month, 1)
        return start, shop_today, "this month"

    if (
        "all time" in t or "overall" in t or "so far" in t or "till now" in t
        or "ಎಲ್ಲಾ" in t or "ಒಟ್ಟಾರೆ" in t or "कुल" in t
    ):
        return date(2000, 1, 1), shop_today, "all time"

    # Default is today
    return shop_today, shop_today, "today"


def answer_ledger_query(
    db: Session,
    shop: Shop,
    query: str,
    language_code: str = "en-IN",
) -> AskLedgerResponse:
    """
    Process natural-language financial questions for the authenticated shop.
    Returns deterministic, validated financial figures with strict tenant isolation.
    """
    clean_q = normalize_indic_digits(query.strip())
    q_lower = clean_q.lower()
    shop_today = _get_shop_today()
    start_date, end_date, date_label = _parse_date_range(q_lower, shop_today)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. QUESTION INTENT: "Who owes me more than ₹1,000?" (Threshold debtors)
    # ──────────────────────────────────────────────────────────────────────────
    threshold_match = re.search(
        r"(?:who owes|owes me|customers? owing|debt over|balance over|more than|above|greater than|>|"
        r"se jyada|kinta hecchu|ಕ್ಕಿಂತ ಹೆಚ್ಚು|ಕ್ಕಿಂತ ಜಾಸ್ತಿ|से ज्यादा|से अधिक|से ऊपर|க்கும் மேல்|కంటే ఎక్కువ)\s*"
        r"[₹$Rs\.]?\s*(\d[\d,]*(?:\.\d{1,2})?)",
        q_lower,
    ) or re.search(
        r"(\d[\d,]*(?:\.\d{1,2})?)\s*(?:rupees|rs|inr|ರೂಪಾಯಿ|रुपये)?\s*"
        r"(?:se jyada|kinta hecchu|ಕ್ಕಿಂತ ಹೆಚ್ಚು|ಕ್ಕಿಂತ ಜಾಸ್ತಿ|से ज्यादा|से अधिक|से ऊपर|க்கும் மேல்|కంటే ఎక్కువ|more|above)",
        q_lower,
    )

    if (
        threshold_match
        or ("who owes" in q_lower and ("1000" in q_lower or "1,000" in q_lower or "500" in q_lower))
        or ("1000" in q_lower and ("ಹೆಚ್ಚು" in q_lower or "ज्यादा" in q_lower or "अधिक" in q_lower or "ಮೇಲ್" in q_lower or "ఎక్కువ" in q_lower))
    ):
        raw_val = "1000"
        if threshold_match:
            raw_val = threshold_match.group(1).replace(",", "")
        elif "1000" in q_lower or "1,000" in q_lower:
            raw_val = "1000"
        elif "500" in q_lower:
            raw_val = "500"

        try:
            threshold = Decimal(raw_val)
        except Exception:
            threshold = Decimal("1000")

        # Fetch all customers for this authenticated shop ONLY
        all_customers = crud.list_customers(db, shop.id)
        debtors = []
        for c in all_customers:
            bal = crud.compute_customer_balance(db, shop.id, c.id)
            if bal > threshold:
                debtors.append((c, bal))

        debtors.sort(key=lambda x: x[1], reverse=True)

        if not debtors:
            return AskLedgerResponse(
                query=clean_q,
                intent="debtors_above_threshold",
                answer=f"No customers currently owe more than ₹{threshold:,.2f}.",
                amount=Decimal("0.00"),
                details=[],
                no_records=True,
            )

        total_debt = sum((b for _, b in debtors), Decimal("0"))
        details = [
            LedgerQueryDetailItem(
                id=c.id,
                name=c.name,
                amount=bal,
                type="debt",
                extra=c.phone or "No phone",
            )
            for c, bal in debtors
        ]
        names_summary = ", ".join(f"{c.name} (₹{bal:,.2f})" for c, bal in debtors[:5])
        if len(debtors) > 5:
            names_summary += f", and {len(debtors) - 5} more"

        answer = (
            f"{len(debtors)} customer(s) owe more than ₹{threshold:,.2f}, totaling ₹{total_debt:,.2f}: {names_summary}."
        )
        return AskLedgerResponse(
            query=clean_q,
            intent="debtors_above_threshold",
            answer=answer,
            amount=total_debt,
            details=details,
            no_records=False,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 2. QUESTION INTENT: "Which customers have outstanding balances?" (All debtors)
    # ──────────────────────────────────────────────────────────────────────────
    if (
        "outstanding balances" in q_lower
        or "which customers have" in q_lower
        or "who owes me" in q_lower
        or "list all debtors" in q_lower
        or "customers with balance" in q_lower
        or "who has udhar" in q_lower
        or "udhar baki" in q_lower
        or "saala baki" in q_lower
        or "ಬಾಕಿ ಗ್ರಾಹಕರು" in q_lower
        or "ಯಾರಲ್ಲಿ ಬಾಕಿ ಇದೆ" in q_lower
        or "ಯಾರು ಸಾಲ ಹೊಂದಿದ್ದಾರೆ" in q_lower
        or "बाकी ग्राहक" in q_lower
        or "किस किस पर उधार है" in q_lower
        or "किस पर बाकी है" in q_lower
        or "யாருக்கு பாக்கி" in q_lower
        or "ఎవరికి బాకీ" in q_lower
    ):
        all_customers = crud.list_customers(db, shop.id)
        debtors = []
        for c in all_customers:
            bal = crud.compute_customer_balance(db, shop.id, c.id)
            if bal > 0:
                debtors.append((c, bal))

        debtors.sort(key=lambda x: x[1], reverse=True)

        if not debtors:
            return AskLedgerResponse(
                query=clean_q,
                intent="all_debtors",
                answer="No customers currently have outstanding balances. All accounts are settled!",
                amount=Decimal("0.00"),
                details=[],
                no_records=True,
            )

        total_debt = sum((b for _, b in debtors), Decimal("0"))
        details = [
            LedgerQueryDetailItem(
                id=c.id,
                name=c.name,
                amount=bal,
                type="outstanding",
                extra=c.phone or "No phone",
            )
            for c, bal in debtors
        ]
        summary_str = ", ".join(f"{c.name} (₹{bal:,.2f})" for c, bal in debtors[:6])
        if len(debtors) > 6:
            summary_str += f", and {len(debtors) - 6} more"

        answer = (
            f"There are {len(debtors)} customer(s) with outstanding balances, totaling ₹{total_debt:,.2f}: {summary_str}."
        )
        return AskLedgerResponse(
            query=clean_q,
            intent="all_debtors",
            answer=answer,
            amount=total_debt,
            details=details,
            no_records=False,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 3. QUESTION INTENT: "How much does <Name> owe?" (Individual customer balance)
    # ──────────────────────────────────────────────────────────────────────────
    # Clean query for regex search
    cand_name = None

    # Kannada: "ರಮೇಶ್ ಎಷ್ಟು ಹಣ ಕೊಡಬೇಕು?", "ರಮೇಶ್ ಎಷ್ಟು ಬಾಕಿ?", "ರಮೇಶ್‌ಗೆ ಎಷ್ಟು ಬಾಕಿ ಇದೆ?"
    m_kn = re.search(r"([a-zA-Z\u0C80-\u0CFF]+)\s*(?:ಗೆ|ige|nige)?\s+ಎಷ್ಟು\s*(?:ಹಣ)?\s*(?:ಕೊಡಬೇಕು|ಬಾಕಿ|ಸಾಲ|ಇದೆ)", clean_q)
    if m_kn:
        cand_name = m_kn.group(1).strip()

    # Hindi: "रमेश पर कितना उधार बाकी है?", "रमेश का कितना बाकी है?", "रमेश को कितना देना है?"
    if not cand_name:
        m_hi = re.search(r"([a-zA-Z\u0900-\u097F]+)\s*(?:पर|का|की|को|se)?\s*कितना\s*(?:उधार|बाकी|पैसे|देना)\s*(?:बाकी|देना|है)?", clean_q)
        if m_hi:
            cand_name = m_hi.group(1).strip()

    # Telugu: "రమేష్ ఎంత ఇవ్వాలి?", "రమేష్ ఎంత బాకీ?"
    if not cand_name:
        m_te = re.search(r"([a-zA-Z\u0C00-\u0C7F]+)\s*(?:కి)?\s*ఎంత\s*(?:ఇవ్వాలి|బాకీ|అప్పు)", clean_q)
        if m_te:
            cand_name = m_te.group(1).strip()

    # Tamil: "ரமேஷ் எவ்வளவு தர வேண்டும்?", "ரமேஷ் பாக்கி எவ்வளவு?"
    if not cand_name:
        m_ta = re.search(r"([a-zA-Z\u0B80-\u0BFF]+)\s*(?:க்கு)?\s*எவ்வளவு\s*(?:தர\s*வேண்டும்|பாக்கி|கடன்)", clean_q)
        if m_ta:
            cand_name = m_ta.group(1).strip()

    # English / Transliterated
    if not cand_name:
        name_owe_match = (
            re.search(r"(?:how much|what)\s+(?:does|do)?\s*([a-zA-Z0-9\u0900-\u0D7F\s\.\-]+?)\s*(?:owe|have to pay|baki|saala)", q_lower)
            or re.search(r"what is\s*([a-zA-Z0-9\u0900-\u0D7F\s\.\-]+?)(?:'s)?\s*(?:balance|udhar|outstanding|debt)", q_lower)
            or re.search(r"balance (?:of|for)\s*([a-zA-Z0-9\u0900-\u0D7F\s\.\-]+)", q_lower)
            or re.search(r"([a-zA-Z0-9\u0900-\u0D7F\s\.\-]+?)\s*(?:ka|ge|ki|ku|nu)?\s*(?:kitna baki|eshtu baki|eshtu saala|balance)", q_lower)
            or re.search(r"([a-zA-Z0-9\u0900-\u0D7F\s\.\-]+?)\s*owes?", q_lower)
        )
        if name_owe_match:
            cand_name = name_owe_match.group(1).strip()

    if cand_name:
        cand_name = _clean_query_cand(cand_name)
        skip_words = {
            "the", "does", "much", "many", "what", "how", "who", "any", "me", "i", "my", "we", "a", "an",
            "today", "yesterday", "indu", "aaj", "ಎಷ್ಟು", "ಇಂದು", "ಇವತ್ತು", "आज", "कितना",
            # Financial keywords that cannot be customer names
            "खर्च", "खर्चा", "ಖರ್ಚು", "ವೆಚ್ಚ", "ಮಾರಾಟ", "ವ್ಯಾಪಾರ", "बिक्री", "सेल", "नकद", "कैश", "ಹಣ", "ನಗದು",
            "उधार", "ಉದ್ಧಾರ", "ಸಾಲ", "udhar", "kadan", "appu", "credit", "cash", "expense", "sale", "sales"
        }
        if cand_name.lower() not in skip_words and len(cand_name) >= 2:
            all_customers = crud.list_customers(db, shop.id)
            cand_canon = _canonical_name(cand_name)

            matched = []
            for c in all_customers:
                base_name = re.sub(r"\s*\[demo\]", "", c.name, flags=re.IGNORECASE).strip()
                base_canon = _canonical_name(base_name)

                # Cross-script and substring matching
                if (
                    cand_canon == base_canon
                    or cand_name.lower() in base_name.lower()
                    or base_name.lower() in cand_name.lower()
                    or cand_canon in base_canon
                ):
                    matched.append(c)

            if not matched:
                return AskLedgerResponse(
                    query=clean_q,
                    intent="customer_balance",
                    answer=f"No customer found with the name '{cand_name.title()}' in your shop records.",
                    amount=None,
                    details=[],
                    no_records=True,
                )

            if len(matched) > 1:
                # Check for exact canonical match priority
                exact = [c for c in matched if _canonical_name(re.sub(r"\s*\[demo\]", "", c.name, flags=re.IGNORECASE).strip()) == cand_canon]
                if len(exact) == 1:
                    matched = exact

            if len(matched) > 1:
                candidate_names = [c.name for c in matched]
                return AskLedgerResponse(
                    query=clean_q,
                    intent="customer_balance",
                    answer=(
                        f"Found {len(matched)} customers matching '{cand_name.title()}': {', '.join(candidate_names)}. "
                        "Please specify the exact customer."
                    ),
                    clarification_needed=True,
                    candidates=candidate_names,
                    details=[
                        LedgerQueryDetailItem(
                            id=c.id,
                            name=c.name,
                            amount=crud.compute_customer_balance(db, shop.id, c.id),
                            type="candidate",
                            extra=c.phone or "No phone",
                        )
                        for c in matched
                    ],
                )

            # Exactly one matched customer
            target_cust = matched[0]
            balance = crud.compute_customer_balance(db, shop.id, target_cust.id)

            if balance > 0:
                answer = f"{target_cust.name} owes ₹{balance:,.2f}."
            elif balance == 0:
                answer = f"{target_cust.name} has no outstanding balance. Current balance is ₹0.00."
            else:
                answer = f"{target_cust.name} has an advance credit / overpayment of ₹{abs(balance):,.2f}."

            return AskLedgerResponse(
                query=clean_q,
                intent="customer_balance",
                answer=answer,
                amount=balance,
                details=[
                    LedgerQueryDetailItem(
                        id=target_cust.id,
                        name=target_cust.name,
                        amount=balance,
                        type="balance",
                        extra=target_cust.phone or "No phone",
                    )
                ],
                no_records=False,
            )

    # ──────────────────────────────────────────────────────────────────────────
    # 4. QUESTION INTENT: "How much credit did I give today?" (Credit sales)
    # ──────────────────────────────────────────────────────────────────────────
    if (
        "credit did i give" in q_lower
        or "credit gave" in q_lower
        or "credit given" in q_lower
        or "udhar diya" in q_lower
        or "saala kotte" in q_lower
        or "credit sales" in q_lower
        or "total udhar" in q_lower
        or "how much credit" in q_lower
        or "ಉದ್ಧಾರ ಕೊಟ್" in q_lower
        or "ಸಾಲ ಕೊಟ್" in q_lower
        or "ಉದ್ಧಾರ ಎಷ್ಟು" in q_lower
        or "ಎಷ್ಟು ಉದ್ಧಾರ" in q_lower
        or "उधार दिया" in q_lower
        or "कितना उधार दिया" in q_lower
        or "उधार की बिक्री" in q_lower
        or "கடன் கொடுத்த" in q_lower
        or "அప్పు ఇచ్చా" in q_lower
    ):
        start_dt = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999)

        txns = list(db.scalars(
            select(Transaction).where(
                Transaction.shop_id == shop.id,
                Transaction.txn_type == TransactionType.CREDIT_SALE,
                Transaction.confirmed == True,  # noqa: E712
                Transaction.created_at >= start_dt,
                Transaction.created_at <= end_dt,
            ).order_by(Transaction.created_at.desc())
        ).all())

        total_credit = sum((t.amount for t in txns), Decimal("0.00"))

        details = []
        for t in txns:
            c_name = "Customer"
            if t.customer_id:
                c = crud.get_customer(db, shop.id, t.customer_id)
                if c:
                    c_name = c.name
            details.append(
                LedgerQueryDetailItem(
                    id=t.id,
                    name=c_name,
                    amount=t.amount,
                    type="CREDIT_SALE",
                    date=t.created_at.strftime("%I:%M %p"),
                    extra=t.note or "",
                )
            )

        if total_credit == 0:
            answer = f"You gave no credit {date_label} (₹0.00 across 0 transactions)."
            no_rec = True
        else:
            answer = f"You gave ₹{total_credit:,.2f} in credit {date_label} across {len(txns)} transaction(s)."
            no_rec = False

        return AskLedgerResponse(
            query=clean_q,
            intent="credit_sales",
            answer=answer,
            amount=total_credit,
            details=details,
            no_records=no_rec,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 5. QUESTION INTENT: "How much cash did I collect today?" (Cash collected)
    # ──────────────────────────────────────────────────────────────────────────
    if (
        "cash did i collect" in q_lower
        or "cash collected" in q_lower
        or "cash received" in q_lower
        or "cash in hand" in q_lower
        or ("cash" in q_lower and "collect" in q_lower)
        or "nagad collect" in q_lower
        or "nagadu banthu" in q_lower
        or "paise jama" in q_lower
        or "ನಗದು ಬಂತು" in q_lower
        or "ನಗದು ಸಂಗ್ರಹ" in q_lower
        or "ಹಣ ಬಂತು" in q_lower
        or "ಎಷ್ಟು ನಗದು" in q_lower
        or "कैश आया" in q_lower
        or "कैश मिला" in q_lower
        or "नकद मिला" in q_lower
        or "नकद आया" in q_lower
        or "पैसा जमा" in q_lower
        or "कितना कैश" in q_lower
        or "कितना नकद" in q_lower
        or "कैश इकट्ठा" in q_lower
        or "பணம் வசூல்" in q_lower
        or "నగదు వచ్చింది" in q_lower
        or "ఎంత నగదు" in q_lower
    ):
        start_dt = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999)

        # Cash collected = Cash Sales + Debt Repayments Received
        cash_sales_amt = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.shop_id == shop.id,
                Transaction.txn_type == TransactionType.CASH_SALE,
                Transaction.confirmed == True,  # noqa: E712
                Transaction.created_at >= start_dt,
                Transaction.created_at <= end_dt,
            )
        ) or Decimal("0.00")

        payments_amt = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.shop_id == shop.id,
                Transaction.txn_type == TransactionType.PAYMENT,
                Transaction.confirmed == True,  # noqa: E712
                Transaction.created_at >= start_dt,
                Transaction.created_at <= end_dt,
            )
        ) or Decimal("0.00")

        total_collected = Decimal(str(cash_sales_amt)) + Decimal(str(payments_amt))

        details = [
            LedgerQueryDetailItem(
                name="Counter Cash Sales",
                amount=Decimal(str(cash_sales_amt)),
                type="CASH_SALE",
            ),
            LedgerQueryDetailItem(
                name="Debt Repayments Received",
                amount=Decimal(str(payments_amt)),
                type="PAYMENT",
            ),
        ]

        if total_collected == 0:
            answer = f"You collected no cash {date_label} (₹0.00)."
            no_rec = True
        else:
            answer = (
                f"You collected ₹{total_collected:,.2f} in cash {date_label} "
                f"(₹{Decimal(str(cash_sales_amt)):,.2f} from cash sales + "
                f"₹{Decimal(str(payments_amt)):,.2f} from debt repayments)."
            )
            no_rec = False

        return AskLedgerResponse(
            query=clean_q,
            intent="cash_collected",
            answer=answer,
            amount=total_collected,
            details=details,
            no_records=no_rec,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 6. QUESTION INTENT: "What were my expenses today?" (Expenses)
    # ──────────────────────────────────────────────────────────────────────────
    if (
        "expenses" in q_lower
        or "expense" in q_lower
        or "how much did i spend" in q_lower
        or "spent today" in q_lower
        or "spend" in q_lower
        or "spent" in q_lower
        or "kharcha" in q_lower
        or "kharchu" in q_lower
        or "ಖರ್ಚು" in q_lower
        or "ವೆಚ್ಚ" in q_lower
        or "खर्च" in q_lower
        or "खर्चा" in q_lower
        or "செலவு" in q_lower
        or "ఖర్చు" in q_lower
    ):
        start_dt = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999)

        exp_list = list(db.scalars(
            select(Expense).where(
                Expense.shop_id == shop.id,
                Expense.created_at >= start_dt,
                Expense.created_at <= end_dt,
            ).order_by(Expense.created_at.desc())
        ).all())

        txn_exp_list = list(db.scalars(
            select(Transaction).where(
                Transaction.shop_id == shop.id,
                Transaction.txn_type == TransactionType.EXPENSE,
                Transaction.confirmed == True,  # noqa: E712
                Transaction.created_at >= start_dt,
                Transaction.created_at <= end_dt,
            ).order_by(Transaction.created_at.desc())
        ).all())

        total_expenses = sum((e.amount for e in exp_list), Decimal("0.00")) + sum((t.amount for t in txn_exp_list), Decimal("0.00"))

        details = [
            LedgerQueryDetailItem(
                id=e.id,
                name=e.category.title(),
                amount=e.amount,
                type="expense",
                extra=e.note or "Direct expense",
                date=e.created_at.strftime("%I:%M %p"),
            )
            for e in exp_list
        ] + [
            LedgerQueryDetailItem(
                id=t.id,
                name="Shop Expense",
                amount=t.amount,
                type="expense",
                extra=t.note or "Transaction expense",
                date=t.created_at.strftime("%I:%M %p"),
            )
            for t in txn_exp_list
        ]

        if total_expenses == 0:
            answer = f"You recorded no expenses {date_label} (₹0.00)."
            no_rec = True
        else:
            answer = f"Your expenses {date_label} were ₹{total_expenses:,.2f} across {len(details)} item(s)."
            no_rec = False

        return AskLedgerResponse(
            query=clean_q,
            intent="expenses",
            answer=answer,
            amount=total_expenses,
            details=details,
            no_records=no_rec,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 7. QUESTION INTENT: "How much did I sell today?" (Total Sales)
    # ──────────────────────────────────────────────────────────────────────────
    if (
        "did i sell" in q_lower
        or "total sales" in q_lower
        or "today sales" in q_lower
        or "total sell" in q_lower
        or "sales today" in q_lower
        or "my sales" in q_lower
        or "sell" in q_lower
        or "sales" in q_lower
        or "sold" in q_lower
        or "bikri" in q_lower
        or "marata" in q_lower
        or "ಮಾರಾಟ" in q_lower
        or "ವ್ಯಾಪಾರ" in q_lower
        or "बिक्री" in q_lower
        or "धंधा" in q_lower
        or "माल बिका" in q_lower
        or "सेल" in q_lower
        or "விற்பனை" in q_lower
        or "అమ్మకాలు" in q_lower
    ):
        start_dt = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, 999999)

        credit_sales = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.shop_id == shop.id,
                Transaction.txn_type == TransactionType.CREDIT_SALE,
                Transaction.confirmed == True,  # noqa: E712
                Transaction.created_at >= start_dt,
                Transaction.created_at <= end_dt,
            )
        ) or Decimal("0.00")

        cash_sales = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.shop_id == shop.id,
                Transaction.txn_type == TransactionType.CASH_SALE,
                Transaction.confirmed == True,  # noqa: E712
                Transaction.created_at >= start_dt,
                Transaction.created_at <= end_dt,
            )
        ) or Decimal("0.00")

        # Strict Accounting Rule: Total sales = Credit Sales + Cash Sales. Repayments are NOT sales.
        total_sales = Decimal(str(credit_sales)) + Decimal(str(cash_sales))

        details = [
            LedgerQueryDetailItem(
                name="Credit Sales (Udhar)",
                amount=Decimal(str(credit_sales)),
                type="CREDIT_SALE",
            ),
            LedgerQueryDetailItem(
                name="Cash Sales",
                amount=Decimal(str(cash_sales)),
                type="CASH_SALE",
            ),
        ]

        if total_sales == 0:
            answer = f"You recorded no sales {date_label} (₹0.00 total sales)."
            no_rec = True
        else:
            answer = (
                f"Your total sales {date_label} are ₹{total_sales:,.2f} "
                f"(₹{Decimal(str(credit_sales)):,.2f} credit sales + ₹{Decimal(str(cash_sales)):,.2f} cash sales)."
            )
            no_rec = False

        return AskLedgerResponse(
            query=clean_q,
            intent="total_sales",
            answer=answer,
            amount=total_sales,
            details=details,
            no_records=no_rec,
        )

    # ──────────────────────────────────────────────────────────────────────────
    # 8. GENERAL INTENT FALLBACK
    # ──────────────────────────────────────────────────────────────────────────
    return AskLedgerResponse(
        query=clean_q,
        intent="unknown",
        answer=(
            "I could not understand that ledger question. You can ask questions such as:\n"
            "• 'How much does Ramesh owe?' / 'ರಮೇಶ್ ಎಷ್ಟು ಹಣ ಕೊಡಬೇಕು?' / 'रमेश पर कितना उधार बाकी है?'\n"
            "• 'How much credit did I give today?' / 'ಇಂದು ಎಷ್ಟು ಉದ್ಧಾರ ಕೊಟ್ಟೆ?' / 'आज कितना उधार दिया?'\n"
            "• 'Who owes me more than ₹1,000?' / '1000 ಕ್ಕಿಂತ ಹೆಚ್ಚು ಬಾಕಿ ಯಾರಲ್ಲಿದೆ?' / '1000 से ज्यादा उधार किस पर है?'\n"
            "• 'How much cash did I collect today?' / 'ಇಂದು ಎಷ್ಟು ನಗದು ಬಂತು?' / 'आज कितना कैश आया?'\n"
            "• 'What were my expenses today?' / 'ಇಂದಿನ ಖರ್ಚು ಎಷ್ಟು?' / 'आज का खर्च कितना हुआ?'\n"
            "• 'Which customers have outstanding balances?'\n"
            "• 'How much did I sell today?' / 'ಇಂದು ಎಷ್ಟು ಮಾರಾಟವಾಗಿದೆ?' / 'आज कितनी बिक्री हुई?'"
        ),
        amount=None,
        details=[],
        no_records=True,
    )
