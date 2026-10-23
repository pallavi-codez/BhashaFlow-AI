import React, { useState, useEffect } from 'react';
import { Receipt, Search, Filter, Mic, RefreshCw, Calendar } from 'lucide-react';
import { api } from '../services/api';

export default function TransactionsView({ currentLang, onOpenVoice }) {
  const [transactions, setTransactions] = useState([]);
  const [filterType, setFilterType] = useState('ALL');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTransactions();
  }, [filterType]);

  async function fetchTransactions() {
    setLoading(true);
    try {
      const params = {};
      if (filterType !== 'ALL') {
        params.txnType = filterType;
      }
      const data = await api.listTransactions(params);
      setTransactions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const filtered = transactions.filter((t) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      (t.customer_name && t.customer_name.toLowerCase().includes(q)) ||
      (t.note && t.note.toLowerCase().includes(q)) ||
      (t.transcript && t.transcript.toLowerCase().includes(q))
    );
  });

  const totalAmount = filtered.reduce((acc, t) => acc + Number(t.amount || 0), 0);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.4rem', fontWeight: 700 }}>
            Master Ledger History
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B' }}>
            Complete immutable audit log of all transactions recorded in your shop.
          </p>
        </div>

        <button className="btn btn-primary" onClick={onOpenVoice}>
          <Mic size={16} /> Record Voice Entry
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: 16, marginBottom: 20 }}>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {['ALL', 'CREDIT_SALE', 'PAYMENT', 'CASH_SALE', 'EXPENSE'].map((type) => {
              const labels = {
                ALL: 'All Records',
                CREDIT_SALE: '🔴 Credit (Udhar)',
                PAYMENT: '🟢 Payments',
                CASH_SALE: '🔵 Cash Sales',
                EXPENSE: '🟣 Expenses',
              };
              const isSelected = filterType === type;
              return (
                <button
                  key={type}
                  className={`btn btn-sm ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setFilterType(type)}
                  style={{ borderRadius: 9999 }}
                >
                  {labels[type]}
                </button>
              );
            })}
          </div>

          <div style={{ position: 'relative', width: 240 }}>
            <Search size={16} color="#94A3B8" style={{ position: 'absolute', left: 12, top: 11 }} />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: 36, padding: '7px 12px 7px 36px', fontSize: '0.85rem' }}
              placeholder="Search note, customer…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Transactions Table */}
      <div className="card">
        <div className="card-header">
          <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#64748B' }}>
            Showing {filtered.length} entries &bull; Total Volume: ₹{totalAmount.toFixed(2)}
          </div>
          <button className="btn btn-secondary btn-sm" onClick={fetchTransactions} title="Refresh">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>

        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '50px 20px', color: '#64748B' }}>
            <Receipt size={40} color="#CBD5E1" style={{ margin: '0 auto 12px' }} />
            <div>No matching ledger records found.</div>
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
                  <th>Voice Transcript</th>
                  <th>Note</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((txn) => {
                  let badgeClass = 'badge-credit';
                  let typeLabel = 'Credit Sale';
                  if (txn.txn_type === 'PAYMENT') {
                    badgeClass = 'badge-payment';
                    typeLabel = 'Payment';
                  } else if (txn.txn_type === 'CASH_SALE') {
                    badgeClass = 'badge-cash';
                    typeLabel = 'Cash Sale';
                  } else if (txn.txn_type === 'EXPENSE') {
                    badgeClass = 'badge-expense';
                    typeLabel = 'Expense';
                  }

                  const dt = new Date(txn.created_at);

                  return (
                    <tr key={txn.id}>
                      <td style={{ color: '#64748B', whiteSpace: 'nowrap' }}>
                        <div>{dt.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}</div>
                        <div style={{ fontSize: '0.75rem', opacity: 0.8 }}>
                          {dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </td>
                      <td style={{ fontWeight: 600 }}>
                        {txn.customer_name || '—'}
                      </td>
                      <td>
                        <span className={`badge ${badgeClass}`}>{typeLabel}</span>
                      </td>
                      <td style={{ fontWeight: 700, fontSize: '1rem' }}>
                        ₹{txn.amount}
                      </td>
                      <td>
                        <span className={`badge ${txn.source === 'voice' ? 'badge-voice' : txn.source === 'demo' ? 'badge-demo' : 'badge-cash'}`}>
                          {txn.source === 'voice' ? '🎙️ Voice' : txn.source === 'demo' ? '✨ Demo' : '✍️ Manual'}
                        </span>
                      </td>
                      <td style={{ color: '#0284C7', fontStyle: txn.transcript ? 'italic' : 'normal', fontSize: '0.8rem', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {txn.transcript ? `"${txn.transcript}"` : '—'}
                      </td>
                      <td style={{ color: '#64748B', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
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
