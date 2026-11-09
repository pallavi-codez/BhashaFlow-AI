import React, { useState, useEffect } from 'react';
import {
  Mic,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  TrendingUp,
  Wallet,
  Receipt,
  Users,
  CreditCard,
  HelpCircle,
  Volume2,
  Lock,
  ChevronRight,
  Globe,
  Play,
  Zap,
  BarChart3,
  Check
} from 'lucide-react';

export default function LandingView({
  onGetStarted,
  onSignIn,
  onDemoLogin,
  languages = [],
  currentLang = 'en-IN',
  onLanguageChange
}) {
  const [activeTab, setActiveTab] = useState('kannada');
  const [selectedDemoQuestion, setSelectedDemoQuestion] = useState(0);

  const DEMO_QUESTIONS = [
    {
      q: 'How much does Ramesh owe?',
      indic: 'ರಮೇಶ್ ಎಷ್ಟು ಹಣ ಕೊಡಬೇಕು?',
      lang: 'Kannada / English',
      intent: 'Customer Balance',
      amount: '₹400.00',
      answer: 'Ramesh owes ₹400.00 (from ₹500.00 credit sales minus ₹100.00 payments).',
      detail: 'Last payment of ₹100 recorded on Oct 29'
    },
    {
      q: 'How much credit did I give today?',
      indic: 'आज कितना उधार दिया?',
      lang: 'Hindi / English',
      intent: 'Today\'s Credit Sales',
      amount: '₹2,000.00',
      answer: 'You gave ₹2,000.00 in credit today across 2 customers (Ramesh ₹500, Suresh ₹1,500).',
      detail: '2 confirmed credit sales entries'
    },
    {
      q: 'Who owes me more than ₹1,000?',
      indic: 'ಯಾರು ₹1,000 ಕ್ಕಿಂತ ಹೆಚ್ಚು ಕೊಡಬೇಕು?',
      lang: 'Kannada / English',
      intent: 'High Debt Customers',
      amount: '₹1,500.00',
      answer: '1 customer owes more than ₹1,000.00: Suresh with an outstanding balance of ₹1,500.00.',
      detail: 'Suresh (+91 98765 43211)'
    },
    {
      q: 'How much cash did I collect today?',
      indic: 'ಇವತ್ತು ಎಷ್ಟು ಕ್ಯಾಶ್ ಕಲೆಕ್ಟ್ ಆಯ್ತು?',
      lang: 'Kannada / English',
      intent: 'Cash Collection',
      amount: '₹400.00',
      answer: 'You collected ₹400.00 in cash today: ₹300.00 from cash sales and ₹100.00 from debt repayments.',
      detail: 'Strictly excludes uncollected credit sales'
    },
    {
      q: 'How much did I sell today?',
      indic: 'आज कुल कितनी बिक्री हुई?',
      lang: 'Hindi / English',
      intent: 'Total Sales',
      amount: '₹2,300.00',
      answer: 'Total sales today: ₹2,300.00 (Credit sales ₹2,000.00 + Cash sales ₹300.00). Debt repayments are excluded from sales.',
      detail: 'Exact Decimal accounting rules applied'
    }
  ];

  const POPULAR_LANG_PREVIEWS = [
    { code: 'kn-IN', name: 'Kannada', native: 'ಕನ್ನಡ', sample: 'Ramesh ge 500 rupees udhar haaku', meaning: 'Add ₹500 credit for Ramesh', voice: 'Kaveri' },
    { code: 'hi-IN', name: 'Hindi', native: 'हिन्दी', sample: 'Ramesh ko 500 rupaye udhar likho', meaning: 'Write ₹500 credit for Ramesh', voice: 'Nalini' },
    { code: 'en-IN', name: 'English', native: 'English', sample: 'Ramesh paid 200 rupees against debt', meaning: 'Record ₹200 repayment from Ramesh', voice: 'Deepak' },
    { code: 'ta-IN', name: 'Tamil', native: 'தமிழ்', sample: 'Ramesh ku 500 roobai kadan podu', meaning: 'Add ₹500 credit for Ramesh', voice: 'Nalini' },
    { code: 'te-IN', name: 'Telugu', native: 'తెలుగు', sample: 'Ramesh ki 500 rupayalu appu raayi', meaning: 'Write ₹500 debt for Ramesh', voice: 'Nalini' },
    { code: 'mr-IN', name: 'Marathi', native: 'मराठी', sample: 'Ramesh la 500 rupaye udhar dya', meaning: 'Give ₹500 credit to Ramesh', voice: 'Nalini' },
  ];

  return (
    <div className="landing-root">
      {/* ── 1. STICKY TOP NAVIGATION BAR ────────────────────────────────────── */}
      <header className="landing-navbar">
        <div className="landing-nav-container">
          {/* Brand Logo */}
          <div className="landing-brand">
            <div className="landing-brand-icon">
              <Sparkles size={20} color="#FFFFFF" />
            </div>
            <div className="landing-brand-text">
              <span className="brand-name">BhashaFlow</span>
              <span className="brand-dot">AI</span>
            </div>
            <span className="brand-tagline-badge">GNANI VOICE AI</span>
          </div>

          {/* Desktop Nav Links */}
          <nav className="landing-nav-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#languages">13 Languages</a>
            <a href="#ask-ledger">Ask Your Ledger</a>
            <a href="#security">Security</a>
          </nav>

          {/* Nav Right Action Buttons */}
          <div className="landing-nav-actions">
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={onDemoLogin}
              title="Test with preloaded Kirana store data without sign-up"
            >
              <Zap size={14} color="#E9B949" />
              <span>Demo Store</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={onSignIn}
            >
              Sign In
            </button>
            <button
              type="button"
              className="btn btn-primary btn-sm"
              onClick={onGetStarted}
            >
              <span>Get Started</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </header>

      {/* ── 2. HERO SECTION WITH MOTION GRAPHICS ───────────────────────────── */}
      <section className="landing-hero">
        <div className="hero-backdrop-glow" />
        <div className="landing-container hero-grid">
          {/* Left Column: Value Proposition */}
          <div className="hero-text-content">
            <div className="hero-pill-badge">
              <div className="pulse-dot" />
              <span>Voice-Powered Digital Ledger for Indian Retail</span>
            </div>

            <h1 className="hero-headline">
              Your Business.<br />
              Your Language.<br />
              <span className="hero-highlight">Your Ledger.</span>
            </h1>

            <p className="hero-subtext">
              Manage customer credit, payments and daily transactions naturally using your voice.
              A smarter digital ledger built for every Indian shopkeeper.
            </p>

            {/* CTAs */}
            <div className="hero-cta-group">
              <button
                type="button"
                className="btn btn-primary btn-lg"
                onClick={onGetStarted}
              >
                <span>Get Started Free</span>
                <ArrowRight size={18} />
              </button>
              <button
                type="button"
                className="btn btn-secondary btn-lg"
                onClick={onDemoLogin}
              >
                <Zap size={17} color="#E9B949" />
                <span>Explore Live Demo</span>
              </button>
            </div>

            {/* Trust Micro-Badges */}
            <div className="hero-trust-bar">
              <div className="trust-item">
                <CheckCircle2 size={16} color="#16865A" />
                <span>13 Indian Languages</span>
              </div>
              <div className="trust-item">
                <CheckCircle2 size={16} color="#16865A" />
                <span>Accurate Ledger Calculations</span>
              </div>
              <div className="trust-item">
                <CheckCircle2 size={16} color="#16865A" />
                <span>Private Shop Data</span>
              </div>
            </div>
          </div>

          {/* Right Column: Hero Motion Graphics & Live Card Showcase */}
          <div className="hero-visual-showcase">
            <div className="interactive-card-stack">
              {/* Floating Top Card: Debt Tracker */}
              <div className="floating-card floating-card-top">
                <div className="floating-card-icon debt">
                  <Users size={16} />
                </div>
                <div>
                  <div className="floating-card-label">Customer Udhar</div>
                  <div className="floating-card-value text-debt">Ramesh: ₹400.00</div>
                </div>
                <span className="badge badge-credit ml-auto">Confirmed</span>
              </div>

              {/* Main Center Piece: Voice-to-Ledger Interactive Visualizer */}
              <div className="hero-device-card">
                <div className="device-header">
                  <div className="device-dots">
                    <span className="dot red" />
                    <span className="dot yellow" />
                    <span className="dot green" />
                  </div>
                  <div className="device-title">BhashaFlow AI • Voice Engine</div>
                  <span className="badge badge-voice">Gnani Prisma STT</span>
                </div>

                <div className="device-body">
                  {/* Waveform Animation */}
                  <div className="waveform-box">
                    <div className="waveform-bar bar-1" />
                    <div className="waveform-bar bar-2" />
                    <div className="waveform-bar bar-3" />
                    <div className="waveform-bar bar-4" />
                    <div className="waveform-bar bar-5" />
                    <div className="waveform-bar bar-6" />
                    <div className="waveform-bar bar-7" />
                    <div className="waveform-bar bar-8" />
                    <div className="waveform-bar bar-9" />
                    <div className="waveform-bar bar-10" />
                    <div className="waveform-bar bar-11" />
                    <div className="waveform-bar bar-12" />
                  </div>

                  <div className="device-transcript">
                    <div className="transcript-label">Recognized Speech (Kannada)</div>
                    <div className="transcript-text">"ರಮೇಶ್‌ಗೆ 500 ರೂಪಾಯಿ ಉದ್ಧಾರ ಹಾಕು"</div>
                    <div className="transcript-translation">"Put 500 rupees credit for Ramesh"</div>
                  </div>

                  {/* Structured Ledger Result */}
                  <div className="device-parsed-preview">
                    <div className="parsed-row">
                      <span className="parsed-key">Customer:</span>
                      <span className="parsed-val">Ramesh [Auto-Matched]</span>
                    </div>
                    <div className="parsed-row">
                      <span className="parsed-key">Amount:</span>
                      <span className="parsed-val amount">₹500.00</span>
                    </div>
                    <div className="parsed-row">
                      <span className="parsed-key">Transaction:</span>
                      <span className="parsed-val type">Credit Sale (Udhar)</span>
                    </div>
                    <div className="parsed-status">
                      <CheckCircle2 size={15} color="#16865A" />
                      <span>Saved to Ledger • Verified Balance: ₹400.00</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating Bottom Card: Cash Collection */}
              <div className="floating-card floating-card-bottom">
                <div className="floating-card-icon cash">
                  <Wallet size={16} />
                </div>
                <div>
                  <div className="floating-card-label">Payment Received</div>
                  <div className="floating-card-value text-cash">+₹300.00 Cash</div>
                </div>
                <span className="badge badge-payment ml-auto">Verified</span>
              </div>
            </div>
          </div>
        </div>
      </section>



      {/* ── 4. HOW IT WORKS: 4-STAGE PIPELINE ───────────────────────────────── */}
      <section id="how-it-works" className="landing-section bg-ivory">
        <div className="landing-container">
          <div className="section-header text-center">
            <span className="section-eyebrow">Natural Voice Pipeline</span>
            <h2 className="section-heading">How BhashaFlow Transforms Voice to Ledger</h2>
            <p className="section-subheading">
              Four seamless steps from regional spoken voice to an immutable, multi-tenant financial record.
            </p>
          </div>

          <div className="pipeline-grid">
            <div className="pipeline-card">
              <div className="pipeline-step-badge">Step 1</div>
              <div className="pipeline-icon-box">
                <Mic size={24} color="#16865A" />
              </div>
              <h3 className="pipeline-title">Speak Naturally</h3>
              <p className="pipeline-desc">
                Tap the microphone and speak as you would talk to your customer in your mother tongue.
              </p>
              <div className="pipeline-example">"Suresh ge 1500 rupees udhar kodi"</div>
            </div>

            <div className="pipeline-card">
              <div className="pipeline-step-badge">Step 2</div>
              <div className="pipeline-icon-box">
                <Sparkles size={24} color="#16865A" />
              </div>
              <h3 className="pipeline-title">Understand &amp; Transcribe</h3>
              <p className="pipeline-desc">
                Gnani Prisma STT converts speech into exact text, handling local Indian retail terminology with ease.
              </p>
              <div className="pipeline-example">Prisma STT + NLP extraction</div>
            </div>

            <div className="pipeline-card">
              <div className="pipeline-step-badge">Step 3</div>
              <div className="pipeline-icon-box">
                <CheckCircle2 size={24} color="#16865A" />
              </div>
              <h3 className="pipeline-title">Confirm &amp; Validate</h3>
              <p className="pipeline-desc">
                Review the auto-detected customer, exact amount, and transaction type before committing to records.
              </p>
              <div className="pipeline-example">Explicit confirmation screen</div>
            </div>

            <div className="pipeline-card">
              <div className="pipeline-step-badge">Step 4</div>
              <div className="pipeline-icon-box">
                <Receipt size={24} color="#16865A" />
              </div>
              <h3 className="pipeline-title">Secure Transaction History</h3>
              <p className="pipeline-desc">
                The transaction is stored in your private store ledger with audit trail and exact Decimal balances.
              </p>
              <div className="pipeline-example">Updated balances in real time</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 5. CORE FEATURES GRID ───────────────────────────────────────────── */}
      <section id="features" className="landing-section">
        <div className="landing-container">
          <div className="section-header text-center">
            <span className="section-eyebrow">Built for Everyday Retail</span>
            <h2 className="section-heading">Designed for Indian Retail Merchants</h2>
            <p className="section-subheading">
              Every detail is engineered for real kirana shop operations — fast, private, and mathematically exact.
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon-wrapper">
                <Mic size={22} color="#16865A" />
              </div>
              <h3 className="feature-title">Voice-First Natural Entry</h3>
              <p className="feature-description">
                No typing required. Record credit sales, payments received, cash sales, and shop expenses in seconds using voice.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper">
                <HelpCircle size={22} color="#16865A" />
              </div>
              <h3 className="feature-title">Ask Your Ledger</h3>
              <p className="feature-description">
                Ask conversational questions like "How much does Ramesh owe?" or "Who owes me more than ₹1,000?" and receive instant database answers.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper">
                <ShieldCheck size={22} color="#16865A" />
              </div>
              <h3 className="feature-title">Multi-Tenant Shop Isolation</h3>
              <p className="feature-description">
                Every shopkeeper's customers, debts, and ledger transactions are strictly encrypted and isolated to their authenticated account.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper">
                <BarChart3 size={22} color="#16865A" />
              </div>
              <h3 className="feature-title">Decimal-Safe Financial Math</h3>
              <p className="feature-description">
                Zero floating-point rounding errors. All transactions and balances are computed with authoritative Python Decimal arithmetic.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper">
                <Volume2 size={22} color="#16865A" />
              </div>
              <h3 className="feature-title">Audio Spoken Answers (TTS)</h3>
              <p className="feature-description">
                Listen to answer summaries read aloud in natural voices like Kaveri, Nalini, and Deepak powered by Gnani Timbre TTS.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon-wrapper">
                <Globe size={22} color="#16865A" />
              </div>
              <h3 className="feature-title">13 Regional Indian Languages</h3>
              <p className="feature-description">
                Full interface and speech support for Kannada, Hindi, Tamil, Telugu, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Odia, Assamese, Urdu, and English.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── 6. ASK YOUR LEDGER INTERACTIVE PREVIEW ─────────────────────────── */}
      <section id="ask-ledger" className="landing-section bg-ivory">
        <div className="landing-container">
          <div className="section-header text-center">
            <span className="section-eyebrow">Financial Conversational AI</span>
            <h2 className="section-heading">Instant Answers from Your Store Records</h2>
            <p className="section-subheading">
              Never guess numbers. Ask your ledger directly in natural language and get deterministic answers calculated from confirmed records.
            </p>
          </div>

          <div className="demo-ask-wrapper">
            {/* Question Selector Chips */}
            <div className="demo-ask-questions">
              {DEMO_QUESTIONS.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  className={`demo-question-pill ${selectedDemoQuestion === idx ? 'active' : ''}`}
                  onClick={() => setSelectedDemoQuestion(idx)}
                >
                  <span className="q-icon">💡</span>
                  <div className="q-text">
                    <div className="q-main">{item.q}</div>
                    <div className="q-indic">{item.indic}</div>
                  </div>
                </button>
              ))}
            </div>

            {/* Answer Showcase Card */}
            <div className="demo-answer-card">
              <div className="answer-header">
                <div>
                  <span className="badge badge-cash">
                    INTENT: {DEMO_QUESTIONS[selectedDemoQuestion].intent.toUpperCase()}
                  </span>
                  <div className="answer-lang-label">
                    Tested in {DEMO_QUESTIONS[selectedDemoQuestion].lang}
                  </div>
                </div>
                <div className="answer-amount-pill">
                  <div className="pill-small">Exact Total</div>
                  <div className="pill-val">{DEMO_QUESTIONS[selectedDemoQuestion].amount}</div>
                </div>
              </div>

              <div className="answer-query-bubble">
                "{DEMO_QUESTIONS[selectedDemoQuestion].q}"
              </div>

              <div className="answer-body-text">
                {DEMO_QUESTIONS[selectedDemoQuestion].answer}
              </div>

              <div className="answer-footer-meta">
                <div className="meta-item">
                  <CheckCircle2 size={14} color="#16865A" />
                  <span>{DEMO_QUESTIONS[selectedDemoQuestion].detail}</span>
                </div>
                <div className="meta-item">
                  <Lock size={14} color="#65756B" />
                  <span>Verified Database Record Only</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 7. MULTILINGUAL INDIAN LANGUAGES SHOWCASE ───────────────────────── */}
      <section id="languages" className="landing-section">
        <div className="landing-container">
          <div className="section-header text-center">
            <span className="section-eyebrow">Pan-Indian Inclusivity</span>
            <h2 className="section-heading">Supported in 13 Indian Languages</h2>
            <p className="section-subheading">
              Every shopkeeper deserves to manage their business in the language they speak at home.
            </p>
          </div>

          <div className="languages-preview-grid">
            {POPULAR_LANG_PREVIEWS.map((lang) => (
              <div key={lang.code} className="lang-preview-card">
                <div className="lang-card-header">
                  <div>
                    <h3 className="lang-name">{lang.name}</h3>
                    <div className="lang-native">{lang.native}</div>
                  </div>
                  <span className="badge badge-cash">{lang.voice} Voice</span>
                </div>
                <div className="lang-sample-box">
                  <div className="lang-sample-text">🗣️ "{lang.sample}"</div>
                  <div className="lang-sample-meaning">{lang.meaning}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="languages-footer-pills">
            <span className="also-supported">Also fully supported:</span>
            {['മലയാളം (Malayalam)', 'বাংলা (Bengali)', 'ગુજરાતી (Gujarati)', 'ਪੰਜਾਬੀ (Punjabi)', 'ଓଡ଼ିଆ (Odia)', 'অসমীয়া (Assamese)', 'اردو (Urdu)'].map((l, i) => (
              <span key={i} className="lang-tag-pill">{l}</span>
            ))}
          </div>
        </div>
      </section>

      {/* ── 8. DEMO SANDBOX BANNER ─────────────────────────────────────────── */}
      <section className="landing-sandbox-cta">
        <div className="landing-container">
          <div className="sandbox-card">
            <div className="sandbox-content">
              <div className="sandbox-badge">
                <Zap size={14} color="#E9B949" />
                <span>Zero Commitment Sandbox</span>
              </div>
              <h2 className="sandbox-title">Test Drive with Live Kirana Data</h2>
              <p className="sandbox-desc">
                Explore an isolated demonstration store with sample customer udhar balances, cash transactions, and voice commands preloaded. No phone number or credit card required.
              </p>
              <div className="sandbox-btn-wrap">
                <button
                  type="button"
                  className="btn btn-gold btn-lg"
                  onClick={onDemoLogin}
                >
                  <Sparkles size={18} />
                  <span>Launch Live Demo Kirana Store</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 9. FINAL HIGH-CONVERSION CTA ────────────────────────────────────── */}
      <section className="landing-final-cta">
        <div className="landing-container text-center">
          <h2 className="final-cta-heading">Ready to Modernize Your Shop's Ledger?</h2>
          <p className="final-cta-subheading">
            Built for India's Kirana Shops across India who have eliminated lost credit, messy paper bahi-khatas, and billing confusion.
          </p>
          <div className="final-cta-actions">
            <button
              type="button"
              className="btn btn-primary btn-lg"
              onClick={onGetStarted}
            >
              <span>Create Shop Account Free</span>
              <ArrowRight size={18} />
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-lg"
              onClick={onSignIn}
            >
              Sign In to Your Store
            </button>
          </div>
        </div>
      </section>

      {/* ── 10. PROFESSIONAL FINTECH FOOTER ─────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="landing-container">
          <div className="footer-top-grid">
            <div className="footer-col brand-col">
              <div className="landing-brand">
                <div className="landing-brand-icon">
                  <Sparkles size={18} color="#FFFFFF" />
                </div>
                <div className="landing-brand-text">
                  <span className="brand-name">BhashaFlow</span>
                  <span className="brand-dot">AI</span>
                </div>
              </div>
              <p className="footer-about">
                The voice-first multilingual digital ledger engineered specifically for India's local retail commerce. Powered by Gnani AI voice intelligence.
              </p>

            </div>

            <div className="footer-col">
              <h4 className="footer-heading">Product</h4>
              <ul className="footer-links">
                <li><a href="#features">Voice Ledger Entry</a></li>
                <li><a href="#ask-ledger">Ask Your Ledger</a></li>
                <li><a href="#how-it-works">Voice Pipeline</a></li>
                <li><button type="button" onClick={onDemoLogin} className="footer-link-btn">Demo Sandbox</button></li>
              </ul>
            </div>

            <div className="footer-col">
              <h4 className="footer-heading">Languages</h4>
              <ul className="footer-links">
                <li><span>Kannada (ಕನ್ನಡ)</span></li>
                <li><span>Hindi (हिन्दी)</span></li>
                <li><span>Tamil (தமிழ்)</span></li>
                <li><span>Telugu (తెలుగు)</span></li>
                <li><span>Urdu, Marathi &amp; More (13 Total)</span></li>
              </ul>
            </div>

            <div className="footer-col">
              <h4 className="footer-heading">Merchant Access</h4>
              <ul className="footer-links">
                <li><button type="button" onClick={onSignIn} className="footer-link-btn">Merchant Sign In</button></li>
                <li><button type="button" onClick={onGetStarted} className="footer-link-btn">Register New Kirana Store</button></li>
                <li><button type="button" onClick={onDemoLogin} className="footer-link-btn">Instant Sandbox Access</button></li>
              </ul>
            </div>
          </div>

          <div className="footer-bottom-bar">
            <div>
              &copy; {new Date().getFullYear()} BhashaFlow AI. All rights reserved.
            </div>
            <div className="footer-credits">
              Voice Intelligence by Gnani AI &bull; Built with pride for Indian Retail
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

