# BhashaFlow AI (ಭಾಷಾಫ್ಲೋ / भाषाफ्लो)

> **Voice-Powered Multilingual Digital Udhar Ledger for Local Indian Grocery Shops (Kirana Stores)**  
> Built with FastAPI, SQLite/PostgreSQL, React, and Gnani AI (Prisma STT & Timbre TTS).

---

## 🌟 Overview

Across India, millions of local kirana store owners manage credit (*udhar*) in physical paper notebooks (*khata*). Paper records lead to lost debts, arithmetic disputes, and wasted bookkeeping time.

**BhashaFlow AI** lets shopkeepers speak naturally in their native Indian language:
- *"Ramesh ge 500 rupees udhar haaku"* (Kannada)
- *"Ramesh ko 500 rupaye udhar likho"* (Hindi)
- *"Ramesh paid 200 rupees"* (English)
- *"Cash sale 300 rupees"*
- *"Shop supplies 250 rupees expense"*

The application records real microphone audio, transcribes it using **Gnani Prisma STT**, deterministically extracts the transaction type, customer, and rupee amount, requires explicit visual confirmation, updates customer balances with decimal-safe financial accounting, and provides spoken confirmations in Indian voices via **Gnani Timbre TTS**.

---

## 📐 Core Architecture

```
[ Browser / Laptop / Mobile ]
         │  ▲
         │  │ 1. Real Audio Streams / REST API
         ▼  │
[ FastAPI Backend (Python 3.11) ] ── (Port 8000)
    ├── /api/stt/transcribe ──────────► Gnani Prisma STT (POST https://api.vachana.ai/stt/v3)
    ├── /api/tts/speak ───────────────► Gnani Timbre TTS (POST https://api.vachana.ai/api/v1/tts/inference)
    ├── /api/stt/parse ───────────────► Multilingual Indic Normalizer & Deterministic Parser
    ├── /api/languages ───────────────► Centralized Indian Language Registry (13 Languages)
    ├── /api/dashboard ───────────────► Exact Decimal Ledger Aggregations
    ├── /api/transactions ────────────► Immutable Transaction Ledger (Idempotent)
    ├── /api/customers ───────────────► Customer Directory & Derived Balances
    └── /api/expenses ────────────────► Shop Expense Tracking
         │
         ▼
[ SQLite / PostgreSQL Database ]
    ├── shops
    ├── customers
    ├── transactions (Numeric(12, 2) Decimal Storage)
    └── expenses
```

---

## ⚖️ Financial & Accounting Rules

All balances are **derived dynamically** from confirmed ledger entries—never cached:

$$\text{Outstanding Customer Debt} = \sum(\text{Credit Sales}) - \sum(\text{Payments Received})$$

| Action | Total Sales | Customer Debt | Cash Received | Expenses |
|---|---|---|---|---|
| **Credit Sale (Udhar)** | ⬆️ Increases | ⬆️ Increases | ➖ No Change | ➖ No Change |
| **Payment Against Debt** | ➖ No Change | ⬇️ Decreases | ⬆️ Increases | ➖ No Change |
| **Cash Sale** | ⬆️ Increases | ➖ No Change | ⬆️ Increases | ➖ No Change |
| **Shop Expense** | ➖ No Change | ➖ No Change | ⬇️ Reduced Net Cash | ⬆️ Increases |

*Example:*
- Credit sale: ₹500  
- Cash sale: ₹300  
- Payment against previous debt: ₹200  
- Expense: ₹100  
**Results:** Total Sales = ₹800, Total Cash Received = ₹500, Increase in Debt = ₹300, Net Cash = ₹400.

---

## 🗣️ Multilingual Capabilities

Centralized in [`backend/languages.py`](backend/languages.py) supporting 13 verified languages:
1. **Kannada (`kn-IN`)**: ಕನ್ನಡ (Voice: Kaveri)
2. **Hindi (`hi-IN`)**: हिन्दी (Voice: Nalini)
3. **English (`en-IN`)**: English (Voice: Deepak)
4. **Tamil (`ta-IN`)**: தமிழ் (Voice: Nalini)
5. **Telugu (`te-IN`)**: తెలుగు (Voice: Nalini)
6. **Malayalam (`ml-IN`)**: മലയാളം (Voice: Nalini)
7. **Marathi (`mr-IN`)**: मराठी (Voice: Nalini)
8. **Bengali (`bn-IN`)**: বাংলা (Voice: Nalini)
9. **Gujarati (`gu-IN`)**: ગુજરાતી (Voice: Nalini)
10. **Punjabi (`pa-IN`)**: ਪੰਜਾਬੀ (Voice: Nalini)
11. **Odia (`or-IN`)**: ଓଡ଼ିଆ (Voice: Nalini)
12. **Assamese (`as-IN`)**: অসমীয়া (Voice: Nalini)
13. **Urdu (`ur-IN`)**: اردو (Voice: Nalini, **Right-to-Left Layout**)

---

## 🚀 Running the Application

### Option A: Integrated Single-Port Mode (Recommended)

1. Make sure frontend is built:
   ```powershell
   cd frontend
   npm run build
   cd ..
   ```
2. Start the FastAPI backend server:
   ```powershell
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
3. Open your browser at:  
   👉 **`http://127.0.0.1:8000/`**  
   Click **"Enter 1-Click Demo Shop"** to instantly explore with pre-loaded realistic kirana data!

---

### Option B: Development Mode (Vite Hot-Reload)

1. Terminal 1 (Backend):
   ```powershell
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. Terminal 2 (Frontend):
   ```powershell
   cd frontend
   npm run dev
   ```
3. Open your browser at:  
   👉 **`http://localhost:5173/`**

---

## 🔑 Gnani AI Configuration

To enable live Gnani AI calls:
1. Create a `.env` file in the `backend/` directory:
   ```env
   GNANI_API_KEY=your_actual_gnani_api_key_here
   DATABASE_URL=sqlite:///./bhashaflow.db
   SECRET_KEY=generate_random_hex_key
   ```
2. The server reads `GNANI_API_KEY` exclusively on the backend. Secrets are **never exposed to the browser or frontend bundle**.
3. If no key is set, the application returns clear, authentic error messages with instant manual entry and zero simulation.

---

## 🧪 Running Automated Tests

Run the full pytest suite (58 unit and integration tests):
```powershell
python -m pytest backend/tests
```
All 58 tests pass covering:
- Credit sales increasing customer debt
- Payments reducing customer debt
- Cash sales excluding debt change
- Expense tracking and net cash movement
- Duplicate prevention via idempotency keys
- Multilingual entity extraction (Indic scripts, numerals, roman transliterations)
- Gnani Prisma STT & Timbre TTS error handling and audio byte validation
- Decimal precision & database isolation
