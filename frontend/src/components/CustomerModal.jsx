import React, { useState } from 'react';
import { X, UserPlus, Phone, FileText } from 'lucide-react';
import { api } from '../services/api';

export default function CustomerModal({ isOpen, onClose, onCustomerCreated }) {
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!isOpen) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    setError('');
    try {
      const created = await api.createCustomer({
        name: name.trim(),
        phone: phone.trim() || null,
        notes: notes.trim() || null,
      });
      setName('');
      setPhone('');
      setNotes('');
      onCustomerCreated(created);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create customer');
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
              background: 'var(--mint)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--emerald-primary)'
            }}>
              <UserPlus size={18} />
            </div>
            <h3 className="modal-title" style={{ fontSize: '1.2rem' }}>Add New Customer</h3>
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
            <label className="form-label">Customer Name *</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Ramesh Kumar"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Phone Number (Optional)</label>
            <input
              type="tel"
              className="form-input"
              placeholder="+919876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Notes / Address (Optional)</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g. Next to bus stop, regular"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: 10, marginTop: 24, justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Adding…' : 'Save Customer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
