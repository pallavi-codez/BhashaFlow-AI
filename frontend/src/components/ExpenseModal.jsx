import React, { useState } from 'react';
import { X, CreditCard, Tag } from 'lucide-react';
import { api } from '../services/api';

const CATEGORIES = [
  { id: 'supplies', label: 'Shop Supplies & Inventory' },
  { id: 'rent', label: 'Shop Rent' },
  { id: 'electricity', label: 'Electricity & Utilities' },
  { id: 'transport', label: 'Transport & Freight' },
  { id: 'tea_snacks', label: 'Tea & Staff Snacks' },
  { id: 'maintenance', label: 'Repairs & Maintenance' },
  { id: 'misc', label: 'Miscellaneous' },
];

export default function ExpenseModal({ isOpen, onClose, onExpenseCreated }) {
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('supplies');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    const val = Number(amount);
    if (!val || val <= 0) {
      setError('Please enter a valid amount.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await api.createExpense({
        amount: val,
        category: category,
        note: note.trim() || null,
      });
      setAmount('');
      setNote('');
      onExpenseCreated();
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to record expense');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: 480 }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36,
              height: 36,
              borderRadius: '50%',
              background: '#FEE2E2',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#D94B4B'
            }}>
              <CreditCard size={18} />
            </div>
            <h3 className="modal-title" style={{ fontSize: '1.2rem' }}>Record Shop Expense</h3>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {error && (
          <div style={{
            background: '#FEE2E2',
            color: '#991B1B',
            padding: '10px 14px',
            borderRadius: 8,
            fontSize: '0.85rem',
            marginBottom: 16
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Expense Amount (₹) *</label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              className="form-input"
              placeholder="0.00"
              required
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Category</label>
            <select
              className="form-select"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              {CATEGORIES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Notes / Merchant</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Packing bags, wholesale invoice"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-danger" disabled={loading}>
              {loading ? 'Recording…' : 'Save Expense'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
