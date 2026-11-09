import React, { useState, useEffect } from 'react';
import { Settings, Globe, Key, Shield, CheckCircle, AlertTriangle, RefreshCw, Cpu, Volume2, Mic } from 'lucide-react';
import { api } from '../services/api';

export default function SettingsView({ currentLang, setCurrentLang, languages, shop }) {
  const [healthStatus, setHealthStatus] = useState('checking');

  useEffect(() => {
    checkHealth();
  }, []);

  async function checkHealth() {
    setHealthStatus('checking');
    try {
      const res = await fetch('/health');
      if (res.ok) {
        setHealthStatus('connected');
      } else {
        setHealthStatus('error');
      }
    } catch {
      setHealthStatus('error');
    }
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.4rem', fontWeight: 700 }}>
          Settings &amp; AI Integration Status
        </h2>
        <p style={{ fontSize: '0.875rem', color: '#64748B' }}>
          Configure shop preferences, multilingual defaults, and check Gnani AI connectivity.
        </p>
      </div>

      {/* ── Language Configuration Card ───────────────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--mint)', color: 'var(--emerald-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Globe size={20} />
            </div>
            <div>
              <h3 className="card-title">Multilingual Language Selection</h3>
              <div style={{ fontSize: '0.8rem', color: 'var(--muted-text)' }}>
                Select active interface and speech-recognition language ({languages.length} Indian languages supported)
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12 }}>
          {languages.map((lang) => {
            const isSelected = lang.code === currentLang;
            return (
              <div
                key={lang.code}
                onClick={() => setCurrentLang(lang.code)}
                style={{
                  border: isSelected ? '2px solid var(--emerald-primary)' : '1px solid var(--border-color)',
                  background: isSelected ? 'var(--mint)' : 'var(--white)',
                  borderRadius: 12,
                  padding: 16,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <div>
                  <div style={{ fontWeight: 700, fontSize: '1rem', color: 'var(--charcoal-text)' }}>
                    {lang.name}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: 'var(--emerald-primary)', fontWeight: 600, marginTop: 2 }}>
                    {lang.native_name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--muted-text)', marginTop: 4 }}>
                    Voice: {lang.default_voice} &bull; {lang.text_direction === 'rtl' ? 'RTL Layout' : 'LTR'}
                  </div>
                </div>

                {isSelected ? (
                  <div style={{
                    width: 24,
                    height: 24,
                    borderRadius: '50%',
                    background: 'var(--emerald-primary)',
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <CheckCircle size={16} />
                  </div>
                ) : (
                  <span className="badge badge-cash">{lang.code}</span>
                )}
              </div>
            );
          })}
        </div>
      </div>



      {/* ── Shop Info Card ────────────────────────────────────────────────── */}
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: 16 }}>Shopkeeper Account Details</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B' }}>STORE NAME</div>
            <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 2 }}>{shop?.name || 'Demo Kirana Store'}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B' }}>REGISTERED PHONE</div>
            <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 2 }}>{shop?.phone || '+910000000000'}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#64748B' }}>ACCOUNT TYPE</div>
            <div style={{ fontSize: '1rem', fontWeight: 700, marginTop: 2 }}>
              {shop?.is_demo ? '⚡ Demonstration Store (Preloaded)' : '🏪 Registered Merchant'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
