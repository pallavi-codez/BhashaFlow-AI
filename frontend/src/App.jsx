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
import ReportsView from './views/ReportsView';
import SettingsView from './views/SettingsView';
import AuthView from './views/AuthView';
import { api } from './services/api';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [shop, setShop] = useState(null);
  const [currentView, setCurrentView] = useState('dashboard');
  const [currentLang, setCurrentLang] = useState('kn-IN');
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
    // Check existing auth session
    const savedShop = api.getSavedShop();
    const token = localStorage.getItem('bhashaflow_token');
    if (savedShop && token) {
      setShop(savedShop);
      setIsAuthenticated(true);
    }

    loadLanguages();
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
    setShop({
      id: authResult.shop_id,
      name: authResult.shop_name,
      is_demo: authResult.shop_name.includes('Demo'),
    });
    setIsAuthenticated(true);
  }

  function handleLogout() {
    api.logout();
    setIsAuthenticated(false);
    setShop(null);
    setCurrentView('dashboard');
  }

  function handleOpenPaymentModal(cust) {
    setPaymentCustomer(cust);
    setPaymentModalOpen(true);
  }

  function handleTransactionComplete() {
    loadData();
  }

  if (!isAuthenticated) {
    return (
      <AuthView
        onAuthSuccess={handleAuthSuccess}
        languages={languages}
        selectedLang={currentLang}
        setSelectedLang={setCurrentLang}
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
          setCurrentLang={setCurrentLang}
          languages={languages}
          onOpenVoice={() => setVoiceModalOpen(true)}
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

          {currentView === 'reports' && (
            <ReportsView stats={dashboardStats} />
          )}

          {currentView === 'settings' && (
            <SettingsView
              currentLang={currentLang}
              setCurrentLang={setCurrentLang}
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
