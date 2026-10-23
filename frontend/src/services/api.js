/**
 * BhashaFlow AI — Frontend API Client.
 * Connects to FastAPI backend endpoints.
 */

const API_BASE = '/api';

function getAuthHeader() {
  const token = localStorage.getItem('bhashaflow_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const api = {
  // ── Auth ──────────────────────────────────────────────────────────────────
  async register(data) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    const result = await res.json();
    localStorage.setItem('bhashaflow_token', result.access_token);
    localStorage.setItem('bhashaflow_shop', JSON.stringify({ id: result.shop_id, name: result.shop_name }));
    return result;
  },

  async login(phone, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    const result = await res.json();
    localStorage.setItem('bhashaflow_token', result.access_token);
    localStorage.setItem('bhashaflow_shop', JSON.stringify({ id: result.shop_id, name: result.shop_name }));
    return result;
  },

  async demoLogin() {
    const res = await fetch(`${API_BASE}/auth/demo`, {
      method: 'POST',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Demo login failed');
    }
    const result = await res.json();
    localStorage.setItem('bhashaflow_token', result.access_token);
    localStorage.setItem('bhashaflow_shop', JSON.stringify({ id: result.shop_id, name: result.shop_name, is_demo: true }));
    return result;
  },

  logout() {
    localStorage.removeItem('bhashaflow_token');
    localStorage.removeItem('bhashaflow_shop');
  },

  getSavedShop() {
    const shop = localStorage.getItem('bhashaflow_shop');
    return shop ? JSON.parse(shop) : null;
  },

  // ── Dashboard ─────────────────────────────────────────────────────────────
  async getDashboard(targetDate = null) {
    let url = `${API_BASE}/dashboard`;
    if (targetDate) url += `?target_date=${targetDate}`;
    const res = await fetch(url, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to load dashboard metrics');
    return res.json();
  },

  // ── Customers ─────────────────────────────────────────────────────────────
  async listCustomers(search = '') {
    let url = `${API_BASE}/customers`;
    if (search) url += `?search=${encodeURIComponent(search)}`;
    const res = await fetch(url, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to load customers');
    return res.json();
  },

  async createCustomer(data) {
    const res = await fetch(`${API_BASE}/customers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create customer');
    }
    return res.json();
  },

  async getCustomer(customerId) {
    const res = await fetch(`${API_BASE}/customers/${customerId}`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Customer not found');
    return res.json();
  },

  // ── Transactions ──────────────────────────────────────────────────────────
  async listTransactions(params = {}) {
    const query = new URLSearchParams();
    if (params.customerId) query.set('customer_id', params.customerId);
    if (params.txnType) query.set('txn_type', params.txnType);
    if (params.fromDate) query.set('from_date', params.fromDate);
    if (params.toDate) query.set('to_date', params.toDate);
    if (params.limit) query.set('limit', params.limit);

    const res = await fetch(`${API_BASE}/transactions?${query.toString()}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to load transactions');
    return res.json();
  },

  async createPendingTransaction(data) {
    const res = await fetch(`${API_BASE}/transactions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(typeof err.detail === 'string' ? err.detail : (err.detail?.message || 'Transaction validation failed'));
    }
    return res.json();
  },

  async confirmTransaction(transactionId, idempotencyKey = null) {
    const res = await fetch(`${API_BASE}/transactions/confirm`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ transaction_id: transactionId, idempotency_key: idempotencyKey }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to confirm transaction');
    }
    return res.json();
  },

  // ── Expenses ──────────────────────────────────────────────────────────────
  async listExpenses(limit = 50) {
    const res = await fetch(`${API_BASE}/expenses?limit=${limit}`, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to load expenses');
    return res.json();
  },

  async createExpense(data) {
    const res = await fetch(`${API_BASE}/expenses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to record expense');
    }
    return res.json();
  },

  async deleteExpense(expenseId) {
    const res = await fetch(`${API_BASE}/expenses/${expenseId}`, {
      method: 'DELETE',
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to delete expense');
    return true;
  },

  // ── Languages ─────────────────────────────────────────────────────────────
  async listLanguages() {
    const res = await fetch(`${API_BASE}/languages`);
    if (!res.ok) throw new Error('Failed to fetch languages');
    return res.json();
  },

  // ── STT (Gnani Prisma) ────────────────────────────────────────────────────
  async transcribeAudio(audioBlob, languageCode = 'kn-IN') {
    const formData = new FormData();
    const mime = audioBlob.type || 'audio/webm';
    const ext = mime.includes('wav') ? 'wav' : 'webm';
    formData.append('audio_file', audioBlob, `recording.${ext}`);
    formData.append('language_code', languageCode);

    const res = await fetch(`${API_BASE}/stt/transcribe`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || err.error || 'Speech transcription failed');
    }
    return res.json();
  },

  async parseTranscript(transcript, languageCode = 'kn-IN') {
    const formData = new FormData();
    formData.append('transcript', transcript);
    formData.append('language_code', languageCode);

    const res = await fetch(`${API_BASE}/stt/parse`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to parse transcript');
    return res.json();
  },

  // ── TTS (Gnani Timbre) ────────────────────────────────────────────────────
  async speakText(text, language = 'kn-IN', voice = 'Kaveri') {
    const res = await fetch(`${API_BASE}/tts/speak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({
        text,
        language,
        voice,
        model: 'timbre-v2.5',
        speed: 1.0,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Voice synthesis failed');
    }

    const audioBlob = await res.blob();
    return URL.createObjectURL(audioBlob);
  },
};
