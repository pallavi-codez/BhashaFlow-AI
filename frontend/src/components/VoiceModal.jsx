import React, { useState, useRef, useEffect } from 'react';
import { 
  Mic, 
  Square, 
  X, 
  CheckCircle2, 
  AlertTriangle, 
  RefreshCw, 
  ArrowRight, 
  User, 
  DollarSign, 
  FileText, 
  Sparkles,
  Volume2
} from 'lucide-react';
import { api } from '../services/api';
import { getTranslation } from '../i18n/translations';
import TtsPlayer from './TtsPlayer';

export default function VoiceModal({ isOpen, onClose, currentLang, languages, onTransactionComplete }) {
  const [stage, setStage] = useState('idle'); // idle | recording | transcribing | parsing | review | saving | success | error
  const [selectedLang, setSelectedLang] = useState(currentLang || 'kn-IN');
  const [transcript, setTranscript] = useState('');
  const [parsedData, setParsedData] = useState({
    txn_type: 'CREDIT_SALE',
    customer_name: '',
    amount: '',
    note: '',
    ambiguous: false,
    ambiguity_reason: null,
  });
  const [errorMessage, setErrorMessage] = useState('');
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [audioUrl, setAudioUrl] = useState(null);
  const [ttsAudioUrl, setTtsAudioUrl] = useState(null);
  const [spokenText, setSpokenText] = useState('');
  const [customers, setCustomers] = useState([]);
  const [existingCustomer, setExistingCustomer] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  const t = (k) => getTranslation(selectedLang, k);

  useEffect(() => {
    setSelectedLang(currentLang || 'kn-IN');
  }, [currentLang]);

  useEffect(() => {
    if (isOpen) {
      resetState();
      loadCustomers();
    }
  }, [isOpen]);

  async function loadCustomers() {
    try {
      const list = await api.listCustomers();
      setCustomers(list);
    } catch {
      // ignore
    }
  }

  function resetState() {
    setStage('idle');
    setTranscript('');
    setParsedData({
      txn_type: 'CREDIT_SALE',
      customer_name: '',
      amount: '',
      note: '',
      ambiguous: false,
      ambiguity_reason: null,
    });
    setErrorMessage('');
    setRecordingSeconds(0);
    setAudioUrl(null);
    setTtsAudioUrl(null);
    setSpokenText('');
    setExistingCustomer(null);
    audioChunksRef.current = [];
    clearInterval(timerRef.current);
  }

  // ── Microphone Recording ──────────────────────────────────────────────────
  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      // Determine supported mime type
      const mimeTypes = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4',
        'audio/wav'
      ];
      let selectedMime = '';
      for (const m of mimeTypes) {
        if (MediaRecorder.isTypeSupported(m)) {
          selectedMime = m;
          break;
        }
      }

      const recorder = new MediaRecorder(stream, selectedMime ? { mimeType: selectedMime } : undefined);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: recorder.mimeType || 'audio/webm' });
        const localUrl = URL.createObjectURL(audioBlob);
        setAudioUrl(localUrl);
        await processAudio(audioBlob);
      };

      recorder.start(100);
      setStage('recording');
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error(err);
      setErrorMessage(
        'Could not access microphone. Please ensure microphone permissions are granted in your browser.'
      );
      setStage('error');
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      clearInterval(timerRef.current);
    }
  }

  // ── Call Gnani Prisma STT ─────────────────────────────────────────────────
  async function processAudio(blob) {
    setStage('transcribing');
    setErrorMessage('');
    try {
      const sttResult = await api.transcribeAudio(blob, selectedLang);
      if (!sttResult.success || !sttResult.transcript) {
        throw new Error(sttResult.error || 'No speech detected.');
      }
      setTranscript(sttResult.transcript);
      await parseTranscriptText(sttResult.transcript);
    } catch (err) {
      setErrorMessage(err.message || 'Speech recognition failed.');
      setStage('error');
    }
  }

  // ── Parse Transcript ──────────────────────────────────────────────────────
  async function parseTranscriptText(text) {
    setStage('parsing');
    try {
      const parsed = await api.parseTranscript(text, selectedLang);
      setTranscript(text);
      setParsedData({
        txn_type: parsed.txn_type || 'CREDIT_SALE',
        customer_name: parsed.customer_name || '',
        amount: parsed.amount ? String(parsed.amount) : '',
        note: parsed.note || (parsed.ambiguous ? parsed.ambiguity_reason : ''),
        ambiguous: parsed.ambiguous,
        ambiguity_reason: parsed.ambiguity_reason,
      });

      // Match against existing customer list
      if (parsed.customer_name) {
        const found = customers.find(
          (c) => c.name.toLowerCase() === parsed.customer_name.toLowerCase()
        );
        setExistingCustomer(found || null);
      }

      setStage('review');
    } catch (err) {
      setErrorMessage('Failed to parse transaction.');
      setStage('error');
    }
  }

  // ── Direct Demo Simulation (No live mic required) ─────────────────────────
  function handleUseSample(sampleText) {
    setTranscript(sampleText);
    parseTranscriptText(sampleText);
  }

  // ── Save & Confirm to DB ──────────────────────────────────────────────────
  async function handleConfirmAndSave() {
    if (!parsedData.amount || Number(parsedData.amount) <= 0) {
      alert('Please enter a valid amount greater than zero.');
      return;
    }

    if (
      (parsedData.txn_type === 'CREDIT_SALE' || parsedData.txn_type === 'PAYMENT') &&
      !parsedData.customer_name.trim()
    ) {
      alert('Customer name is required for credit sales and payments.');
      return;
    }

    setStage('saving');
    try {
      let customerId = existingCustomer?.id || null;

      // If customer doesn't exist yet and it's credit/payment, create customer first
      if (!customerId && parsedData.customer_name.trim()) {
        const newCust = await api.createCustomer({
          name: parsedData.customer_name.trim(),
        });
        customerId = newCust.id;
        setExistingCustomer(newCust);
      }

      // Generate idempotency key for duplicate submission prevention
      const idempotencyKey = `voice_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

      // 1. Create Pending Transaction
      const pendingTxn = await api.createPendingTransaction({
        customer_id: customerId,
        txn_type: parsedData.txn_type,
        amount: Number(parsedData.amount),
        note: parsedData.note || 'Voice transaction',
        source: 'voice',
        transcript: transcript,
        idempotency_key: idempotencyKey,
      });

      // 2. Explicit User Confirmation
      await api.confirmTransaction(pendingTxn.id, idempotencyKey);

      // 3. Spoken Confirmation via Gnani Timbre TTS
      let confirmationPhrase = '';
      const amtStr = `₹${parsedData.amount}`;
      const cName = parsedData.customer_name || 'Customer';

      if (parsedData.txn_type === 'CREDIT_SALE') {
        confirmationPhrase = `${cName}, ${amtStr} credit recorded.`;
      } else if (parsedData.txn_type === 'PAYMENT') {
        confirmationPhrase = `${cName}, ${amtStr} payment received.`;
      } else if (parsedData.txn_type === 'CASH_SALE') {
        confirmationPhrase = `Cash sale ${amtStr} recorded.`;
      } else {
        confirmationPhrase = `Shop expense ${amtStr} recorded.`;
      }

      setSpokenText(confirmationPhrase);

      // Synthesize audio using Gnani Timbre
      try {
        const langConfig = languages.find((l) => l.code === selectedLang);
        const voice = langConfig?.default_voice || 'Kaveri';
        const ttsUrl = await api.speakText(confirmationPhrase, selectedLang, voice);
        setTtsAudioUrl(ttsUrl);
      } catch (ttsErr) {
        console.warn('Gnani TTS note:', ttsErr.message);
      }

      setStage('success');
      if (onTransactionComplete) {
        onTransactionComplete();
      }
    } catch (err) {
      setErrorMessage(err.message || 'Failed to save transaction');
      setStage('error');
    }
  }

  if (!isOpen) return null;

  const currentLangConfig = languages.find((l) => l.code === selectedLang) || {
    name: 'Kannada',
    sample_phrase: 'Ramesh ge 500 rupees udhar haaku',
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content" style={{ maxWidth: '640px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36,
              height: 36,
              borderRadius: '50%',
              background: '#EBF3FC',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#1E6FCC'
            }}>
              <Mic size={20} />
            </div>
            <div>
              <h2 className="modal-title" style={{ fontSize: '1.25rem' }}>{t('recordTransaction')}</h2>
              <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                Gnani Prisma STT &amp; Timbre TTS Powered
              </div>
            </div>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Language Selector inside Modal */}
        <div style={{ marginBottom: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#F8FAFC', padding: '10px 14px', borderRadius: '12px' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#334155' }}>
            Spoken Language:
          </span>
          <select
            className="form-select"
            style={{ width: 'auto', padding: '6px 12px', fontSize: '0.85rem' }}
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
          >
            {languages.map((l) => (
              <option key={l.code} value={l.code}>
                {l.native_name} — {l.name}
              </option>
            ))}
          </select>
        </div>

        {/* ── STAGE 1: IDLE / RECORDING ────────────────────────────────────────── */}
        {(stage === 'idle' || stage === 'recording') && (
          <div className="recording-box">
            <button
              className={`mic-hero-button ${stage === 'recording' ? 'is-recording' : ''}`}
              onClick={stage === 'recording' ? stopRecording : startRecording}
              title={stage === 'recording' ? 'Click to Stop' : 'Click to Speak'}
            >
              {stage === 'recording' ? <Square size={36} /> : <Mic size={40} />}
            </button>

            {stage === 'recording' ? (
              <>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#EF4444' }}>
                  {t('listening')}
                </div>
                <div style={{ fontSize: '0.9rem', color: '#64748B', marginTop: 4 }}>
                  00:{recordingSeconds < 10 ? `0${recordingSeconds}` : recordingSeconds}
                </div>
                <div className="waveform-container">
                  <div className="waveform-bar" />
                  <div className="waveform-bar" />
                  <div className="waveform-bar" />
                  <div className="waveform-bar" />
                  <div className="waveform-bar" />
                  <div className="waveform-bar" />
                  <div className="waveform-bar" />
                  <div className="waveform-bar" />
                </div>
                <button
                  onClick={stopRecording}
                  className="btn btn-danger btn-sm"
                  style={{ marginTop: 12, borderRadius: '9999px' }}
                >
                  <Square size={14} /> Stop &amp; Transcribe
                </button>
              </>
            ) : (
              <>
                <div style={{ fontSize: '1.05rem', fontWeight: 600, color: '#0F172A' }}>
                  Tap microphone to speak
                </div>
                <div style={{ fontSize: '0.85rem', color: '#64748B', maxWidth: 420, marginTop: 4 }}>
                  Speak natural Kirana ledger commands like credit sales, debt payments, or cash.
                </div>

                {/* Sample Phrases for testing */}
                <div style={{ marginTop: 24, textAlign: 'left', width: '100%' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', marginBottom: 8 }}>
                    Sample test commands ({currentLangConfig.name}):
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div
                      className="sample-chip"
                      style={{ color: '#0F172A', background: '#F1F5F9' }}
                      onClick={() => handleUseSample(currentLangConfig.sample_phrase)}
                    >
                      🗣️ "{currentLangConfig.sample_phrase}"
                    </div>
                    <div
                      className="sample-chip"
                      style={{ color: '#0F172A', background: '#F1F5F9' }}
                      onClick={() => handleUseSample('Ramesh paid 200 rupees')}
                    >
                      🗣️ "Ramesh paid 200 rupees" (Payment)
                    </div>
                    <div
                      className="sample-chip"
                      style={{ color: '#0F172A', background: '#F1F5F9' }}
                      onClick={() => handleUseSample('Cash sale 300 rupees')}
                    >
                      🗣️ "Cash sale 300 rupees" (Cash Sale)
                    </div>
                  </div>
                </div>
              </>
            )}
          </div>
        )}

        {/* ── STAGE 2: PROCESSING (Gnani Prisma STT) ───────────────────────────── */}
        {(stage === 'transcribing' || stage === 'parsing' || stage === 'saving') && (
          <div style={{ padding: '40px 20px', textAlign: 'center' }}>
            <div style={{
              width: 54,
              height: 54,
              margin: '0 auto 16px',
              border: '4px solid #E2E8F0',
              borderTopColor: '#1E6FCC',
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite'
            }} />
            <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#0F172A' }}>
              {stage === 'transcribing' ? 'Gnani Prisma STT Transcribing…' : stage === 'parsing' ? 'Language Parsing…' : 'Saving to Immutable Ledger…'}
            </div>
            <div style={{ fontSize: '0.85rem', color: '#64748B', marginTop: 4 }}>
              Connecting to real Gnani AI endpoints without simulation.
            </div>
          </div>
        )}

        {/* ── STAGE 3: EDITABLE CONFIRMATION REVIEW ────────────────────────────── */}
        {stage === 'review' && (
          <div>
            {/* Transcript Preview */}
            <div style={{
              background: '#F8FAFC',
              border: '1px solid #E2E8F0',
              borderRadius: '12px',
              padding: '12px 16px',
              marginBottom: 16
            }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#1E6FCC', textTransform: 'uppercase' }}>
                Gnani Prisma Transcript
              </div>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: '#0F172A', marginTop: 4 }}>
                "{transcript}"
              </div>
            </div>

            {parsedData.ambiguous && (
              <div style={{
                background: '#FEF3C7',
                border: '1px solid #F59E0B',
                borderRadius: '10px',
                padding: '10px 14px',
                marginBottom: 16,
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                fontSize: '0.85rem',
                color: '#92400E'
              }}>
                <AlertTriangle size={18} flexShrink={0} />
                <div>
                  <strong>Clarification needed:</strong> {parsedData.ambiguity_reason || 'Please verify missing details below.'}
                </div>
              </div>
            )}

            {/* Editable Confirmation Form */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <div className="form-group" style={{ gridColumn: 'span 2' }}>
                <label className="form-label">{t('type')}</label>
                <select
                  className="form-select"
                  value={parsedData.txn_type}
                  onChange={(e) => setParsedData({ ...parsedData, txn_type: e.target.value })}
                >
                  <option value="CREDIT_SALE">🔴 Udhar / Credit Given (Customer Debt Increases)</option>
                  <option value="PAYMENT">🟢 Payment Received (Customer Debt Decreases)</option>
                  <option value="CASH_SALE">🔵 Cash Sale (Immediate Cash In Hand)</option>
                  <option value="EXPENSE">🟣 Shop Expense (Outflow)</option>
                </select>
              </div>

              {(parsedData.txn_type === 'CREDIT_SALE' || parsedData.txn_type === 'PAYMENT') && (
                <div className="form-group">
                  <label className="form-label">{t('customer')}</label>
                  <input
                    type="text"
                    className="form-input"
                    placeholder="Customer Name (e.g. Ramesh)"
                    value={parsedData.customer_name}
                    onChange={(e) => {
                      const val = e.target.value;
                      setParsedData({ ...parsedData, customer_name: val });
                      const found = customers.find(c => c.name.toLowerCase() === val.toLowerCase());
                      setExistingCustomer(found || null);
                    }}
                  />
                  {existingCustomer ? (
                    <div style={{ fontSize: '0.75rem', color: '#059669', marginTop: 4 }}>
                      ✓ Existing Customer (Current Udhar: ₹{existingCustomer.outstanding_balance})
                    </div>
                  ) : parsedData.customer_name ? (
                    <div style={{ fontSize: '0.75rem', color: '#1E6FCC', marginTop: 4 }}>
                      + New Customer will be created automatically
                    </div>
                  ) : null}
                </div>
              )}

              <div className="form-group" style={parsedData.txn_type === 'CASH_SALE' || parsedData.txn_type === 'EXPENSE' ? { gridColumn: 'span 2' } : {}}>
                <label className="form-label">{t('amount')}</label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  className="form-input"
                  placeholder="0.00"
                  value={parsedData.amount}
                  onChange={(e) => setParsedData({ ...parsedData, amount: e.target.value })}
                />
              </div>

              <div className="form-group" style={{ gridColumn: 'span 2' }}>
                <label className="form-label">{t('note')}</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Rice, dal, monthly goods"
                  value={parsedData.note}
                  onChange={(e) => setParsedData({ ...parsedData, note: e.target.value })}
                />
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, marginTop: 20 }}>
              <button
                className="btn btn-secondary"
                style={{ flex: 1 }}
                onClick={resetState}
              >
                <RefreshCw size={16} /> Re-record
              </button>
              <button
                className="btn btn-primary"
                style={{ flex: 2 }}
                onClick={handleConfirmAndSave}
              >
                <CheckCircle2 size={18} /> {t('confirmAndSave')}
              </button>
            </div>
          </div>
        )}

        {/* ── STAGE 4: SUCCESS & SPOKEN RECEIPT ────────────────────────────────── */}
        {stage === 'success' && (
          <div style={{ textAlign: 'center', padding: '24px 10px' }}>
            <div style={{
              width: 64,
              height: 64,
              borderRadius: '50%',
              background: '#ECFDF5',
              color: '#10B981',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px'
            }}>
              <CheckCircle2 size={38} />
            </div>

            <h3 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.4rem', fontWeight: 700, color: '#0F172A' }}>
              Transaction Successfully Saved!
            </h3>
            <p style={{ fontSize: '0.9rem', color: '#64748B', marginTop: 4 }}>
              Ledger entry is recorded permanently and balances have been updated.
            </p>

            {/* Spoken Audio Player */}
            {ttsAudioUrl && (
              <div style={{ marginTop: 20, textAlign: 'left' }}>
                <TtsPlayer
                  audioUrl={ttsAudioUrl}
                  confirmationText={spokenText}
                  voiceName={languages.find(l => l.code === selectedLang)?.default_voice || 'Kaveri'}
                />
              </div>
            )}

            <div style={{ display: 'flex', gap: 12, marginTop: 24, justifyContent: 'center' }}>
              <button
                className="btn btn-secondary"
                onClick={resetState}
              >
                <Mic size={16} /> Record Another
              </button>
              <button
                className="btn btn-primary"
                onClick={onClose}
              >
                Done / View Dashboard
              </button>
            </div>
          </div>
        )}

        {/* ── STAGE 5: ERROR STATE ────────────────────────────────────────────── */}
        {stage === 'error' && (
          <div style={{ textAlign: 'center', padding: '28px 10px' }}>
            <div style={{
              width: 54,
              height: 54,
              borderRadius: '50%',
              background: '#FEE2E2',
              color: '#EF4444',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px'
            }}>
              <AlertTriangle size={32} />
            </div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#991B1B' }}>
              Voice Processing Notice
            </h3>
            <p style={{ fontSize: '0.875rem', color: '#64748B', maxWidth: 460, margin: '8px auto 20px' }}>
              {errorMessage}
            </p>

            <div style={{ display: 'flex', gap: 10, justifyContent: 'center' }}>
              <button className="btn btn-secondary" onClick={resetState}>
                <RefreshCw size={16} /> Try Again
              </button>
              <button
                className="btn btn-primary"
                onClick={() => {
                  setStage('review');
                  setParsedData({
                    txn_type: 'CREDIT_SALE',
                    customer_name: '',
                    amount: '',
                    note: '',
                    ambiguous: false,
                    ambiguity_reason: null,
                  });
                }}
              >
                Enter Manually Instead
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
