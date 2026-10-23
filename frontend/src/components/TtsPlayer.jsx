import React, { useState, useRef, useEffect } from 'react';
import { Volume2, Play, Pause, RotateCcw } from 'lucide-react';

export default function TtsPlayer({ audioUrl, confirmationText, voiceName = 'Kaveri' }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  useEffect(() => {
    // Autoplay when new audio URL arrives
    if (audioUrl && audioRef.current) {
      audioRef.current.currentTime = 0;
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {
        // Autoplay may be blocked by browser policy until user interacts
        setIsPlaying(false);
      });
    }
  }, [audioUrl]);

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  };

  const handleReplay = () => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = 0;
    audioRef.current.play().then(() => setIsPlaying(true)).catch(() => {});
  };

  return (
    <div className="tts-player-card">
      <audio
        ref={audioRef}
        src={audioUrl}
        onEnded={() => setIsPlaying(false)}
        style={{ display: 'none' }}
      />

      <div className="tts-avatar">
        <Volume2 size={22} />
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: '#065F46', textTransform: 'uppercase' }}>
          GNANI TIMBRE SPOKEN RECEIPT ({voiceName})
        </div>
        <div style={{ fontSize: '0.9rem', color: '#0F172A', fontWeight: 600, marginTop: 2 }}>
          "{confirmationText}"
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <button
          onClick={togglePlay}
          className="btn btn-sm btn-success"
          style={{ padding: '8px 14px', borderRadius: '9999px' }}
          title={isPlaying ? 'Pause' : 'Play Spoken Confirmation'}
        >
          {isPlaying ? <Pause size={16} /> : <Play size={16} />}
          <span>{isPlaying ? 'Pause' : 'Play'}</span>
        </button>

        <button
          onClick={handleReplay}
          className="btn btn-sm btn-secondary"
          style={{ padding: '8px', borderRadius: '50%' }}
          title="Replay Voice Receipt"
        >
          <RotateCcw size={16} />
        </button>
      </div>
    </div>
  );
}
