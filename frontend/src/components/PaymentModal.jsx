import React, { useState, useEffect } from 'react';
import { X, CheckCircle, AlertCircle, IndianRupee } from 'lucide-react';
import { api } from '../services/api';

export default function PaymentModal({ isOpen, onClose, customer, onPaymentRecorded }) {
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (customer && customer.outstanding_balance > 0) {
      setAmount(String(customer.outstanding_balance));
    } else {
      setAmount('');
    }
    setNote('');
    setError('');
  }, [customer, isOpen]);

  if (!isOpen || !customer) return null;

  const outstanding = Number(customer.outstanding_balance || 0);
  const payAmt = Number(amount || 0);
  const isOverpayment = payAmt > outstanding;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!payAmt || payAmt <= 0) {
      setError('Please enter a valid amount.');
      return;
    }

    if (isOverpayment) {
      const proceed = window.confirm(
        `Payment of ₹${payAmt} exceeds current outstanding debt of ₹${outstanding}. Record payment anyway?`
      );
      if (!proceed) return;
    }

    setLoading(true);
    setError('');
    try {
      const idempotencyKey = `pay_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
      const pending = await api.createPendingTransaction({
        customer_id: customer.id,
        txn_type: 'PAYMENT',
        amount: payAmt,
        note: note.trim() || 'Debt payment',
        source: 'manual',
        idempotency_key: idempotencyKey,
      });

      await api.confirmTransaction(pending.id, idempotencyKey);
      onPaymentRecorded();
      onClose();
    } catch (err) {
      setError(err.message || 'Payment recording failed');
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
              background: '#ECFDF5',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#10B981'
            }}>
              <CheckCircle size={20} />
            </div>
            <div>
              <h3 className="modal-title" style={{ fontSize: '1.2rem' }}>Record Debt Payment</h3>
              <div style={{ fontSize: '0.8rem', color: '#64748B' }}>
                Customer: <strong>{customer.name}</strong>
              </div>
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Balance Card */}
        <div style={{
          background: '#F8FAFC',
          border: '1px solid #E2E8F0',
          borderRadius: 12,
          padding: '14px',
          marginBottom: 18,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B' }}>CURRENT OUTSTANDING DEBT</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: '#F59E0B' }}>
              ₹{customer.outstanding_balance}
            </div>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setAmount(String(customer.outstanding_balance))}
          >
            Clear Full Balance
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
            <label className="form-label">Payment Amount Received (₹) *</label>
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

          {isOverpayment && (
            <div style={{
              background: '#FEF3C7',
              color: '#92400E',
              padding: '8px 12px',
              borderRadius: 8,
              fontSize: '0.8rem',
              marginBottom: 14,
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}>
              <AlertCircle size={16} flexShrink={0} />
              <span>Amount exceeds outstanding balance (₹{outstanding}).</span>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Note / Payment Method</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Cash, UPI, Google Pay"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-success" disabled={loading}>
              {loading ? 'Recording…' : 'Save Payment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
