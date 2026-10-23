import React, { useState } from 'react';
import { Sparkles, Phone, Lock, Store, User, ArrowRight, CheckCircle2, ShieldCheck } from 'lucide-react';
import { api } from '../services/api';

export default function AuthView({ onAuthSuccess, languages, selectedLang, setSelectedLang }) {
  const [mode, setMode] = useState('demo'); // 'demo' | 'login' | 'register'
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [shopName, setShopName] = useState('');
  const [ownerName, setOwnerName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleDemoLogin() {
    setLoading(true);
    setError('');
    try {
      const data = await api.demoLogin();
      onAuthSuccess(data);
    } catch (err) {
      setError(err.message || 'Demo initialization failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await api.login(phone.trim(), password);
      onAuthSuccess(data);
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await api.register({
        name: shopName.trim(),
        owner_name: ownerName.trim(),
        phone: phone.trim(),
        password: password,
        language: selectedLang,
      });
      onAuthSuccess(data);
    } catch (err) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at 10% 20%, rgba(30, 111, 204, 0.08) 0%, rgba(248, 250, 252, 1) 90%)',
      padding: '24px'
    }}>
      <div style={{
        background: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: '24px',
        maxWidth: '520px',
        width: '100%',
        padding: '36px',
        boxShadow: '0 20px 40px -15px rgba(0,0,0,0.07)'
      }}>
        {/* Header Branding */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            width: 56,
            height: 56,
            background: 'linear-gradient(135deg, #1E6FCC, #38BDF8)',
            borderRadius: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            margin: '0 auto 16px',
            boxShadow: '0 10px 25px rgba(30, 111, 204, 0.35)'
          }}>
            <Sparkles size={28} />
          </div>

          <h1 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.85rem', fontWeight: 800, color: '#0F172A', letterSpacing: '-0.02em' }}>
            BhashaFlow AI
          </h1>
          <p style={{ fontSize: '0.95rem', color: '#64748B', marginTop: 4 }}>
            Voice-Powered Digital Udhar Ledger for Indian Kirana Stores
          </p>
        </div>

        {/* Language Selection Bar */}
        <div style={{
          background: '#F8FAFC',
          border: '1px solid #E2E8F0',
          borderRadius: 12,
          padding: '10px 14px',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>
            Preferred Language:
          </span>
          <select
            className="form-select"
            style={{ width: 'auto', padding: '6px 12px', fontSize: '0.85rem' }}
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
          >
            {languages.map((l) => (
              <option key={l.code} value={l.code}>
                {l.native_name} ({l.name})
              </option>
            ))}
          </select>
        </div>

        {error && (
          <div style={{
            background: '#FEE2E2',
            color: '#991B1B',
            padding: '12px',
            borderRadius: 10,
            fontSize: '0.85rem',
            marginBottom: 20
          }}>
            {error}
          </div>
        )}

        {/* Tab Controls */}
        <div style={{ display: 'flex', background: '#F1F5F9', borderRadius: 10, padding: 4, marginBottom: 24 }}>
          <button
            type="button"
            className="btn btn-sm"
            onClick={() => setMode('demo')}
            style={{
              flex: 1,
              background: mode === 'demo' ? '#FFFFFF' : 'transparent',
              color: mode === 'demo' ? '#1E6FCC' : '#64748B',
              boxShadow: mode === 'demo' ? '0 2px 4px rgba(0,0,0,0.06)' : 'none',
              fontWeight: 700
            }}
          >
            ⚡ Quick Demo
          </button>
          <button
            type="button"
            className="btn btn-sm"
            onClick={() => setMode('login')}
            style={{
              flex: 1,
              background: mode === 'login' ? '#FFFFFF' : 'transparent',
              color: mode === 'login' ? '#0F172A' : '#64748B',
              boxShadow: mode === 'login' ? '0 2px 4px rgba(0,0,0,0.06)' : 'none',
              fontWeight: 600
            }}
          >
            Login
          </button>
          <button
            type="button"
            className="btn btn-sm"
            onClick={() => setMode('register')}
            style={{
              flex: 1,
              background: mode === 'register' ? '#FFFFFF' : 'transparent',
              color: mode === 'register' ? '#0F172A' : '#64748B',
              boxShadow: mode === 'register' ? '0 2px 4px rgba(0,0,0,0.06)' : 'none',
              fontWeight: 600
            }}
          >
            New Shop
          </button>
        </div>

        {/* ── DEMO MODE (Fastest Evaluation) ─────────────────────────────── */}
        {mode === 'demo' && (
          <div style={{ textAlign: 'center' }}>
            <div style={{
              background: '#F0FDF4',
              border: '1px solid #BBF7D0',
              borderRadius: 14,
              padding: 20,
              marginBottom: 20,
              textAlign: 'left'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: '#065F46', fontWeight: 700, fontSize: '0.9rem', marginBottom: 6 }}>
                <CheckCircle2 size={18} /> Pre-Loaded Kirana Demonstration
              </div>
              <p style={{ fontSize: '0.85rem', color: '#166534', lineHeight: 1.5 }}>
                Launches immediately with verified test data (Ramesh, Suresh, Lakshmi), pre-calculated balances, and full Gnani STT &amp; Timbre TTS capabilities.
              </p>
            </div>

            <button
              className="btn btn-primary btn-lg"
              style={{ width: '100%', borderRadius: 12, padding: '16px' }}
              onClick={handleDemoLogin}
              disabled={loading}
            >
              <Sparkles size={18} />
              <span>{loading ? 'Initializing Demo…' : 'Enter 1-Click Demo Shop'}</span>
              <ArrowRight size={18} />
            </button>
          </div>
        )}

        {/* ── LOGIN FORM ─────────────────────────────────────────────────── */}
        {mode === 'login' && (
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <input
                type="tel"
                className="form-input"
                placeholder="+919876543210"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Password</label>
              <input
                type="password"
                className="form-input"
                placeholder="••••••••"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg"
              style={{ width: '100%', marginTop: 12, borderRadius: 12 }}
              disabled={loading}
            >
              {loading ? 'Logging in…' : 'Log In to Shop'}
            </button>
          </form>
        )}

        {/* ── REGISTER FORM ──────────────────────────────────────────────── */}
        {mode === 'register' && (
          <form onSubmit={handleRegister}>
            <div className="form-group">
              <label className="form-label">Shop Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Mahalakshmi Provision Store"
                required
                value={shopName}
                onChange={(e) => setShopName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Owner Name</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. Anand Gowda"
                required
                value={ownerName}
                onChange={(e) => setOwnerName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <input
                type="tel"
                className="form-input"
                placeholder="+919876543210"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Create Password</label>
              <input
                type="password"
                className="form-input"
                placeholder="Min 6 characters"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-lg"
              style={{ width: '100%', marginTop: 12, borderRadius: 12 }}
              disabled={loading}
            >
              {loading ? 'Creating Account…' : 'Register Shop & Start'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
