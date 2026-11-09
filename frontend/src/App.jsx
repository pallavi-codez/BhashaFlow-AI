import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import MobileNav from './components/MobileNav';
import VoiceModal from './components/VoiceModal';
import CustomerModal from './components/CustomerModal';
import PaymentModal from './components/PaymentModal';
import ExpenseModal from './components/ExpenseModal';
import DashboardView from './views/DashboardView';
import CustomersView from './views/CustomersView';
import TransactionsView from './views/TransactionsView';
import ExpensesView from './views/ExpensesView';
import AskLedgerView from './views/AskLedgerView';
import SettingsView from './views/SettingsView';
import AuthView from './views/AuthView';
import LandingView from './views/LandingView';
import { api } from './services/api';

function getInitialLanguage() {
  try {
    // 1. Authenticated account preference
    const savedShop = localStorage.getItem('bhashaflow_shop');
    if (savedShop) {
      const parsed = JSON.parse(savedShop);
      if (parsed?.language) return parsed.language;
    }
    // 2. Locally saved guest preference
    const guestLang = localStorage.getItem('bhashaflow_guest_lang');
    if (guestLang) return guestLang;
  } catch (e) {
    console.warn('Failed to read stored language preference:', e);
  }
  // 3. Strict first-visit default: English (en-IN), never inferred from browser/IP
  return 'en-IN';
}

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [guestView, setGuestView] = useState('landing'); // 'landing' | 'login' | 'register'
  const [shop, setShop] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [currentLang, setCurrentLang] = useState(getInitialLanguage);
  const [languages, setLanguages] = useState([]);
  const [dashboardStats, setDashboardStats] = useState(null);
  const [transactions, setTransactions] = useState([]);

  // Modals
  const [voiceModalOpen, setVoiceModalOpen] = useState(false);
  const [customerModalOpen, setCustomerModalOpen] = useState(false);
  const [paymentModalOpen, setPaymentModalOpen] = useState(false);
  const [paymentCustomer, setPaymentCustomer] = useState(null);
  const [expenseModalOpen, setExpenseModalOpen] = useState(false);

  useEffect(() => {
    async function restoreSession() {
      const token = localStorage.getItem('bhashaflow_token');
      if (token) {
        try {
          const profile = await api.getMe();
          const guestLang = localStorage.getItem('bhashaflow_guest_lang');
          const resolvedLang = profile.language || guestLang || 'en-IN';
          setShop({
            id: profile.id,
            name: profile.name,
            owner_name: profile.owner_name,
            phone: profile.phone,
            is_demo: !!profile.is_demo,
            language: resolvedLang,
          });
          setCurrentLang(resolvedLang);
          setIsAuthenticated(true);
        } catch (err) {
          console.warn('Session verification failed, logging out:', err.message);
          api.logout();
          setIsAuthenticated(false);
          setShop(null);
        }
      }
      loadLanguages();
    }

    restoreSession();
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated]);

  useEffect(() => {
    // Dynamic RTL text direction for Urdu
    const isRtl = currentLang === 'ur-IN';
    document.documentElement.dir = isRtl ? 'rtl' : 'ltr';
    document.documentElement.lang = currentLang;
  }, [currentLang]);

  async function loadLanguages() {
    try {
      const list = await api.listLanguages();
      setLanguages(list);
    } catch {
      // Fallback if backend server not yet queried
      setLanguages([
        { code: 'kn-IN', name: 'Kannada', native_name: 'ಕನ್ನಡ', default_voice: 'Kaveri', sample_phrase: 'Ramesh ge 500 rupees udhar haaku', text_direction: 'ltr' },
        { code: 'hi-IN', name: 'Hindi', native_name: 'हिन्दी', default_voice: 'Nalini', sample_phrase: 'Ramesh ko 500 rupaye udhar likho', text_direction: 'ltr' },
        { code: 'en-IN', name: 'English', native_name: 'English (India)', default_voice: 'Deepak', sample_phrase: 'Ramesh paid 200 rupees', text_direction: 'ltr' },
        { code: 'ta-IN', name: 'Tamil', native_name: 'தமிழ்', default_voice: 'Nalini', sample_phrase: 'Ramesh ku 500 roobai kadan podu', text_direction: 'ltr' },
        { code: 'te-IN', name: 'Telugu', native_name: 'తెలుగు', default_voice: 'Nalini', sample_phrase: 'Ramesh ki 500 rupayalu appu raayi', text_direction: 'ltr' },
        { code: 'ur-IN', name: 'Urdu', native_name: 'اردو', default_voice: 'Nalini', sample_phrase: 'رمیش کو 500 روپے ادھار لکھو', text_direction: 'rtl' },
      ]);
    }
  }

  async function loadData() {
    try {
      const stats = await api.getDashboard();
      setDashboardStats(stats);
      const txns = await api.listTransactions({ limit: 50 });
      setTransactions(txns);
    } catch (err) {
      console.warn('Data load error:', err.message);
    }
  }

  function handleAuthSuccess(authResult) {
    const guestLang = localStorage.getItem('bhashaflow_guest_lang');
    const resolvedLang = authResult.language || guestLang || 'en-IN';
    setShop({
      id: authResult.shop_id,
      name: authResult.shop_name,
      is_demo: !!authResult.is_demo,
      language: resolvedLang,
    });
    setCurrentLang(resolvedLang);
    setIsAuthenticated(true);
  }

  async function handleLanguageChange(newLang) {
    if (!newLang) return;
    // 1. Immediate UI update across all components
    setCurrentLang(newLang);
    // 2. Persist locally for returning visits / guests
    try {
      localStorage.setItem('bhashaflow_guest_lang', newLang);
    } catch (e) {
      console.warn('Failed to store guest language preference:', e);
    }
    // 3. For authenticated customers, persist to backend shop profile
    if (isAuthenticated || localStorage.getItem('bhashaflow_token')) {
      try {
        await api.updateLanguage(newLang);
        setShop((prev) => (prev ? { ...prev, language: newLang } : null));
      } catch (err) {
        console.warn('Failed to persist language to backend:', err.message);
      }
    }
  }

  async function handleDemoLogin() {
    try {
      const data = await api.demoLogin();
      handleAuthSuccess(data);
    } catch (err) {
      console.error('Demo store initialization failed:', err);
    }
  }

  function handleLogout() {
    api.logout();
    setIsAuthenticated(false);
    setShop(null);
    setCurrentView('dashboard');
    setGuestView('landing');
  }

  function handleOpenPaymentModal(cust) {
    setPaymentCustomer(cust);
    setPaymentModalOpen(true);
  }

  function handleTransactionComplete() {
    loadData();
  }

  if (!isAuthenticated) {
    if (guestView === 'landing') {
      return (
        <LandingView
          onGetStarted={() => setGuestView('register')}
          onSignIn={() => setGuestView('login')}
          onDemoLogin={handleDemoLogin}
          languages={languages}
          currentLang={currentLang}
          onLanguageChange={handleLanguageChange}
        />
      );
    }

    return (
      <AuthView
        initialMode={guestView}
        onBackToHome={() => setGuestView('landing')}
        onAuthSuccess={handleAuthSuccess}
        languages={languages}
        selectedLang={currentLang}
        setSelectedLang={handleLanguageChange}
      />
    );
  }

  return (
    <div className="app-layout">
      {/* Desktop Navigation Sidebar */}
      <Sidebar
        currentView={currentView}
        setCurrentView={setCurrentView}
        currentLang={currentLang}
        shop={shop}
        onLogout={handleLogout}
        onOpenVoice={() => setVoiceModalOpen(true)}
      />

      <div className="main-content">
        {/* Top Header */}
        <Header
          currentView={currentView}
          currentLang={currentLang}
          setCurrentLang={handleLanguageChange}
          languages={languages}
          onOpenVoice={() => setVoiceModalOpen(true)}
          shop={shop}
        />

        {/* Dynamic Page Views */}
        <main className="page-container">
          {currentView === 'dashboard' && (
            <DashboardView
              stats={dashboardStats}
              transactions={transactions}
              currentLang={currentLang}
              languages={languages}
              onOpenVoice={() => setVoiceModalOpen(true)}
              onOpenCustomerModal={() => setCustomerModalOpen(true)}
              onOpenExpenseModal={() => setExpenseModalOpen(true)}
              setCurrentView={setCurrentView}
              shop={shop}
            />
          )}

          {currentView === 'customers' && (
            <CustomersView
              currentLang={currentLang}
              onOpenCustomerModal={() => setCustomerModalOpen(true)}
              onOpenPaymentModal={handleOpenPaymentModal}
            />
          )}

          {currentView === 'transactions' && (
            <TransactionsView
              currentLang={currentLang}
              onOpenVoice={() => setVoiceModalOpen(true)}
            />
          )}

          {currentView === 'expenses' && (
            <ExpensesView
              onOpenExpenseModal={() => setExpenseModalOpen(true)}
            />
          )}

          {currentView === 'ask-ledger' && (
            <AskLedgerView currentLang={currentLang} languages={languages} />
          )}

          {currentView === 'settings' && (
            <SettingsView
              currentLang={currentLang}
              setCurrentLang={handleLanguageChange}
              languages={languages}
              shop={shop}
            />
          )}
        </main>

        {/* Mobile Navigation Bar */}
        <MobileNav
          currentView={currentView}
          setCurrentView={setCurrentView}
          currentLang={currentLang}
          onOpenVoice={() => setVoiceModalOpen(true)}
        />
      </div>

      {/* Global Modals */}
      <VoiceModal
        isOpen={voiceModalOpen}
        onClose={() => setVoiceModalOpen(false)}
        currentLang={currentLang}
        languages={languages}
        onTransactionComplete={handleTransactionComplete}
      />

      <CustomerModal
        isOpen={customerModalOpen}
        onClose={() => setCustomerModalOpen(false)}
        onCustomerCreated={() => {
          loadData();
        }}
      />

      <PaymentModal
        isOpen={paymentModalOpen}
        onClose={() => {
          setPaymentModalOpen(false);
          setPaymentCustomer(null);
        }}
        customer={paymentCustomer}
        onPaymentRecorded={() => {
          loadData();
        }}
      />

      <ExpenseModal
        isOpen={expenseModalOpen}
        onClose={() => setExpenseModalOpen(false)}
        onExpenseCreated={() => {
          loadData();
        }}
      />
    </div>
  );
}
