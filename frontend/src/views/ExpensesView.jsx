import React, { useState, useEffect } from 'react';
import { CreditCard, Plus, Trash2, Tag, Calendar, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export default function ExpensesView({ onOpenExpenseModal }) {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchExpenses();
  }, []);

  async function fetchExpenses() {
    setLoading(true);
    try {
      const data = await api.listExpenses();
      setExpenses(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id) {
    if (!window.confirm('Delete this expense record?')) return;
    try {
      await api.deleteExpense(id);
      fetchExpenses();
    } catch (err) {
      alert(err.message || 'Failed to delete expense');
    }
  }

  const totalExpenseAmount = expenses.reduce((acc, e) => acc + Number(e.amount || 0), 0);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.4rem', fontWeight: 700 }}>
            Shop Expense Tracker
          </h2>
          <p style={{ fontSize: '0.875rem', color: '#64748B' }}>
            Record shop overheads, stock purchases, and operational outlays.
          </p>
        </div>

        <button className="btn btn-primary" onClick={onOpenExpenseModal}>
          <Plus size={16} /> Record Expense
        </button>
      </div>

      {/* Summary Card */}
      <div className="card" style={{ background: 'linear-gradient(135deg, #FEF2F2 0%, #FFFFFF 100%)', borderColor: '#FECACA' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#991B1B', textTransform: 'uppercase' }}>
              TOTAL RECORDED EXPENSES
            </div>
            <div style={{ fontFamily: 'Outfit, sans-serif', fontSize: '2rem', fontWeight: 800, color: '#DC2626', marginTop: 4 }}>
              ₹{totalExpenseAmount.toFixed(2)}
            </div>
          </div>

          <div style={{ fontSize: '0.85rem', color: '#64748B', maxWidth: 440 }}>
            Expenses decrease net cash movement in your shop calculations. They are kept strictly separate from sales to ensure true financial integrity.
          </div>
        </div>
      </div>

      {/* Expenses List */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">Expense History ({expenses.length})</h3>
        </div>

        {expenses.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '50px 20px', color: '#64748B' }}>
            <CreditCard size={40} color="#CBD5E1" style={{ margin: '0 auto 12px' }} />
            <div>No expenses recorded yet.</div>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Category</th>
                  <th>Amount</th>
                  <th>Notes</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {expenses.map((e) => {
                  const dt = new Date(e.created_at);
                  return (
                    <tr key={e.id}>
                      <td style={{ color: '#64748B', whiteSpace: 'nowrap' }}>
                        {dt.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td>
                        <span className="badge badge-expense" style={{ textTransform: 'capitalize' }}>
                          <Tag size={12} /> {e.category || 'Supplies'}
                        </span>
                      </td>
                      <td style={{ fontWeight: 700, fontSize: '1rem', color: '#DC2626' }}>
                        ₹{e.amount}
                      </td>
                      <td style={{ color: '#64748B' }}>
                        {e.note || '—'}
                      </td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '6px', color: '#EF4444', borderColor: 'transparent' }}
                          onClick={() => handleDelete(e.id)}
                          title="Delete expense"
                        >
                          <Trash2 size={16} />
                        </button>
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
