import React, { useState, useRef, useEffect } from 'react';
import { Globe, Mic, ChevronDown, Check } from 'lucide-react';
import { getTranslation } from '../i18n/translations';

export default function Header({ currentView, currentLang, setCurrentLang, languages, onOpenVoice }) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const t = (k) => getTranslation(currentLang, k);

  const viewTitles = {
    dashboard: t('dashboard'),
    customers: t('customers'),
    transactions: t('transactions'),
    expenses: t('expenses'),
    reports: t('reports'),
    settings: t('settings'),
  };

  const activeLangConfig = languages.find((l) => l.code === currentLang) || {
    name: 'Kannada',
    native_name: 'ಕನ್ನಡ',
    code: 'kn-IN',
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
      <div className="topbar-left">
        <h1 className="topbar-title">{viewTitles[currentView] || 'BhashaFlow AI'}</h1>
      </div>

      <div className="topbar-right">
        {/* Language Selector Dropdown */}
        <div className="lang-dropdown" ref={dropdownRef}>
          <button
            className="lang-selector"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            title="Switch Language"
          >
            <Globe size={16} color="#1E6FCC" />
            <span>{activeLangConfig.native_name} ({activeLangConfig.name})</span>
            <ChevronDown size={14} />
          </button>

          {dropdownOpen && (
            <div className="lang-menu">
              <div style={{ padding: '6px 8px', fontSize: '0.75rem', fontWeight: 700, color: '#64748B' }}>
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
                    {isSelected && <Check size={16} color="#1E6FCC" />}
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
            borderRadius: '9999px',
            boxShadow: '0 4px 12px rgba(30, 111, 204, 0.3)',
          }}
        >
          <Mic size={16} />
          <span>{t('voiceEntry')}</span>
        </button>
      </div>
    </header>
  );
}
