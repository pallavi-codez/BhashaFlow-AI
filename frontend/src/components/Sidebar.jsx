import React from 'react';
import { 
  LayoutDashboard, 
  Mic, 
  Users, 
  Receipt, 
  CreditCard, 
  BarChart3, 
  Settings, 
  LogOut,
  Sparkles
} from 'lucide-react';
import { getTranslation } from '../i18n/translations';

export default function Sidebar({ currentView, setCurrentView, currentLang, shop, onLogout, onOpenVoice }) {
  const t = (k) => getTranslation(currentLang, k);

  const navItems = [
    { id: 'dashboard', label: t('dashboard'), icon: LayoutDashboard },
    { id: 'voice', label: t('voiceEntry'), icon: Mic, highlight: true },
    { id: 'customers', label: t('customers'), icon: Users },
    { id: 'transactions', label: t('transactions'), icon: Receipt },
    { id: 'expenses', label: t('expenses'), icon: CreditCard },
    { id: 'reports', label: t('reports'), icon: BarChart3 },
    { id: 'settings', label: t('settings'), icon: Settings },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Sparkles size={22} />
        </div>
        <div>
          <div className="brand-title">BhashaFlow</div>
          <div style={{ fontSize: '0.7rem', color: '#38BDF8', fontWeight: 600 }}>GNANI AI POWERED</div>
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
                background: 'none',
                textAlign: 'left',
                border: 'none',
              }}
            >
              <Icon size={19} color={isActive ? '#FFFFFF' : item.highlight ? '#38BDF8' : '#94A3B8'} />
              <span>{item.label}</span>
              {item.highlight && !isActive && (
                <span style={{
                  marginLeft: 'auto',
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: '#38BDF8',
                  boxShadow: '0 0 8px #38BDF8'
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
            color: '#EF4444',
            borderColor: 'rgba(239, 68, 68, 0.2)',
            width: '100%',
            justifyContent: 'center',
          }}
        >
          <LogOut size={15} />
          <span>{t('logout')}</span>
        </button>
      </div>
    </aside>
  );
}
