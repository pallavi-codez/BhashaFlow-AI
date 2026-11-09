import React, { useState, useRef, useEffect } from 'react';
import {
  HelpCircle,
  Search,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Users,
  TrendingUp,
  Wallet,
  CreditCard,
  Receipt,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Mic,
  Square,
  X,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { api } from '../services/api';
import { getTranslation } from '../i18n/translations';

const EXAMPLE_QUERIES = [
  'How much does Ramesh owe?',
  'How much credit did I give today?',
  'Who owes me more than ₹1,000?',
  'How much cash did I collect today?',
  'What were my expenses today?',
  'How much did I sell today?',
];

export default function AskLedgerView({ currentLang = 'en-IN', languages = [] }) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // ── Voice Recording State ─────────────────────────────────────────────────
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [voiceNotice, setVoiceNotice] = useState(null);
  const [voiceError, setVoiceError] = useState(null);

  // ── TTS State ─────────────────────────────────────────────────────────────
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [ttsLoading, setTtsLoading] = useState(false);
  const [ttsError, setTtsError] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioPlayerRef = useRef(null);

  const t = (k) => getTranslation(currentLang, k);

  const langConfig = languages?.find((l) => l.code === currentLang) || {
    name: 'English',
    native_name: 'English',
    default_voice: currentLang === 'kn-IN' ? 'Kaveri' : currentLang === 'en-IN' ? 'Deepak' : 'Nalini',
  };
  const voiceName = langConfig.default_voice || (currentLang === 'kn-IN' ? 'Kaveri' : currentLang === 'en-IN' ? 'Deepak' : 'Nalini');

  useEffect(() => {
    // Cleanup media and audio on unmount
    return () => {
      clearInterval(timerRef.current);
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
        audioPlayerRef.current = null;
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  // ── Asking Questions ──────────────────────────────────────────────────────
  async function handleAsk(queryText) {
    const q = (queryText !== undefined ? queryText : query).trim();
    if (!q) return;

    setQuery(q);
    setLoading(true);
    setError(null);
    stopSpeaking();

    try {
      // Calls existing deterministic query processor with authenticated session & selected language
      const resp = await api.askLedger(q, currentLang);
      setResult(resp);
    } catch (err) {
      console.error('Ledger query error:', err);
      setError(err.message || 'Failed to answer ledger question. Please try again.');
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function handleFormSubmit(e) {
    e.preventDefault();
    handleAsk();
  }

  function handleSelectCandidate(candName) {
    const newQuery = `How much does ${candName} owe?`;
    setQuery(newQuery);
    handleAsk(newQuery);
  }

  // ── Voice Input (Gnani Prisma STT) ────────────────────────────────────────
  async function startRecording() {
    setVoiceError(null);
    setVoiceNotice(null);
    stopSpeaking();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      const mimeTypes = [
        'audio/ogg;codecs=opus',
        'audio/ogg',
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/wav',
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
        await processVoiceAudio(audioBlob);
      };

      recorder.start(100);
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Microphone access error:', err);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setVoiceError('Microphone permission was denied. Please allow microphone access in your browser or type your question below.');
      } else {
        setVoiceError(`Could not access microphone: ${err.message}. You can type your question below.`);
      }
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
    }
  }

  function cancelRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      // Discard recorded chunks
      audioChunksRef.current = [];
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
      setRecordingSeconds(0);
      setVoiceNotice('Voice recording cancelled.');
    }
  }

  async function processVoiceAudio(audioBlob) {
    if (!audioBlob || audioBlob.size === 0) {
      setVoiceError('No audio recorded. Please try again.');
      return;
    }

    setIsTranscribing(true);
    setVoiceNotice(`Transcribing speech in ${langConfig.name} with Gnani Prisma STT…`);

    try {
      // Voice input asks a question ONLY — never creates or saves ledger transactions!
      const sttResult = await api.transcribeAudio(audioBlob, currentLang);
      if (!sttResult.success || !sttResult.transcript || !sttResult.transcript.trim()) {
        throw new Error(sttResult.error || 'No speech was detected. Please speak clearly or type your question.');
      }

      const recognizedText = sttResult.transcript.trim();
      // Display the recognized transcript in the input field so user can review or edit it
      setQuery(recognizedText);
      setVoiceNotice(`Recognized: "${recognizedText}". Submitting question to ledger…`);
      setVoiceError(null);

      // Submit recognized question to Ask Your Ledger
      await handleAsk(recognizedText);
    } catch (err) {
      console.warn('STT Error:', err.message);
      setVoiceError(err.message || 'Speech recognition failed. You can still type your question below.');
      setVoiceNotice(null);
    } finally {
      setIsTranscribing(false);
    }
  }

  // ── Voice Output (Gnani Timbre TTS) ───────────────────────────────────────
  async function handleSpeakAnswer() {
    if (!result || !result.answer) return;

    // Stop previous playback if any
    stopSpeaking();
    setTtsLoading(true);
    setTtsError(null);

    try {
      // Extract clean spoken text
      let textToSpeak = result.answer;
      // Strip markdown asterisks or bullet formatting for natural speech
      textToSpeak = textToSpeak.replace(/[*_#•]/g, ' ').replace(/\s+/g, ' ').trim();

      const audioUrl = await api.speakText(textToSpeak, currentLang, voiceName);
      const audio = new Audio(audioUrl);
      audioPlayerRef.current = audio;

      audio.onended = () => {
        setIsSpeaking(false);
      };

      audio.onerror = (e) => {
        console.warn('Audio playback error:', e);
        setIsSpeaking(false);
        setTtsError('Audio playback failed in your browser.');
      };

      await audio.play();
      setIsSpeaking(true);
    } catch (err) {
      console.warn('Gnani TTS error:', err.message);
      setTtsError(`Voice synthesis unavailable: ${err.message}. The full written answer remains visible above.`);
      setIsSpeaking(false);
    } finally {
      setTtsLoading(false);
    }
  }

  function stopSpeaking() {
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current = null;
    }
    setIsSpeaking(false);
  }

  return (
    <div>
      {/* ── Page Header ─────────────────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
          <div style={{
            width: 38,
            height: 38,
            borderRadius: 10,
            background: 'linear-gradient(135deg, #16865A, #123B2A)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#FFFFFF'
          }}>
            <HelpCircle size={22} />
          </div>
          <div>
            <h2 style={{ fontFamily: 'Outfit, sans-serif', fontSize: '1.4rem', fontWeight: 700, margin: 0 }}>
              {t('askLedger')}
            </h2>
            <div style={{ fontSize: '0.8rem', color: '#16865A', fontWeight: 600 }}>
              VOICE &amp; TEXT FINANCIAL INTELLIGENCE &bull; GNANI AI POWERED &bull; ZERO FABRICATION
            </div>
          </div>
        </div>
        <p style={{ fontSize: '0.875rem', color: '#65756B', maxWidth: 700 }}>
          Ask any question about your shop's sales, udhar, cash collections, customer balances, or expenses in your preferred language ({langConfig.native_name} - {langConfig.name}).
          Answers are computed strictly from real database records belonging to your authenticated store.
        </p>
      </div>

      {/* ── Query Input Box ─────────────────────────────────────────────── */}
      <div className="card" style={{ padding: 20, marginBottom: 20, border: '1px solid #E3EAE3', boxShadow: '0 4px 16px rgba(18,59,42,0.04)' }}>
        <form onSubmit={handleFormSubmit} style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: 260 }}>
            <div style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: '#94A3B8' }}>
              <Search size={18} />
            </div>
            <input
              type="text"
              className="input-field"
              style={{ paddingLeft: 42, width: '100%', height: 46, fontSize: '0.95rem' }}
              placeholder={isRecording ? `Listening in ${langConfig.name}…` : `Ask in ${langConfig.name} (e.g., How much does Ramesh owe? / ರಮೇಶ್ ಎಷ್ಟು ಕೊಡಬೇಕು?)`}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={loading || isTranscribing}
              aria-label="Ask Your Ledger question input"
              autoFocus
            />
          </div>

          {/* Voice Input Trigger */}
          <button
            type="button"
            className={`btn ${isRecording ? 'btn-danger' : 'btn-secondary'}`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={loading || isTranscribing}
            aria-label={isRecording ? "Stop voice recording" : "Record voice question"}
            title={isRecording ? "Stop voice recording" : `Speak question in ${langConfig.name}`}
            style={{
              height: 46,
              padding: '0 16px',
              borderRadius: 10,
              border: isRecording ? '2px solid #D94B4B' : '1px solid #16865A',
              background: isRecording ? '#FEE2E2' : '#DDF4E6',
              color: isRecording ? '#D94B4B' : '#123B2A',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {isRecording ? <Square size={16} color="#D94B4B" /> : <Mic size={18} color="#16865A" />}
            <span>{isRecording ? "Stop" : "Speak"}</span>
          </button>

          {/* Ask Button */}
          <button
            type="submit"
            className="btn btn-primary"
            style={{ height: 46, padding: '0 24px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}
            disabled={loading || isTranscribing || !query.trim()}
            aria-label="Submit financial question"
          >
            {loading ? (
              <>
                <RefreshCw size={16} className="spin" />
                <span>Calculating...</span>
              </>
            ) : (
              <>
                <Sparkles size={16} />
                <span>Ask Ledger</span>
              </>
            )}
          </button>
        </form>

        {/* Voice Recording / Transcribing Indicator Banner */}
        {isRecording && (
          <div style={{
            marginTop: 14,
            padding: '12px 16px',
            background: '#FEF2F2',
            border: '1px solid #FCA5A5',
            borderRadius: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 10
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                background: '#EF4444',
                boxShadow: '0 0 10px #EF4444',
                animation: 'pulse 1s infinite'
              }} />
              <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#991B1B' }}>
                Listening in {langConfig.native_name} ({langConfig.name}) &bull; 00:{recordingSeconds < 10 ? `0${recordingSeconds}` : recordingSeconds}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                type="button"
                onClick={stopRecording}
                className="btn btn-danger btn-sm"
                style={{ borderRadius: 6, padding: '4px 12px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 4 }}
              >
                <Square size={13} />
                <span>Stop &amp; Submit</span>
              </button>
              <button
                type="button"
                onClick={cancelRecording}
                className="btn btn-secondary btn-sm"
                style={{ borderRadius: 6, padding: '4px 10px', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 4, background: '#FFFFFF' }}
              >
                <X size={13} />
                <span>Cancel</span>
              </button>
            </div>
          </div>
        )}

        {isTranscribing && (
          <div style={{
            marginTop: 14,
            padding: '10px 16px',
            background: '#EFF6FF',
            border: '1px solid #BFDBFE',
            borderRadius: 10,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            fontSize: '0.85rem',
            color: '#1E40AF'
          }}>
            <RefreshCw size={16} className="spin" color="#2563EB" />
            <span>Processing speech with Gnani Prisma STT ({langConfig.name})…</span>
          </div>
        )}

        {voiceNotice && !isRecording && !isTranscribing && (
          <div style={{
            marginTop: 12,
            padding: '8px 14px',
            background: '#ECFDF5',
            border: '1px solid #A7F3D0',
            borderRadius: 8,
            fontSize: '0.825rem',
            color: '#065F46',
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <span>🎙️</span>
            <span>{voiceNotice}</span>
          </div>
        )}

        {voiceError && (
          <div style={{
            marginTop: 12,
            padding: '10px 14px',
            background: '#FEF2F2',
            border: '1px solid #FECACA',
            borderRadius: 8,
            fontSize: '0.85rem',
            color: '#991B1B',
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            <AlertCircle size={16} color="#DC2626" style={{ flexShrink: 0 }} />
            <span>{voiceError}</span>
          </div>
        )}

        {/* Suggested Quick Queries */}
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#64748B', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Example Questions (Click to Ask)
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {EXAMPLE_QUERIES.map((eq, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleAsk(eq)}
                disabled={loading || isRecording}
                style={{
                  background: query === eq ? '#ECFDF5' : '#F8FAFC',
                  color: query === eq ? '#065F46' : '#334155',
                  border: query === eq ? '1px solid #10B981' : '1px solid #E2E8F0',
                  borderRadius: 20,
                  padding: '6px 14px',
                  fontSize: '0.82rem',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                <span>💡</span>
                <span>{eq}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Loading State ───────────────────────────────────────────────── */}
      {loading && (
        <div className="card" style={{ padding: '36px 20px', textAlign: 'center', background: '#F8FAFC' }}>
          <div style={{
            width: 44,
            height: 44,
            borderRadius: '50%',
            background: '#ECFDF5',
            color: '#10B981',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 14px'
          }}>
            <RefreshCw size={22} className="spin" />
          </div>
          <div style={{ fontSize: '1rem', fontWeight: 600, color: '#1E293B', marginBottom: 4 }}>
            Auditing Immutable Ledger Records...
          </div>
          <p style={{ fontSize: '0.85rem', color: '#64748B', maxWidth: 450, margin: '0 auto' }}>
            Aggregating confirmed transactions and computing exact decimal sums for your shop.
          </p>
        </div>
      )}

      {/* ── Error State ─────────────────────────────────────────────────── */}
      {error && !loading && (
        <div style={{
          padding: 16,
          background: '#FEF2F2',
          border: '1px solid #FCA5A5',
          borderRadius: 12,
          marginBottom: 20,
          display: 'flex',
          alignItems: 'flex-start',
          gap: 12
        }}>
          <AlertCircle size={20} color="#DC2626" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <div style={{ fontWeight: 600, color: '#991B1B', fontSize: '0.9rem' }}>Query Failed</div>
            <p style={{ fontSize: '0.85rem', color: '#B91C1C', marginTop: 4 }}>{error}</p>
            <button
              onClick={() => handleAsk()}
              className="btn btn-secondary btn-sm"
              style={{ marginTop: 8, background: '#FFFFFF', borderColor: '#FCA5A5', color: '#991B1B' }}
            >
              Try Again
            </button>
          </div>
        </div>
      )}

      {/* ── Answer Area ─────────────────────────────────────────────────── */}
      {result && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Primary Answer Card */}
          <div className="card" style={{
            padding: 24,
            background: '#FFFFFF',
            border: result.no_records ? '1px solid #E3EAE3' : '1px solid #DDF4E6',
            boxShadow: '0 4px 18px rgba(18, 59, 42, 0.06)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, marginBottom: 14, flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 34,
                  height: 34,
                  borderRadius: '50%',
                  background: result.no_records ? '#F8FAF8' : '#DDF4E6',
                  color: result.no_records ? '#65756B' : '#16865A',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {result.no_records ? <AlertCircle size={18} /> : <CheckCircle2 size={18} />}
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#65756B', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                    Intent: {result.intent.replace(/_/g, ' ')}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#202923', fontStyle: 'italic' }}>
                    "{result.query}"
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {/* Gnani Timbre TTS Speaker Button */}
                <button
                  type="button"
                  onClick={isSpeaking ? stopSpeaking : handleSpeakAnswer}
                  disabled={ttsLoading}
                  className="btn btn-secondary btn-sm"
                  aria-label={isSpeaking ? "Stop spoken answer" : "Speak answer aloud with Gnani Timbre TTS"}
                  title={isSpeaking ? "Stop speech" : `Read aloud in ${langConfig.name}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    background: isSpeaking ? '#FEE2E2' : '#DDF4E6',
                    borderColor: isSpeaking ? '#F87171' : '#16865A',
                    color: isSpeaking ? '#D94B4B' : '#123B2A',
                    fontWeight: 600,
                    borderRadius: 8
                  }}
                >
                  {ttsLoading ? (
                    <>
                      <RefreshCw size={14} className="spin" />
                      <span>Synthesizing...</span>
                    </>
                  ) : isSpeaking ? (
                    <>
                      <VolumeX size={15} />
                      <span>Stop Speaking</span>
                    </>
                  ) : (
                    <>
                      <Volume2 size={15} />
                      <span>Read Aloud ({voiceName})</span>
                    </>
                  )}
                </button>

                {result.amount !== null && result.amount !== undefined && (
                  <div style={{
                    background: '#DDF4E6',
                    border: '1px solid #16865A',
                    borderRadius: 12,
                    padding: '6px 16px',
                    textAlign: 'right'
                  }}>
                    <div style={{ fontSize: '0.7rem', color: '#123B2A', fontWeight: 700, textTransform: 'uppercase' }}>
                      Calculated Total
                    </div>
                    <div style={{ fontSize: '1.25rem', fontWeight: 800, color: '#123B2A' }}>
                      ₹{Number(result.amount).toFixed(2)}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Answer Text */}
            <div style={{
              fontSize: '1.1rem',
              fontWeight: 600,
              color: '#0F172A',
              lineHeight: 1.6,
              background: '#F8FAFC',
              padding: '16px 20px',
              borderRadius: 10,
              borderLeft: '4px solid #10B981',
              whiteSpace: 'pre-line'
            }}>
              {result.answer}
            </div>

            {/* Recoverable TTS Error Notice (leaves written answer visible) */}
            {ttsError && (
              <div style={{
                marginTop: 10,
                padding: '8px 12px',
                background: '#FEF2F2',
                border: '1px solid #FECACA',
                borderRadius: 8,
                fontSize: '0.8rem',
                color: '#991B1B',
                display: 'flex',
                alignItems: 'center',
                gap: 8
              }}>
                <AlertCircle size={14} color="#DC2626" style={{ flexShrink: 0 }} />
                <span>{ttsError}</span>
              </div>
            )}

            {/* Ambiguity Resolution / Candidates */}
            {result.clarification_needed && result.candidates?.length > 0 && (
              <div style={{ marginTop: 18, padding: 16, background: '#FFFBEB', borderRadius: 10, border: '1px solid #FDE68A' }}>
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#92400E', marginBottom: 8 }}>
                  Did you mean one of these customers?
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                  {result.candidates.map((cand, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSelectCandidate(cand)}
                      style={{
                        background: '#FFFFFF',
                        border: '1px solid #F59E0B',
                        color: '#92400E',
                        borderRadius: 20,
                        padding: '6px 14px',
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 6
                      }}
                    >
                      <Users size={14} />
                      <span>{cand}</span>
                      <ArrowRight size={14} />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Detailed Item Breakdown (When available) */}
          {result.details && result.details.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">
                  Detailed Breakdown ({result.details.length} item{result.details.length > 1 ? 's' : ''})
                </h3>
                <span className="badge badge-cash">Verified Isolated Records</span>
              </div>

              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Name / Item</th>
                      <th>Category / Role</th>
                      <th>Date / Time</th>
                      <th style={{ textAlign: 'right' }}>Amount</th>
                      <th>Extra Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.details.map((item, idx) => (
                      <tr key={idx}>
                        <td style={{ fontWeight: 600, color: '#1E293B' }}>
                          {item.name || 'Ledger Entry'}
                        </td>
                        <td>
                          <span className={`badge ${
                            item.type === 'debt' || item.type === 'CREDIT_SALE' ? 'badge-credit' :
                            item.type === 'CASH_SALE' ? 'badge-cash' :
                            item.type === 'PAYMENT' ? 'badge-payment' :
                            item.type === 'expense' ? 'badge-expense' : 'badge-demo'
                          }`}>
                            {item.type || 'Entry'}
                          </span>
                        </td>
                        <td style={{ color: '#64748B', whiteSpace: 'nowrap' }}>
                          {item.date || 'Today'}
                        </td>
                        <td style={{ fontWeight: 700, fontSize: '0.95rem', textAlign: 'right' }}>
                          {item.amount !== null && item.amount !== undefined
                            ? `₹${Number(item.amount).toFixed(2)}`
                            : '—'}
                        </td>
                        <td style={{ color: '#64748B', fontSize: '0.85rem' }}>
                          {item.extra || '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Accounting Integrity Note ─────────────────────────────────────── */}
      <div style={{
        marginTop: 24,
        padding: '14px 18px',
        background: '#F0FDF4',
        border: '1px solid #BBF7D0',
        borderRadius: 10,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        fontSize: '0.85rem',
        color: '#166534'
      }}>
        <ShieldCheck size={20} color="#16A34A" style={{ flexShrink: 0 }} />
        <div>
          <strong>Authoritative Accounting Rules:</strong> Total sales = Credit Sales (Udhar) + Counter Cash Sales.
          Debt repayments collected from customers decrease debt and add to cash collected, but are <em>never</em> counted as new sales.
          All calculations are decimal-exact without float rounding.
        </div>
      </div>
    </div>
  );
}
