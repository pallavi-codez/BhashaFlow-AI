import React from 'react';
import { LayoutDashboard, Users, Mic, Receipt, Settings } from 'lucide-react';
import { getTranslation } from '../i18n/translations';

export default function MobileNav({ currentView, setCurrentView, currentLang, onOpenVoice }) {
  const t = (k) => getTranslation(currentLang, k);

  return (
    <nav className="mobile-bottom-nav">
      <div
        className={`mobile-nav-item ${currentView === 'dashboard' ? 'active' : ''}`}
        onClick={() => setCurrentView('dashboard')}
      >
        <LayoutDashboard size={20} />
        <span>{t('dashboard')}</span>
      </div>

      <div
        className={`mobile-nav-item ${currentView === 'customers' ? 'active' : ''}`}
        onClick={() => setCurrentView('customers')}
      >
        <Users size={20} />
        <span>{t('customers')}</span>
      </div>

      {/* Floating Center Mic Button */}
      <div className="mobile-mic-fab" onClick={onOpenVoice} title="Record Voice">
        <Mic size={24} />
      </div>

      <div
        className={`mobile-nav-item ${currentView === 'transactions' ? 'active' : ''}`}
        onClick={() => setCurrentView('transactions')}
      >
        <Receipt size={20} />
        <span>{t('transactions')}</span>
      </div>

      <div
        className={`mobile-nav-item ${currentView === 'settings' ? 'active' : ''}`}
        onClick={() => setCurrentView('settings')}
      >
        <Settings size={20} />
        <span>{t('settings')}</span>
      </div>
    </nav>
  );
}
