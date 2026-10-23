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
            <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#EBF3FC', color: '#1E6FCC', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Globe size={20} />
            </div>
            <div>
              <h3 className="card-title">Multilingual Language Selection</h3>
              <div style={{ fontSize: '0.8rem', color: '#64748B' }}>
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
                  border: isSelected ? '2px solid #1E6FCC' : '1px solid var(--border)',
                  background: isSelected ? '#EFF6FF' : 'var(--bg-surface)',
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
                  <div style={{ fontWeight: 700, fontSize: '1rem', color: '#0F172A' }}>
                    {lang.name}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#1E6FCC', fontWeight: 600, marginTop: 2 }}>
                    {lang.native_name}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: '#64748B', marginTop: 4 }}>
                    Voice: {lang.default_voice} &bull; {lang.text_direction === 'rtl' ? 'RTL Layout' : 'LTR'}
                  </div>
                </div>

                {isSelected ? (
                  <div style={{
                    width: 24,
                    height: 24,
                    borderRadius: '50%',
                    background: '#1E6FCC',
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

      {/* ── Gnani AI Architecture & Secrets Guide ─────────────────────────── */}
      <div className="card">
        <div className="card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 36, height: 36, borderRadius: '50%', background: '#F0FDF4', color: '#10B981', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Cpu size={20} />
            </div>
            <div>
              <h3 className="card-title">Gnani AI Integration Status</h3>
              <div style={{ fontSize: '0.8rem', color: '#64748B' }}>
                Prisma Speech-to-Text &amp; Timbre Text-to-Speech Architecture
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span className={`badge ${healthStatus === 'connected' ? 'badge-payment' : 'badge-credit'}`}>
              Backend API: {healthStatus === 'connected' ? '● Online' : 'Checking…'}
            </span>
            <button className="btn btn-secondary btn-sm" onClick={checkHealth} title="Check connection">
              <RefreshCw size={14} />
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
          {/* STT Status */}
          <div style={{ padding: 18, background: '#F8FAFC', borderRadius: 12, border: '1px solid #E2E8F0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Mic size={18} color="#1E6FCC" />
              <div style={{ fontWeight: 700, color: '#0F172A' }}>Gnani Prisma (STT)</div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#64748B', lineHeight: 1.5 }}>
              Endpoint: <code>POST https://api.vachana.ai/stt/v3</code><br />
              Format: <code>multipart/form-data</code> with ITN native numerals.<br />
              Auth: <code>X-API-Key-ID</code> (Protected Server-Side)
            </div>
          </div>

          {/* TTS Status */}
          <div style={{ padding: 18, background: '#F8FAFC', borderRadius: 12, border: '1px solid #E2E8F0' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Volume2 size={18} color="#10B981" />
              <div style={{ fontWeight: 700, color: '#0F172A' }}>Gnani Timbre (TTS)</div>
            </div>
            <div style={{ fontSize: '0.8rem', color: '#64748B', lineHeight: 1.5 }}>
              Endpoint: <code>POST https://api.vachana.ai/api/v1/tts/inference</code><br />
              Model: <code>timbre-v2.5</code> (Voices: Kaveri, Nalini, Deepak)<br />
              Output: Streamed browser-playable WAV PCM audio.
            </div>
          </div>
        </div>

        <div style={{ marginTop: 20, padding: '16px', background: '#F8FAFC', borderRadius: 12, border: '1px dashed #CBD5E1' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 700, fontSize: '0.9rem', color: '#0F172A', marginBottom: 6 }}>
            <Key size={16} color="#F59E0B" /> Secret Configuration Guide
          </div>
          <p style={{ fontSize: '0.85rem', color: '#64748B', lineHeight: 1.6 }}>
            To supply your live Gnani API key: set <code>GNANI_API_KEY=&lt;your_key&gt;</code> in <code>backend/.env</code> or as a system environment variable. The backend reads it securely on the server side and never exposes secrets to the browser bundle or client requests.
          </p>
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
