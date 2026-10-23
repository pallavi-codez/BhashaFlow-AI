import React from 'react';
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
  Users, 
  Receipt,
  AlertCircle
} from 'lucide-react';
import { getTranslation } from '../i18n/translations';

export default function DashboardView({ 
  stats, 
  transactions, 
  currentLang, 
  languages,
  onOpenVoice,
  onOpenCustomerModal,
  onOpenExpenseModal,
  setCurrentView
}) {
  const t = (k) => getTranslation(currentLang, k);

  const activeLangConfig = languages.find((l) => l.code === currentLang) || {
    sample_phrase: 'Ramesh ge 500 rupees udhar haaku',
    name: 'Kannada',
  };

  const totalSales = Number(stats?.total_credit_sales || 0) + Number(stats?.total_cash_sales || 0);

  return (
    <div>
      {/* ── Metric Cards ─────────────────────────────────────────────────── */}
      <div className="metrics-grid">
        {/* Total Outstanding Customer Udhar */}
        <div className="metric-card metric-debt">
          <div className="metric-header">
            <span className="metric-label">{t('outstandingDebt')}</span>
            <div className="metric-icon-box">
              <AlertCircle size={22} />
            </div>
          </div>
          <div className="metric-value">
            ₹{stats?.total_outstanding !== undefined ? stats.total_outstanding : '0.00'}
          </div>
          <div className="metric-footer">
            <span>Derived strictly from confirmed ledger entries</span>
          </div>
        </div>

        {/* Today's Cash Collected */}
        <div className="metric-card metric-cash">
          <div className="metric-header">
            <span className="metric-label">{t('cashInHand')}</span>
            <div className="metric-icon-box">
              <Wallet size={22} />
            </div>
          </div>
          <div className="metric-value">
            ₹{stats?.total_cash_received !== undefined ? stats.total_cash_received : '0.00'}
          </div>
          <div className="metric-footer">
            <span>Cash Sales (₹{stats?.total_cash_sales || 0}) + Debt Paid (₹{stats?.total_payments_received || 0})</span>
          </div>
        </div>

        {/* Today's Total Sales */}
        <div className="metric-card metric-sales">
          <div className="metric-header">
            <span className="metric-label">{t('todaySales')}</span>
            <div className="metric-icon-box">
              <TrendingUp size={22} />
            </div>
          </div>
          <div className="metric-value">
            ₹{totalSales.toFixed(2)}
          </div>
          <div className="metric-footer">
            <span>Credit Sales (₹{stats?.total_credit_sales || 0}) + Cash Sales (₹{stats?.total_cash_sales || 0})</span>
          </div>
        </div>

        {/* Today's Expenses */}
        <div className="metric-card metric-expense">
          <div className="metric-header">
            <span className="metric-label">{t('todayExpenses')}</span>
            <div className="metric-icon-box">
              <CreditCard size={22} />
            </div>
          </div>
          <div className="metric-value">
            ₹{stats?.total_expenses !== undefined ? stats.total_expenses : '0.00'}
          </div>
          <div className="metric-footer">
            <span>Net cash movement: ₹{stats?.net_cash_movement || 0}</span>
          </div>
        </div>
      </div>

      {/* ── Voice Action Banner ───────────────────────────────────────────── */}
      <div className="voice-banner">
        <div className="voice-banner-content">
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'rgba(255,255,255,0.2)', padding: '3px 10px', borderRadius: 9999, fontSize: '0.75rem', fontWeight: 700, marginBottom: 10 }}>
            <Mic size={13} /> VOICE-FIRST UDHAR ENTRY
          </div>
          <h2 className="voice-banner-title">{t('quickVoiceTitle')}</h2>
          <p className="voice-banner-subtitle">{t('quickVoiceSub')}</p>

          <div className="voice-banner-examples">
            <span style={{ fontSize: '0.8rem', opacity: 0.85, marginRight: 4 }}>Try speaking:</span>
            <div className="sample-chip" onClick={onOpenVoice}>
              🗣️ "{activeLangConfig.sample_phrase}"
            </div>
            <div className="sample-chip" onClick={onOpenVoice}>
              🗣️ "Ramesh paid 200 rupees"
            </div>
            <div className="sample-chip" onClick={onOpenVoice}>
              🗣️ "Cash sale 300 rupees"
            </div>
          </div>
        </div>

        <button className="voice-btn-large" onClick={onOpenVoice}>
          <div className="mic-pulse-ring">
            <Mic size={18} />
          </div>
          <span>{t('recordTransaction')}</span>
        </button>
      </div>

      {/* ── Quick Action Bar ──────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 28, flexWrap: 'wrap' }}>
        <button className="btn btn-secondary" onClick={onOpenCustomerModal}>
          <Plus size={16} />
          <span>{t('addCustomer')}</span>
        </button>
        <button className="btn btn-secondary" onClick={onOpenExpenseModal}>
          <CreditCard size={16} />
          <span>{t('recordExpense')}</span>
        </button>
        <button className="btn btn-secondary" onClick={() => setCurrentView('customers')}>
          <Users size={16} />
          <span>{t('allCustomers')} ({stats?.total_customers || 0})</span>
        </button>
        <button className="btn btn-secondary" onClick={() => setCurrentView('transactions')}>
          <Receipt size={16} />
          <span>View All Transactions</span>
        </button>
      </div>

      {/* ── Financial Breakdown & Analytics ──────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20, marginBottom: 28 }}>
        {/* Sales Composition */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <h3 className="card-title">Today's Sales Breakdown</h3>
            <span className="badge badge-cash">₹{totalSales.toFixed(2)} Total</span>
          </div>

          <div style={{ display: 'flex', gap: 14, alignItems: 'center', marginBottom: 16 }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 6 }}>
                <span style={{ color: '#F59E0B', fontWeight: 600 }}>Credit Sales (Udhar)</span>
                <span style={{ fontWeight: 700 }}>₹{stats?.total_credit_sales || '0.00'}</span>
              </div>
              <div style={{ height: 8, background: '#E2E8F0', borderRadius: 9999, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  background: '#F59E0B',
                  width: `${totalSales > 0 ? (Number(stats?.total_credit_sales || 0) / totalSales) * 100 : 50}%`,
                  borderRadius: 9999
                }} />
              </div>
            </div>

            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: 6 }}>
                <span style={{ color: '#0284C7', fontWeight: 600 }}>Cash Sales</span>
                <span style={{ fontWeight: 700 }}>₹{stats?.total_cash_sales || '0.00'}</span>
              </div>
              <div style={{ height: 8, background: '#E2E8F0', borderRadius: 9999, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  background: '#0284C7',
                  width: `${totalSales > 0 ? (Number(stats?.total_cash_sales || 0) / totalSales) * 100 : 50}%`,
                  borderRadius: 9999
                }} />
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.75rem', color: '#64748B', background: '#F8FAFC', padding: '10px 14px', borderRadius: 8 }}>
            💡 <strong>Financial Rule:</strong> Udhar sales increase customer debt but do NOT add to cash collected. Payments against previous debt add to cash received but do NOT count as new sales.
          </div>
        </div>

        {/* Cash In vs Expenses */}
        <div className="card" style={{ marginBottom: 0 }}>
          <div className="card-header">
            <h3 className="card-title">Cash Movement Summary</h3>
            <span className="badge badge-payment">Net: ₹{stats?.net_cash_movement || '0.00'}</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#ECFDF5', borderRadius: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <ArrowDownLeft size={18} color="#10B981" />
                <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#065F46' }}>Total Cash Received</span>
              </div>
              <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#065F46' }}>
                +₹{stats?.total_cash_received || '0.00'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', background: '#FEE2E2', borderRadius: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <ArrowUpRight size={18} color="#EF4444" />
                <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#991B1B' }}>Shop Expenses Paid</span>
              </div>
              <span style={{ fontSize: '1.05rem', fontWeight: 700, color: '#991B1B' }}>
                -₹{stats?.total_expenses || '0.00'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Recent Transactions Table ────────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">{t('recentTransactions')}</h3>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => setCurrentView('transactions')}
          >
            View All ({transactions.length})
          </button>
        </div>

        {transactions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748B' }}>
            <Receipt size={36} color="#CBD5E1" style={{ margin: '0 auto 12px' }} />
            <div style={{ fontSize: '0.95rem', fontWeight: 500 }}>{t('noTransactions')}</div>
            <p style={{ fontSize: '0.8rem', marginTop: 4 }}>
              Tap the microphone above or use a sample command to record your first ledger entry!
            </p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date &amp; Time</th>
                  <th>Customer</th>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Source</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {transactions.slice(0, 7).map((txn) => {
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
                      <td style={{ color: '#64748B', whiteSpace: 'nowrap' }}>
                        <div>{dateStr}</div>
                        <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>{timeStr}</div>
                      </td>
                      <td style={{ fontWeight: 600 }}>
                        {txn.customer_name || '—'}
                      </td>
                      <td>
                        <span className={`badge ${badgeClass}`}>
                          {typeLabel}
                        </span>
                      </td>
                      <td style={{ fontWeight: 700, fontSize: '1rem' }}>
                        ₹{txn.amount}
                      </td>
                      <td>
                        <span className={`badge ${txn.source === 'voice' ? 'badge-voice' : txn.source === 'demo' ? 'badge-demo' : 'badge-cash'}`}>
                          {txn.source === 'voice' ? '🎙️ Voice' : txn.source === 'demo' ? '✨ Demo' : '✍️ Manual'}
                        </span>
                      </td>
                      <td style={{ color: '#64748B', maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
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
