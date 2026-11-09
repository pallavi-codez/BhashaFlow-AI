import React, { useState, useEffect } from 'react';
import {
  Mic,
  ShieldCheck,
  CheckCircle2,
  Zap,
  Globe,
  ArrowRight,
  Eye,
  EyeOff,
  AlertCircle,
  Sparkles,
  Lock,
  ArrowLeft,
  Store,
  User,
  Phone,
  KeyRound,
  Check
} from 'lucide-react';
import { api } from '../services/api';

const PALETTE = {
  deepForest: '#123B2A',
  emerald: '#16865A',
  emeraldHover: '#116B46',
  mint: '#DDF4E6',
  warmIvory: '#FAF9F4',
  white: '#FFFFFF',
  charcoal: '#202923',
  muted: '#65756B',
  border: '#E3EAE3',
  softGold: '#E9B949',
  danger: '#D94B4B',
  errorBg: '#FEE2E2',
};

const FEATURES = [
  {
    icon: <Mic size={18} color="#FFFFFF" />,
    title: 'Voice-First AI Ledger',
    desc: 'Speak naturally in 13 Indian languages to record customer credit and debt collections instantly.',
  },
  {
    icon: <ShieldCheck size={18} color="#FFFFFF" />,
    title: 'Multi-Tenant Shop Isolation',
    desc: 'Your ledger, customers, and accounts are private, encrypted, and isolated strictly to your store.',
  },
  {
    icon: <Zap size={18} color="#FFFFFF" />,
    title: 'Instant Udhar & Cash Reconciliation',
    desc: 'Track daily credit sales, cash in hand, debt collections, and shop expenses in real time.',
  },
  {
    icon: <CheckCircle2 size={18} color="#FFFFFF" />,
    title: 'Decimal-Safe Accounting',
    desc: 'Exact ledger balance computation with zero floating-point errors and overpayment guardrails.',
  },
];

const POPULAR_LANGUAGES = [
  'ಕನ್ನಡ (Kannada)',
  'हिन्दी (Hindi)',
  'English',
  'தமிழ் (Tamil)',
  'తెలుగు (Telugu)',
  'मराठी (Marathi)',
  'اردو (Urdu)',
  'বাংলা (Bengali)',
];

export default function AuthView({
  onAuthSuccess,
  languages = [],
  selectedLang = 'en-IN',
  setSelectedLang,
  initialMode = 'login',
  onBackToHome
}) {
  const [mode, setMode] = useState(initialMode); // 'login' | 'register'
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [shopName, setShopName] = useState('');
  const [ownerName, setOwnerName] = useState('');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setMode(initialMode);
  }, [initialMode]);

  async function handleDemoLogin() {
    setLoading(true);
    setError('');
    try {
      const data = await api.demoLogin();
      onAuthSuccess(data);
    } catch (err) {
      setError(err.message || 'Demo store initialization failed. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    if (!phone.trim() || !password) {
      setError('Please provide both your registered shop phone number and password.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await api.login(phone.trim(), password);
      onAuthSuccess(data);
    } catch (err) {
      setError(err.message || 'Invalid phone or password. Please verify your credentials.');
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e) {
    e.preventDefault();
    if (!shopName.trim() || !ownerName.trim() || !phone.trim() || !password) {
      setError('Please fill in all required store details.');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const data = await api.register({
        name: shopName.trim(),
        owner_name: ownerName.trim(),
        phone: phone.trim(),
        password: password,
        language: selectedLang || 'en-IN',
      });
      onAuthSuccess(data);
    } catch (err) {
      setError(err.message || 'Registration failed. This phone number may already be registered.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-root" style={{ minHeight: '100vh', display: 'flex', background: PALETTE.warmIvory }}>
      {/* ─── LEFT BRAND SHOWCASE PANEL (Desktop) ─────────────────────────── */}
      <div
        className="auth-showcase-panel"
        style={{
          flex: '0 0 46%',
          background: `linear-gradient(155deg, ${PALETTE.deepForest} 0%, #154532 50%, #1C5A41 100%)`,
          padding: '48px 52px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          position: 'relative',
          overflow: 'hidden',
          color: '#FFFFFF'
        }}
      >
        {/* Subtle mesh circle */}
        <div
          style={{
            position: 'absolute',
            top: '-15%',
            right: '-15%',
            width: 480,
            height: 480,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(22, 134, 90, 0.25) 0%, transparent 70%)',
            pointerEvents: 'none',
          }}
        />

        {/* Top Branding */}
        <div style={{ position: 'relative', zIndex: 2 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28 }}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                background: 'rgba(255, 255, 255, 0.15)',
                backdropFilter: 'blur(8px)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid rgba(255, 255, 255, 0.2)',
              }}
            >
              <Sparkles size={22} color="#FFFFFF" />
            </div>
            <div>
              <div style={{ fontFamily: "'Outfit', sans-serif", fontSize: '1.45rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                BhashaFlow <span style={{ color: PALETTE.softGold }}>AI</span>
              </div>
              <div style={{ fontSize: '0.72rem', color: PALETTE.mint, fontWeight: 700, letterSpacing: '0.06em' }}>
                VOICE FINTECH &bull; GNANI AI POWERED
              </div>
            </div>
          </div>

          <h2
            style={{
              fontFamily: "'Outfit', sans-serif",
              fontSize: '2.1rem',
              fontWeight: 800,
              lineHeight: 1.25,
              color: '#FFFFFF',
              marginBottom: 16,
            }}
          >
            Your Business.<br />
            Your Language.<br />
            <span style={{ color: PALETTE.softGold }}>Your Ledger.</span>
          </h2>

          <p
            style={{
              fontSize: '0.98rem',
              color: 'rgba(255, 255, 255, 0.85)',
              lineHeight: 1.6,
              maxWidth: 440,
              marginBottom: 36,
            }}
          >
            Record customer udhar, cash sales, and debt settlements by speaking naturally in your regional language.
            Built specifically for India's retail merchants.
          </p>

          {/* Features list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18, marginBottom: 36 }}>
            {FEATURES.map((item, idx) => (
              <div key={idx} style={{ display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                <div
                  style={{
                    width: 34,
                    height: 34,
                    borderRadius: 10,
                    background: 'rgba(255, 255, 255, 0.12)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: 2,
                  }}
                >
                  {item.icon}
                </div>
                <div>
                  <div style={{ fontSize: '0.92rem', fontWeight: 700, color: '#FFFFFF', marginBottom: 2 }}>
                    {item.title}
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'rgba(255, 255, 255, 0.72)', lineHeight: 1.45 }}>
                    {item.desc}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Supported language pills footer */}
        <div style={{ marginTop: 24, paddingTop: 20, borderTop: '1px solid rgba(255, 255, 255, 0.12)' }}>
          <div
            style={{
              fontSize: '0.72rem',
              fontWeight: 600,
              textTransform: 'uppercase',
              color: 'rgba(255, 255, 255, 0.65)',
              letterSpacing: '0.05em',
              marginBottom: 10,
            }}
          >
            Powered by Gnani AI Voice Engines &bull; 13 Indian Languages
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {POPULAR_LANGUAGES.map((lang, i) => (
              <span
                key={i}
                style={{
                  fontSize: '0.74rem',
                  padding: '3px 10px',
                  background: 'rgba(255, 255, 255, 0.1)',
                  borderRadius: 20,
                  color: 'rgba(255, 255, 255, 0.9)',
                }}
              >
                {lang}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* ─── RIGHT INTERACTIVE AUTH FORM PANEL ───────────────────────────── */}
      <div
        className="auth-form-panel"
        style={{
          flex: '1',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '40px 24px',
          background: PALETTE.warmIvory,
          minHeight: '100vh',
          boxSizing: 'border-box',
          overflowY: 'auto'
        }}
      >
        {/* Top Back-To-Home and Mobile Header */}
        <div style={{ width: '100%', maxWidth: 460, marginBottom: 18, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          {onBackToHome && (
            <button
              type="button"
              onClick={onBackToHome}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                background: 'none',
                border: 'none',
                color: PALETTE.muted,
                fontSize: '0.875rem',
                fontWeight: 600,
                cursor: 'pointer',
                padding: '6px 0',
                transition: 'color 0.15s ease',
              }}
              onMouseOver={(e) => (e.currentTarget.style.color = PALETTE.emerald)}
              onMouseOut={(e) => (e.currentTarget.style.color = PALETTE.muted)}
            >
              <ArrowLeft size={16} />
              <span>Back to Home</span>
            </button>
          )}

          {/* Quick Demo Store Pill */}
          <button
            type="button"
            onClick={handleDemoLogin}
            disabled={loading}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              background: PALETTE.mint,
              border: `1px solid rgba(22, 134, 90, 0.3)`,
              color: PALETTE.emerald,
              borderRadius: 20,
              padding: '5px 12px',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            <Zap size={13} color="#E9B949" />
            <span>Try Demo</span>
          </button>
        </div>

        {/* Card Box */}
        <div
          style={{
            width: '100%',
            maxWidth: 460,
            background: PALETTE.white,
            border: `1px solid ${PALETTE.border}`,
            borderRadius: 20,
            padding: '36px 36px 32px',
            boxShadow: '0 8px 30px rgba(18, 59, 42, 0.06), 0 1px 3px rgba(0, 0, 0, 0.04)',
          }}
        >
          {/* Sign In vs Register Tabs */}
          <div
            style={{
              display: 'flex',
              background: '#F1F5F2',
              borderRadius: 12,
              padding: 4,
              marginBottom: 24,
              gap: 4,
            }}
          >
            <button
              type="button"
              id="auth-tab-login"
              onClick={() => {
                setMode('login');
                setError('');
              }}
              style={{
                flex: 1,
                padding: '10px 14px',
                borderRadius: 9,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: mode === 'login' ? 700 : 500,
                color: mode === 'login' ? PALETTE.emerald : PALETTE.muted,
                background: mode === 'login' ? PALETTE.white : 'transparent',
                boxShadow: mode === 'login' ? '0 2px 6px rgba(18, 59, 42, 0.08)' : 'none',
                transition: 'all 0.2s ease',
                fontFamily: 'inherit',
              }}
            >
              Sign In
            </button>
            <button
              type="button"
              id="auth-tab-register"
              onClick={() => {
                setMode('register');
                setError('');
              }}
              style={{
                flex: 1,
                padding: '10px 14px',
                borderRadius: 9,
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.9rem',
                fontWeight: mode === 'register' ? 700 : 500,
                color: mode === 'register' ? PALETTE.emerald : PALETTE.muted,
                background: mode === 'register' ? PALETTE.white : 'transparent',
                boxShadow: mode === 'register' ? '0 2px 6px rgba(18, 59, 42, 0.08)' : 'none',
                transition: 'all 0.2s ease',
                fontFamily: 'inherit',
              }}
            >
              Register Shop
            </button>
          </div>

          {/* Primary Language Selector Pill */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              background: '#F8FAF8',
              border: `1px solid ${PALETTE.border}`,
              borderRadius: 10,
              padding: '8px 14px',
              marginBottom: 20,
            }}
          >
            <Globe size={16} color={PALETTE.emerald} style={{ flexShrink: 0 }} />
            <span style={{ fontSize: '0.82rem', fontWeight: 600, color: PALETTE.charcoal, flexShrink: 0 }}>
              Primary Language:
            </span>
            <select
              id="auth-language-select"
              value={selectedLang}
              onChange={(e) => setSelectedLang && setSelectedLang(e.target.value)}
              style={{
                flex: 1,
                border: 'none',
                background: 'transparent',
                fontSize: '0.85rem',
                color: PALETTE.emerald,
                fontWeight: 600,
                outline: 'none',
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              {languages.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.native_name} ({l.name})
                </option>
              ))}
            </select>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              id="auth-error-banner"
              style={{
                background: PALETTE.errorBg,
                color: PALETTE.danger,
                padding: '12px 14px',
                borderRadius: 10,
                fontSize: '0.85rem',
                marginBottom: 20,
                display: 'flex',
                alignItems: 'flex-start',
                gap: 10,
                lineHeight: 1.45,
                border: '1px solid #FCA5A5',
              }}
            >
              <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 1 }} />
              <span>{error}</span>
            </div>
          )}

          {/* ── SIGN IN FORM ────────────────────────────────────────── */}
          {mode === 'login' && (
            <form onSubmit={handleLogin} noValidate>
              <div style={{ marginBottom: 18 }}>
                <label
                  htmlFor="login-phone"
                  style={{
                    display: 'block',
                    fontSize: '0.825rem',
                    fontWeight: 600,
                    color: PALETTE.charcoal,
                    marginBottom: 6,
                  }}
                >
                  Shop Phone Number
                </label>
                <div style={{ position: 'relative' }}>
                  <div style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94A3B8' }}>
                    <Phone size={16} />
                  </div>
                  <input
                    id="login-phone"
                    type="tel"
                    placeholder="+91 98765 43210"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="input-field"
                    style={{ paddingLeft: 40, width: '100%', height: 46 }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: 24 }}>
                <label
                  htmlFor="login-password"
                  style={{
                    display: 'block',
                    fontSize: '0.825rem',
                    fontWeight: 600,
                    color: PALETTE.charcoal,
                    marginBottom: 6,
                  }}
                >
                  Password
                </label>
                <div style={{ position: 'relative' }}>
                  <div style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94A3B8' }}>
                    <KeyRound size={16} />
                  </div>
                  <input
                    id="login-password"
                    type={showPass ? 'text' : 'password'}
                    placeholder="Enter shop password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input-field"
                    style={{ paddingLeft: 40, paddingRight: 44, width: '100%', height: 46 }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass((s) => !s)}
                    aria-label={showPass ? 'Hide password' : 'Show password'}
                    style={{
                      position: 'absolute',
                      right: 12,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      color: PALETTE.muted,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      padding: 4,
                    }}
                  >
                    {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                id="login-submit-button"
                disabled={loading}
                className="btn btn-primary btn-lg"
                style={{ width: '100%', height: 48, borderRadius: 10, fontSize: '0.96rem' }}
              >
                {loading ? 'Authenticating…' : 'Sign In to Store'}
                {!loading && <ArrowRight size={17} />}
              </button>
            </form>
          )}

          {/* ── REGISTER FORM ───────────────────────────────────────── */}
          {mode === 'register' && (
            <form onSubmit={handleRegister} noValidate>
              <div style={{ marginBottom: 14 }}>
                <label
                  htmlFor="reg-shop-name"
                  style={{
                    display: 'block',
                    fontSize: '0.825rem',
                    fontWeight: 600,
                    color: PALETTE.charcoal,
                    marginBottom: 6,
                  }}
                >
                  Shop / Store Name
                </label>
                <div style={{ position: 'relative' }}>
                  <div style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94A3B8' }}>
                    <Store size={16} />
                  </div>
                  <input
                    id="reg-shop-name"
                    type="text"
                    placeholder="Sri Lakshmi Provision Store"
                    required
                    value={shopName}
                    onChange={(e) => setShopName(e.target.value)}
                    className="input-field"
                    style={{ paddingLeft: 40, width: '100%', height: 44 }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: 14 }}>
                <label
                  htmlFor="reg-owner-name"
                  style={{
                    display: 'block',
                    fontSize: '0.825rem',
                    fontWeight: 600,
                    color: PALETTE.charcoal,
                    marginBottom: 6,
                  }}
                >
                  Owner / Merchant Name
                </label>
                <div style={{ position: 'relative' }}>
                  <div style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94A3B8' }}>
                    <User size={16} />
                  </div>
                  <input
                    id="reg-owner-name"
                    type="text"
                    placeholder="Ramesh Kumar"
                    required
                    value={ownerName}
                    onChange={(e) => setOwnerName(e.target.value)}
                    className="input-field"
                    style={{ paddingLeft: 40, width: '100%', height: 44 }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: 14 }}>
                <label
                  htmlFor="reg-phone"
                  style={{
                    display: 'block',
                    fontSize: '0.825rem',
                    fontWeight: 600,
                    color: PALETTE.charcoal,
                    marginBottom: 6,
                  }}
                >
                  Registered Phone Number
                </label>
                <div style={{ position: 'relative' }}>
                  <div style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94A3B8' }}>
                    <Phone size={16} />
                  </div>
                  <input
                    id="reg-phone"
                    type="tel"
                    placeholder="+91 98765 43210"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="input-field"
                    style={{ paddingLeft: 40, width: '100%', height: 44 }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: 22 }}>
                <label
                  htmlFor="reg-password"
                  style={{
                    display: 'block',
                    fontSize: '0.825rem',
                    fontWeight: 600,
                    color: PALETTE.charcoal,
                    marginBottom: 6,
                  }}
                >
                  Create Password (min 6 characters)
                </label>
                <div style={{ position: 'relative' }}>
                  <div style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94A3B8' }}>
                    <KeyRound size={16} />
                  </div>
                  <input
                    id="reg-password"
                    type={showPass ? 'text' : 'password'}
                    placeholder="Minimum 6 characters"
                    required
                    minLength={6}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="input-field"
                    style={{ paddingLeft: 40, paddingRight: 44, width: '100%', height: 44 }}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass((s) => !s)}
                    aria-label={showPass ? 'Hide password' : 'Show password'}
                    style={{
                      position: 'absolute',
                      right: 12,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      color: PALETTE.muted,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      padding: 4,
                    }}
                  >
                    {showPass ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                id="register-submit-button"
                disabled={loading}
                className="btn btn-primary btn-lg"
                style={{ width: '100%', height: 48, borderRadius: 10, fontSize: '0.96rem' }}
              >
                {loading ? 'Creating Store…' : 'Register Shop & Get Started'}
                {!loading && <ArrowRight size={17} />}
              </button>
            </form>
          )}

          {/* ── SEPARATE DEMO SECTION ─────────────────────────────────── */}
          <div
            style={{
              marginTop: 24,
              paddingTop: 20,
              borderTop: `1px solid ${PALETTE.border}`,
              textAlign: 'center',
            }}
          >
            <div style={{ fontSize: '0.82rem', color: PALETTE.muted, marginBottom: 10 }}>
              Want to test with sample Kirana records?
            </div>
            <button
              type="button"
              id="demo-store-button"
              onClick={handleDemoLogin}
              disabled={loading}
              className="btn btn-secondary"
              style={{
                width: '100%',
                height: 42,
                borderRadius: 10,
                borderColor: PALETTE.emerald,
                color: PALETTE.emerald,
                background: PALETTE.mint,
                fontWeight: 700,
              }}
            >
              <Zap size={16} color="#E9B949" />
              <span>{loading ? 'Opening Demo Sandbox…' : 'Open Live Demo Store (No Sign-Up)'}</span>
            </button>
          </div>
        </div>

        {/* Security Footer */}
        <div
          style={{
            marginTop: 22,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: '0.75rem',
            color: PALETTE.muted,
            textAlign: 'center',
          }}
        >
          <Lock size={13} color={PALETTE.emerald} />
          <span>256-Bit Encrypted &bull; Multi-Tenant Isolated &bull; Gnani Voice AI</span>
        </div>
      </div>
    </div>
  );
}
