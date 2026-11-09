import React, { useState, useRef, useEffect } from 'react';
import { Globe, Mic, ChevronDown, Check } from 'lucide-react';
import { getTranslation } from '../i18n/translations';

export default function Header({ currentView, currentLang, setCurrentLang, languages, onOpenVoice, shop }) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const t = (k) => getTranslation(currentLang, k);

  const viewTitles = {
    dashboard: t('dashboard'),
    'ask-ledger': t('askLedger'),
    customers: t('customers'),
    transactions: t('transactions'),
    expenses: t('expenses'),
    settings: t('settings'),
  };

  const activeLangConfig = languages.find((l) => l.code === currentLang) || {
    name: 'English',
    native_name: 'English (India)',
    code: 'en-IN',
  };

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="topbar">
      <div className="topbar-left" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <h1 className="topbar-title">{viewTitles[currentView] || 'BhashaFlow AI'}</h1>
        {shop?.is_demo && (
          <span className="demo-indicator-badge" title="You are viewing synthetic demo kirana data">
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#D97706', display: 'inline-block' }} />
            Demo Store
          </span>
        )}
      </div>

      <div className="topbar-right">
        {/* Language Selector Dropdown */}
        <div className="lang-dropdown" ref={dropdownRef}>
          <button
            className="lang-selector"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            title="Switch Language"
          >
            <Globe size={16} color="var(--primary)" />
            <span>{activeLangConfig.native_name} ({activeLangConfig.name})</span>
            <ChevronDown size={14} />
          </button>

          {dropdownOpen && (
            <div className="lang-menu">
              <div style={{ padding: '6px 8px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)' }}>
                SELECT INDIAN LANGUAGE
              </div>
              {languages.map((lang) => {
                const isSelected = lang.code === currentLang;
                return (
                  <div
                    key={lang.code}
                    className={`lang-option ${isSelected ? 'active' : ''}`}
                    onClick={() => {
                      setCurrentLang(lang.code);
                      setDropdownOpen(false);
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: isSelected ? 600 : 500 }}>{lang.name}</div>
                      <div className="lang-native-badge">{lang.native_name}</div>
                    </div>
                    {isSelected && <Check size={16} color="var(--primary)" />}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Quick Voice Trigger */}
        <button
          className="btn btn-primary btn-sm"
          onClick={onOpenVoice}
          style={{
            borderRadius: 'var(--radius-full)',
            boxShadow: '0 4px 12px rgba(22, 134, 90, 0.25)',
          }}
        >
          <Mic size={16} />
          <span>{t('voiceEntry')}</span>
        </button>
      </div>
    </header>
  );
}
