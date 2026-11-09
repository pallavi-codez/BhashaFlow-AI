import React from 'react';
import { 
  LayoutDashboard, 
  Mic, 
  Users, 
  Receipt, 
  CreditCard, 
  HelpCircle, 
  Settings, 
  LogOut,
  Sparkles
} from 'lucide-react';
import { getTranslation } from '../i18n/translations';

export default function Sidebar({ currentView, setCurrentView, currentLang, shop, onLogout, onOpenVoice }) {
  const t = (k) => getTranslation(currentLang, k);

  const navItems = [
    { id: 'dashboard', label: currentLang === 'en-IN' ? 'Overview' : t('dashboard'), icon: LayoutDashboard },
    { id: 'voice', label: currentLang === 'en-IN' ? 'Voice Transactions' : t('voiceEntry'), icon: Mic, highlight: true },
    { id: 'ask-ledger', label: currentLang === 'en-IN' ? 'Ask Your Ledger' : t('askLedger'), icon: HelpCircle },
    { id: 'customers', label: currentLang === 'en-IN' ? 'Customers' : t('customers'), icon: Users },
    { id: 'transactions', label: currentLang === 'en-IN' ? 'Transaction History' : t('transactions'), icon: Receipt },
    { id: 'expenses', label: currentLang === 'en-IN' ? 'Expenses' : t('expenses'), icon: CreditCard },
    { id: 'settings', label: currentLang === 'en-IN' ? 'Settings' : t('settings'), icon: Settings },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Sparkles size={20} color="#FFFFFF" />
        </div>
        <div>
          <div className="brand-title">BhashaFlow</div>
          <div style={{ fontSize: '0.68rem', color: '#DDF4E6', fontWeight: 700, letterSpacing: '0.04em' }}>GNANI AI POWERED</div>
        </div>
        {shop?.is_demo && <span className="brand-badge">DEMO</span>}
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;
          return (
            <button
              key={item.id}
              onClick={() => {
                if (item.id === 'voice') {
                  onOpenVoice();
                } else {
                  setCurrentView(item.id);
                }
              }}
              className={`nav-link ${isActive ? 'active' : ''}`}
              style={{
                width: '100%',
                background: isActive ? '#16865A' : 'none',
                textAlign: 'left',
                border: 'none',
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                cursor: 'pointer',
              }}
            >
              <Icon size={18} color={isActive ? '#FFFFFF' : item.highlight ? '#E9B949' : 'rgba(255, 255, 255, 0.7)'} />
              <span>{item.label}</span>
              {item.highlight && !isActive && (
                <span style={{
                  marginLeft: 'auto',
                  width: 7,
                  height: 7,
                  borderRadius: '50%',
                  background: '#E9B949',
                  boxShadow: '0 0 6px #E9B949'
                }} />
              )}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="shop-pill">
          <div className="shop-avatar">
            {shop?.name ? shop.name.charAt(0).toUpperCase() : 'K'}
          </div>
          <div style={{ minWidth: 0, flex: 1 }}>
            <div className="shop-info-name">{shop?.name || 'My Kirana Store'}</div>
            <div className="shop-info-phone">{shop?.phone || '+91 Demo Mode'}</div>
          </div>
        </div>

        <button
          onClick={onLogout}
          className="btn btn-secondary btn-sm"
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            color: '#F87171',
            borderColor: 'rgba(248, 113, 113, 0.2)',
            width: '100%',
            justifyContent: 'center',
          }}
        >
          <LogOut size={14} />
          <span>{t('logout')}</span>
        </button>
      </div>
    </aside>
  );
}
