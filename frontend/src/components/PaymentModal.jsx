import React, { useState, useEffect } from 'react';
import { X, CheckCircle, AlertCircle, IndianRupee } from 'lucide-react';
import { api } from '../services/api';

export default function PaymentModal({ isOpen, onClose, customer, onPaymentRecorded }) {
  const [amount, setAmount] = useState('');
  const [note, setNote] = useState('');
  const [confirmOverpayment, setConfirmOverpayment] = useState(false);
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
    setConfirmOverpayment(false);
  }, [customer, isOpen]);

  if (!isOpen || !customer) return null;

  const outstanding = Number(customer.outstanding_balance || 0);
  const payAmt = Number(amount || 0);
  const isOverpayment = payAmt > outstanding;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!payAmt || payAmt <= 0) {
      setError('Please enter a valid payment amount greater than zero.');
      return;
    }

    if (isOverpayment && !confirmOverpayment) {
      setError(
        `Payment of ₹${payAmt.toFixed(2)} exceeds current debt ₹${outstanding.toFixed(2)}. Please check the explicit confirmation box below to proceed.`
      );
      return;
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
        allow_overpayment: isOverpayment && confirmOverpayment,
      });

      await api.confirmTransaction(pending.id, idempotencyKey);
      onPaymentRecorded();
      onClose();
    } catch (err) {
      if (err.isOverpayment) {
        setError(
          `Payment of ₹${payAmt.toFixed(2)} exceeds outstanding balance of ₹${err.outstanding}. Check the box to confirm overpayment.`
        );
      } else {
        setError(err.message || 'Payment recording failed');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: 480 }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: '50%',
                background: 'var(--mint)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--emerald-primary)',
              }}
            >
              <CheckCircle size={20} />
            </div>
            <div>
              <h3 className="modal-title" style={{ fontSize: '1.2rem' }}>
                Record Debt Payment
              </h3>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Customer: <strong>{customer.name}</strong>
              </div>
            </div>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        {/* Balance Card */}
        <div
          style={{
            background: 'var(--bg-app)',
            border: '1px solid var(--border)',
            borderRadius: 12,
            padding: '14px',
            marginBottom: 18,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              CURRENT OUTSTANDING DEBT
            </div>
            <div
              style={{
                fontSize: '1.4rem',
                fontWeight: 700,
                color: outstanding > 0 ? 'var(--warning)' : 'var(--primary)',
              }}
            >
              ₹{outstanding.toFixed(2)}
            </div>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => {
              setAmount(String(outstanding > 0 ? outstanding : 0));
              setConfirmOverpayment(false);
            }}
          >
            Clear Full Balance
          </button>
        </div>

        {error && (
          <div
            style={{
              background: '#FEE2E2',
              color: '#991B1B',
              padding: '10px 14px',
              borderRadius: 8,
              fontSize: '0.85rem',
              marginBottom: 16,
              border: '1px solid #FCA5A5',
            }}
          >
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
              onChange={(e) => {
                setAmount(e.target.value);
                if (Number(e.target.value || 0) <= outstanding) {
                  setConfirmOverpayment(false);
                }
              }}
            />
          </div>

          {/* Overpayment Explicit Confirmation Banner */}
          {isOverpayment && (
            <div
              style={{
                background: '#FEF3C7',
                border: '1px solid #FCD34D',
                color: '#92400E',
                padding: '12px 14px',
                borderRadius: 10,
                marginBottom: 16,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontWeight: 700,
                  fontSize: '0.85rem',
                  marginBottom: 4,
                }}
              >
                <AlertCircle size={16} style={{ flexShrink: 0 }} />
                <span>Overpayment / Advance Payment Notice</span>
              </div>
              <div style={{ fontSize: '0.8rem', lineHeight: 1.45, marginBottom: 10 }}>
                Entered amount (₹{payAmt.toFixed(2)}) exceeds current outstanding debt of ₹{outstanding.toFixed(2)}. This
                will create an advance balance of ₹{(payAmt - outstanding).toFixed(2)}.
              </div>
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontSize: '0.825rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                <input
                  type="checkbox"
                  id="confirm-overpayment-checkbox"
                  checked={confirmOverpayment}
                  onChange={(e) => setConfirmOverpayment(e.target.checked)}
                />
                <span>Yes, I explicitly confirm recording this overpayment</span>
              </label>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Note / Payment Method</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Cash, UPI, Google Pay, PhonePe"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-success"
              disabled={loading || (isOverpayment && !confirmOverpayment)}
            >
              {loading ? 'Recording…' : 'Save Payment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
