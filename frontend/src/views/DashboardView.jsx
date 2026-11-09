import React, { useState } from 'react';
import {
  IndianRupee,
  ArrowDownLeft,
  ArrowUpRight,
  TrendingUp,
  Wallet,
  CreditCard,
  Plus,
  Mic,
  CheckCircle,
  CheckCircle2,
  Users,
  Receipt,
  AlertCircle,
  HelpCircle,
  Sparkles,
  Search,
  RefreshCw,
  ArrowRight,
  Calendar,
  Zap,
  Tag
} from 'lucide-react';
import { getTranslation } from '../i18n/translations';
import { api } from '../services/api';

export default function DashboardView({
  stats,
  transactions = [],
  currentLang = 'en-IN',
  languages = [],
  onOpenVoice,
  onOpenCustomerModal,
  onOpenExpenseModal,
  setCurrentView,
  shop
}) {
  const [askQuery, setAskQuery] = useState('');
  const [askLoading, setAskLoading] = useState(false);
  const [askError, setAskError] = useState(null);
  const [askResult, setAskResult] = useState(null);

  const t = (k) => getTranslation(currentLang, k);

  const activeLangConfig = languages.find((l) => l.code === currentLang) || {
    sample_phrase: 'Ramesh paid 200 rupees',
    name: 'English',
  };

  const totalSales = Number(stats?.total_credit_sales || 0) + Number(stats?.total_cash_sales || 0);

  // Formatted current date
  const todayFormatted = new Date().toLocaleDateString('en-IN', {
    weekday: 'long',
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });

  async function handleQuickAsk(qText) {
    const q = (qText !== undefined ? qText : askQuery).trim();
    if (!q) return;

    setAskQuery(q);
    setAskLoading(true);
    setAskError(null);

    try {
      const resp = await api.askLedger(q, currentLang);
      setAskResult(resp);
    } catch (err) {
      setAskError(err.message || 'Failed to answer question');
      setAskResult(null);
    } finally {
      setAskLoading(false);
    }
  }

  return (
    <div>
      {/* ── 1. PERSONALIZED WELCOME & STATUS HEADER ─────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 28, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <h2 style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--deep-forest)', margin: 0 }}>
              Namaste, {shop?.owner_name || shop?.name || 'Merchant'} 👋
            </h2>
            {shop?.is_demo && (
              <span className="demo-indicator-badge">
                <Zap size={12} color="#D97706" />
                <span>Demo Store</span>
              </span>
            )}
          </div>
          <p style={{ fontSize: '0.88rem', color: 'var(--muted-text)', margin: 0 }}>
            {shop?.name || 'My Kirana Store'} &bull; {todayFormatted} &bull; {activeLangConfig.name} Voice Active
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={onOpenVoice}
            style={{ borderRadius: 'var(--radius-full)', padding: '10px 20px', boxShadow: '0 4px 14px rgba(22, 134, 90, 0.3)' }}
          >
            <Mic size={17} />
            <span>Record Voice Entry</span>
          </button>
        </div>
      </div>

      {/* ── 2. METRIC CARDS GRID ───────────────────────────────────────────── */}
      <div className="metrics-grid">
        {/* Card 1: Today's Total Sales */}
        <div className="metric-card metric-sales">
          <div className="metric-header">
            <span className="metric-label">Today's Sales</span>
            <div className="metric-icon-box">
              <TrendingUp size={20} />
            </div>
          </div>
          <div className="metric-value">
            ₹{totalSales.toFixed(2)}
          </div>
          <div className="metric-footer">
            Credit: ₹{stats?.total_credit_sales || '0.00'} &bull; Cash: ₹{stats?.total_cash_sales || '0.00'}
          </div>
        </div>

        {/* Card 2: Cash Received Today */}
        <div className="metric-card metric-cash">
          <div className="metric-header">
            <span className="metric-label">Cash Collected</span>
            <div className="metric-icon-box">
              <Wallet size={20} />
            </div>
          </div>
          <div className="metric-value">
            ₹{stats?.total_cash_received !== undefined ? stats.total_cash_received : '0.00'}
          </div>
          <div className="metric-footer">
            Cash Sales (₹{stats?.total_cash_sales || '0'}) + Debt Paid (₹{stats?.total_payments_received || '0'})
          </div>
        </div>

        {/* Card 3: Total Outstanding Customer Udhar */}
        <div className="metric-card metric-debt">
          <div className="metric-header">
            <span className="metric-label">Outstanding Udhar</span>
            <div className="metric-icon-box">
              <AlertCircle size={20} />
            </div>
          </div>
          <div className="metric-value" style={{ color: Number(stats?.total_outstanding || 0) > 0 ? '#B45309' : 'inherit' }}>
            ₹{stats?.total_outstanding !== undefined ? stats.total_outstanding : '0.00'}
          </div>
          <div className="metric-footer">
            Across {stats?.total_customers || 0} active customer accounts
          </div>
        </div>

        {/* Card 4: Today's Expenses */}
        <div className="metric-card metric-expense">
          <div className="metric-header">
            <span className="metric-label">Shop Expenses</span>
            <div className="metric-icon-box">
              <CreditCard size={20} />
            </div>
          </div>
          <div className="metric-value">
            ₹{stats?.total_expenses !== undefined ? stats.total_expenses : '0.00'}
          </div>
          <div className="metric-footer">
            Net cash movement: ₹{stats?.net_cash_movement || '0.00'}
          </div>
        </div>
      </div>

      {/* ── 3. VOICE ACTION BANNER ─────────────────────────────────────────── */}
      <div className="voice-banner">
        <div className="voice-banner-content">
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'rgba(255,255,255,0.15)', padding: '4px 10px', borderRadius: 9999, fontSize: '0.74rem', fontWeight: 700, marginBottom: 8 }}>
            <Mic size={13} color="#DDF4E6" />
            <span>VOICE-FIRST REGIONAL ENTRY</span>
          </div>
          <h3 className="voice-banner-title">Speak naturally in your mother tongue</h3>
          <p className="voice-banner-subtitle">
            Say customer name, amount, and items — BhashaFlow handles parsing, matching, and bookkeeping in seconds.
          </p>

          <div className="voice-banner-examples">
            <span style={{ fontSize: '0.8rem', opacity: 0.85, marginRight: 4 }}>Example phrases:</span>
            <div className="sample-chip" onClick={onOpenVoice}>
              🗣️ "{activeLangConfig.sample_phrase}"
            </div>
            <div className="sample-chip" onClick={onOpenVoice}>
              🗣️ "Cash sale 300 rupees counter"
            </div>
          </div>
        </div>

        <button type="button" className="voice-btn-large" onClick={onOpenVoice}>
          <div className="mic-pulse-ring">
            <Mic size={17} color="#123B2A" />
          </div>
          <span>Record Transaction</span>
        </button>
      </div>

      {/* ── 4. QUICK ACTION BAR ────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 28, flexWrap: 'wrap' }}>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => setCurrentView('ask-ledger')}
          style={{ borderColor: 'var(--emerald-primary)', color: 'var(--emerald-primary)', background: '#F4FAF6', fontWeight: 600 }}
        >
          <HelpCircle size={16} />
          <span>Ask Your Ledger</span>
        </button>
        <button type="button" className="btn btn-secondary" onClick={onOpenCustomerModal}>
          <Plus size={16} />
          <span>Add Customer</span>
        </button>
        <button type="button" className="btn btn-secondary" onClick={onOpenExpenseModal}>
          <Tag size={16} />
          <span>Record Expense</span>
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => setCurrentView('customers')}>
          <Users size={16} />
          <span>Customer Directory ({stats?.total_customers || 0})</span>
        </button>
        <button type="button" className="btn btn-secondary" onClick={() => setCurrentView('transactions')}>
          <Receipt size={16} />
          <span>Transaction Audit History</span>
        </button>
      </div>

      {/* ── 5. ASK YOUR LEDGER INLINE FINANCIAL ASSISTANT ───────────────────── */}
      <div className="card" style={{ marginBottom: 28, border: '1px solid #DDF4E6', boxShadow: '0 4px 18px rgba(18, 59, 42, 0.04)' }}>
        <div className="card-header" style={{ paddingBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: 'var(--mint)',
              color: 'var(--emerald-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <HelpCircle size={20} />
            </div>
            <div>
              <h3 className="card-title" style={{ margin: 0, fontSize: '1.1rem' }}>Ask Your Ledger</h3>
              <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--muted-text)' }}>
                Instant deterministic answers from confirmed records &bull; Zero fabricated numbers
              </p>
            </div>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setCurrentView('ask-ledger')}
            style={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <span>Full Assistant</span>
            <ArrowRight size={13} />
          </button>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleQuickAsk();
          }}
          style={{ display: 'flex', gap: 10, marginTop: 8, flexWrap: 'wrap' }}
        >
          <div style={{ position: 'relative', flex: 1, minWidth: 260 }}>
            <div style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94A3B8' }}>
              <Search size={16} />
            </div>
            <input
              type="text"
              className="input-field"
              style={{ paddingLeft: 42, width: '100%', height: 44, fontSize: '0.92rem' }}
              placeholder="e.g. How much does Ramesh owe? / How much did I sell today?"
              value={askQuery}
              onChange={(e) => setAskQuery(e.target.value)}
              disabled={askLoading}
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ height: 44, padding: '0 22px', fontWeight: 600 }}
            disabled={askLoading || !askQuery.trim()}
          >
            {askLoading ? (
              <>
                <RefreshCw size={15} className="spin" />
                <span>Auditing...</span>
              </>
            ) : (
              <>
                <Sparkles size={15} />
                <span>Ask Ledger</span>
              </>
            )}
          </button>
        </form>

        {/* Suggestion Chips */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 12 }}>
          {[
            'How much does Ramesh owe?',
            'How much credit did I give today?',
            'Who owes me more than ₹1,000?',
            'How much cash did I collect today?',
            'What were my expenses today?',
            'How much did I sell today?',
          ].map((eq, i) => (
            <button
              key={i}
              type="button"
              onClick={() => handleQuickAsk(eq)}
              disabled={askLoading}
              style={{
                background: askQuery === eq ? 'var(--mint)' : '#F8FAF8',
                color: askQuery === eq ? 'var(--deep-forest)' : 'var(--charcoal-text)',
                border: askQuery === eq ? '1px solid var(--emerald-primary)' : '1px solid var(--border-color)',
                borderRadius: 16,
                padding: '5px 11px',
                fontSize: '0.78rem',
                cursor: 'pointer',
                fontWeight: 500,
                transition: 'all 0.15s ease'
              }}
            >
              💡 {eq}
            </button>
          ))}
        </div>

        {/* Inline Result */}
        {askError && (
          <div style={{ marginTop: 14, padding: 12, background: '#FEF2F2', border: '1px solid #FCA5A5', borderRadius: 8, fontSize: '0.85rem', color: '#991B1B' }}>
            {askError}
          </div>
        )}

        {askResult && !askLoading && (
          <div style={{
            marginTop: 14,
            padding: 16,
            background: '#F6FAF7',
            border: '1px solid #DDF4E6',
            borderRadius: 10,
            display: 'flex',
            flexDirection: 'column',
            gap: 8
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="badge badge-credit">
                INTENT: {askResult.intent.replace(/_/g, ' ').toUpperCase()}
              </span>
              {askResult.amount !== null && askResult.amount !== undefined && (
                <span style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--deep-forest)' }}>
                  ₹{Number(askResult.amount).toFixed(2)}
                </span>
              )}
            </div>
            <div style={{ fontSize: '0.94rem', color: 'var(--charcoal-text)', fontWeight: 600, lineHeight: 1.5 }}>
              {askResult.answer}
            </div>
            {askResult.details && askResult.details.length > 0 && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
                <button
                  type="button"
                  onClick={() => setCurrentView('ask-ledger')}
                  style={{ background: 'none', border: 'none', color: 'var(--emerald-primary)', fontSize: '0.82rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
                >
                  <span>View full audit breakdown ({askResult.details.length} records)</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ── 6. FINANCIAL COMPOSITION & ANALYTICS ──────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20, marginBottom: 28 }}>
        {/* Sales Breakdown */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <h3 className="card-title">Sales Composition</h3>
            <span className="badge badge-cash">₹{totalSales.toFixed(2)} Total</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.825rem', marginBottom: 5 }}>
                <span style={{ color: 'var(--muted-text)', fontWeight: 600 }}>Credit Sales (Udhar)</span>
                <span style={{ fontWeight: 700 }}>₹{stats?.total_credit_sales || '0.00'}</span>
              </div>
              <div style={{ height: 8, background: '#EEF2F0', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  background: 'var(--soft-gold)',
                  width: totalSales > 0 ? `${((Number(stats?.total_credit_sales || 0) / totalSales) * 100).toFixed(0)}%` : '0%'
                }} />
              </div>
            </div>

            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.825rem', marginBottom: 5 }}>
                <span style={{ color: 'var(--muted-text)', fontWeight: 600 }}>Counter Cash Sales</span>
                <span style={{ fontWeight: 700 }}>₹{stats?.total_cash_sales || '0.00'}</span>
              </div>
              <div style={{ height: 8, background: '#EEF2F0', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  background: 'var(--emerald-primary)',
                  width: totalSales > 0 ? `${((Number(stats?.total_cash_sales || 0) / totalSales) * 100).toFixed(0)}%` : '0%'
                }} />
              </div>
            </div>
          </div>
        </div>

        {/* Cash Inflow vs Expenses Outflow */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <h3 className="card-title">Cash Reconciliation</h3>
            <span className="badge badge-credit">Net: ₹{stats?.net_cash_movement || '0.00'}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#F4FAF6', borderRadius: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <ArrowDownLeft size={18} color="var(--emerald-primary)" />
                <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--deep-forest)' }}>Cash Received</span>
              </div>
              <span style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--deep-forest)' }}>
                +₹{stats?.total_cash_received || '0.00'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#FEF2F2', borderRadius: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <ArrowUpRight size={18} color="var(--danger-red)" />
                <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#991B1B' }}>Expenses Outflow</span>
              </div>
              <span style={{ fontSize: '1.05rem', fontWeight: 800, color: 'var(--danger-red)' }}>
                -₹{stats?.total_expenses || '0.00'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── 7. RECENT TRANSACTIONS AUDIT FEED ─────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <div>
            <h3 className="card-title">{t('recentTransactions')}</h3>
            <div style={{ fontSize: '0.78rem', color: 'var(--muted-text)' }}>
              Latest confirmed entries in your shop's immutable ledger
            </div>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setCurrentView('transactions')}
          >
            <span>View All ({transactions.length})</span>
            <ArrowRight size={13} />
          </button>
        </div>

        {transactions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 20px', color: 'var(--muted-text)' }}>
            <Receipt size={40} color="#CBD5E1" style={{ margin: '0 auto 12px' }} />
            <div style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--charcoal-text)' }}>No transactions recorded yet</div>
            <p style={{ fontSize: '0.85rem', marginTop: 4, maxWidth: 400, margin: '4px auto 16px' }}>
              Tap the microphone above or record your first transaction in any regional language!
            </p>
            <button type="button" className="btn btn-primary btn-sm" onClick={onOpenVoice}>
              <Mic size={15} />
              <span>Record First Voice Entry</span>
            </button>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Customer</th>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Source</th>
                  <th>Note / Item</th>
                </tr>
              </thead>
              <tbody>
                {transactions.slice(0, 8).map((txn) => {
                  let badgeClass = 'badge-credit';
                  let typeLabel = 'Credit Sale (Udhar)';
                  if (txn.txn_type === 'PAYMENT') {
                    badgeClass = 'badge-payment';
                    typeLabel = 'Payment Received';
                  } else if (txn.txn_type === 'CASH_SALE') {
                    badgeClass = 'badge-cash';
                    typeLabel = 'Cash Sale';
                  } else if (txn.txn_type === 'EXPENSE') {
                    badgeClass = 'badge-expense';
                    typeLabel = 'Expense';
                  }

                  const dt = new Date(txn.created_at);
                  const timeStr = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                  const dateStr = dt.toLocaleDateString([], { month: 'short', day: 'numeric' });

                  return (
                    <tr key={txn.id}>
                      <td style={{ color: 'var(--muted-text)', whiteSpace: 'nowrap' }}>
                        <div style={{ fontWeight: 600, color: 'var(--charcoal-text)' }}>{dateStr}</div>
                        <div style={{ fontSize: '0.74rem' }}>{timeStr}</div>
                      </td>
                      <td style={{ fontWeight: 700, color: 'var(--charcoal-text)' }}>
                        {txn.customer_name || '—'}
                      </td>
                      <td>
                        <span className={`badge ${badgeClass}`}>
                          {typeLabel}
                        </span>
                      </td>
                      <td style={{ fontWeight: 800, fontSize: '0.98rem', color: 'var(--charcoal-text)' }}>
                        ₹{txn.amount}
                      </td>
                      <td>
                        <span className={`badge ${txn.source === 'voice' ? 'badge-voice' : txn.source === 'demo' ? 'badge-demo' : 'badge-cash'}`}>
                          {txn.source === 'voice' ? '🎙️ Voice' : txn.source === 'demo' ? '✨ Demo' : '✍️ Manual'}
                        </span>
                      </td>
                      <td style={{ color: 'var(--muted-text)', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.84rem' }}>
                        {txn.note || '—'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
