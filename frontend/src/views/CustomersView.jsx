import React, { useState, useEffect } from 'react';
import { Users, Search, Plus, Phone, AlertCircle, CheckCircle, ArrowRight, ArrowDownLeft, ArrowUpRight } from 'lucide-react';
import { api } from '../services/api';
import { getTranslation } from '../i18n/translations';

export default function CustomersView({ 
  currentLang, 
  onOpenCustomerModal, 
  onOpenPaymentModal 
}) {
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerTxns, setCustomerTxns] = useState([]);
  const [loading, setLoading] = useState(true);

  const t = (k) => getTranslation(currentLang, k);

  useEffect(() => {
    fetchCustomers();
  }, [search]);

  async function fetchCustomers() {
    setLoading(true);
    try {
      const data = await api.listCustomers(search);
      setCustomers(data);
      if (data.length > 0 && !selectedCustomer) {
        selectCustomer(data[0]);
      } else if (selectedCustomer) {
        // Refresh selected customer balance
        const updated = data.find((c) => c.id === selectedCustomer.id);
        if (updated) setSelectedCustomer(updated);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function selectCustomer(cust) {
    setSelectedCustomer(cust);
    try {
      const txns = await api.listTransactions({ customerId: cust.id });
      setCustomerTxns(txns);
    } catch {
      setCustomerTxns([]);
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.4rem', fontWeight: 700 }}>
            Customer Ledger Directory
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B' }}>
            Track individual customer debts, credit limits, and payment receipts.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 12 }}>
          <div style={{ position: 'relative', width: 260 }}>
            <Search size={16} color="#94A3B8" style={{ position: 'absolute', left: 12, top: 12 }} />
            <input
              type="text"
              className="form-input"
              style={{ paddingLeft: 36 }}
              placeholder="Search customers…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <button className="btn btn-primary" onClick={onOpenCustomerModal}>
            <Plus size={16} />
            <span>Add Customer</span>
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 380px) 1fr', gap: 24 }}>
        {/* Customer List */}
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--border)', background: '#F8FAFC' }}>
            <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase' }}>
              Customers ({customers.length})
            </span>
          </div>

          <div style={{ maxHeight: '680px', overflowY: 'auto' }}>
            {customers.length === 0 ? (
              <div style={{ padding: 32, textAlign: 'center', color: '#64748B' }}>
                <Users size={32} color="#CBD5E1" style={{ margin: '0 auto 8px' }} />
                <div>No customers found.</div>
              </div>
            ) : (
              customers.map((c) => {
                const isSelected = selectedCustomer?.id === c.id;
                const balance = Number(c.outstanding_balance || 0);

                return (
                  <div
                    key={c.id}
                    onClick={() => selectCustomer(c)}
                    style={{
                      padding: '16px 20px',
                      borderBottom: '1px solid var(--border-light)',
                      cursor: 'pointer',
                      background: isSelected ? '#EFF6FF' : 'transparent',
                      borderLeft: isSelected ? '4px solid #1E6FCC' : '4px solid transparent',
                      transition: 'all 0.15s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: '#0F172A', fontSize: '0.95rem' }}>
                        {c.name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748B', display: 'flex', alignItems: 'center', gap: 4, marginTop: 2 }}>
                        {c.phone ? <span>{c.phone}</span> : <span>No phone recorded</span>}
                      </div>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <div style={{
                        fontSize: '0.95rem',
                        fontWeight: 700,
                        color: balance > 0 ? '#F59E0B' : '#10B981'
                      }}>
                        ₹{balance.toFixed(2)}
                      </div>
                      <div style={{ fontSize: '0.7rem', color: '#64748B' }}>
                        {balance > 0 ? 'Due Udhar' : 'Cleared'}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Selected Customer Ledger Detail */}
        {selectedCustomer ? (
          <div>
            <div className="card" style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
                <div>
                  <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.4rem', fontWeight: 700 }}>
                    {selectedCustomer.name}
                  </h3>
                  <div style={{ display: 'flex', gap: 16, marginTop: 6, fontSize: '0.85rem', color: '#64748B' }}>
                    {selectedCustomer.phone && <span>📞 {selectedCustomer.phone}</span>}
                    <span>🗓️ Customer since {new Date(selectedCustomer.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B' }}>CURRENT BALANCE</div>
                    <div style={{
                      fontSize: '1.75rem',
                      fontWeight: 700,
                      color: Number(selectedCustomer.outstanding_balance) > 0 ? '#F59E0B' : '#10B981'
                    }}>
                      ₹{selectedCustomer.outstanding_balance}
                    </div>
                  </div>

                  <button
                    className="btn btn-success"
                    onClick={() => onOpenPaymentModal(selectedCustomer)}
                  >
                    <CheckCircle size={16} /> Record Payment
                  </button>
                </div>
              </div>
            </div>

            {/* Customer Transaction Timeline */}
            <div className="card">
              <div className="card-header">
                <h4 className="card-title">Ledger Entries for {selectedCustomer.name}</h4>
                <span style={{ fontSize: '0.8rem', color: '#64748B' }}>
                  {customerTxns.length} records
                </span>
              </div>

              {customerTxns.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '36px 20px', color: '#64748B' }}>
                  No transaction history recorded yet for this customer.
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Type</th>
                        <th>Amount</th>
                        <th>Source</th>
                        <th>Notes / Goods</th>
                      </tr>
                    </thead>
                    <tbody>
                      {customerTxns.map((txn) => {
                        const isCredit = txn.txn_type === 'CREDIT_SALE';
                        const dt = new Date(txn.created_at);

                        return (
                          <tr key={txn.id}>
                            <td style={{ color: '#64748B', whiteSpace: 'nowrap' }}>
                              {dt.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
                            </td>
                            <td>
                              <span className={`badge ${isCredit ? 'badge-credit' : 'badge-payment'}`}>
                                {isCredit ? '🔴 Credit Given' : '🟢 Payment Received'}
                              </span>
                            </td>
                            <td style={{
                              fontWeight: 700,
                              color: isCredit ? '#F59E0B' : '#10B981'
                            }}>
                              {isCredit ? `+₹${txn.amount}` : `-₹${txn.amount}`}
                            </td>
                            <td>
                              <span className={`badge ${txn.source === 'voice' ? 'badge-voice' : 'badge-cash'}`}>
                                {txn.source === 'voice' ? '🎙️ Voice' : '✍️ Manual'}
                              </span>
                            </td>
                            <td style={{ color: '#64748B' }}>
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
        ) : (
          <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 60, color: '#64748B' }}>
            Select a customer from the left list to view their ledger history.
          </div>
        )}
      </div>
    </div>
  );
}
