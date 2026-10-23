"""
Gnani AI Timbre — Text-to-Speech (REST).

Endpoint: POST https://api.vachana.ai/api/v1/tts/inference
Auth:     X-API-Key-ID header
Body:     JSON
Response: Raw WAV audio bytes (200 OK)

Voices for timbre-v2.5: Nalini, Kaveri, Deepak, …
Voices for timbre-v3.0: Shivani, Avinash, Lakshmi, …
"""
from __future__ import annotations

import logging

import httpx

from ..config import get_settings

logger = logging.getLogger(__name__)

_TTS_URL = "https://api.vachana.ai/api/v1/tts/inference"

# Default audio config: WAV, 48 kHz, mono, 16-bit PCM — browser-playable
_DEFAULT_AUDIO_CONFIG = {
    "sample_rate":  48000,
    "num_channels": 1,
    "sample_width": 2,
    "encoding":     "linear_pcm",
    "container":    "wav",
}

# Documented voices per model (from official voice catalog)
TIMBRE_V25_VOICES = ["Nalini", "Kaveri", "Deepak"]
TIMBRE_V30_VOICES = ["Shivani", "Avinash", "Lakshmi"]


class GnaniTTSError(Exception):
    """Raised when Gnani TTS fails. Callers must NOT synthesise fake audio."""


async def synthesize(
    text: str,
    voice: str = "Kaveri",
    model: str = "timbre-v2.5",
    language: str = "kn-IN",
    speed: float = 1.0,
) -> bytes:
    """
    Call Gnani Timbre TTS and return raw WAV bytes.

    Raises GnaniTTSError on any failure.
    """
    settings = get_settings()
    if not settings.gnani_api_key:
        raise GnaniTTSError(
            "GNANI_API_KEY is not configured. "
            "Set it in backend/.env before using text-to-speech."
        )

    if not text.strip():
        raise GnaniTTSError("TTS text cannot be empty.")

    headers = {
        "Content-Type": "application/json",
        "X-API-Key-ID": settings.gnani_api_key,
    }
    payload = {
        "text":         text,
        "voice":        voice,
        "model":        model,
        "language":     language,
        "speed":        speed,
        "audio_config": _DEFAULT_AUDIO_CONFIG,
    }

    try:
        async with httpx.AsyncClient(timeout=settings.gnani_timeout_seconds) as client:
            response = await client.post(_TTS_URL, headers=headers, json=payload)
    except httpx.TimeoutException as exc:
        raise GnaniTTSError(f"Gnani TTS request timed out after {settings.gnani_timeout_seconds}s") from exc
    except httpx.RequestError as exc:
        raise GnaniTTSError(f"Gnani TTS network error: {exc}") from exc

    if response.status_code == 401:
        raise GnaniTTSError("Gnani TTS: Invalid or missing API key (401 Unauthorized).")
    if response.status_code == 400:
        raise GnaniTTSError(
            f"Gnani TTS: Bad request — check voice/model/language combination. "
            f"Detail: {response.text[:300]}"
        )
    if response.status_code == 429:
        raise GnaniTTSError("Gnani TTS: Rate limit exceeded. Please try again later.")
    if response.status_code >= 500:
        raise GnaniTTSError(f"Gnani TTS: Server error ({response.status_code}).")
    if response.status_code != 200:
        raise GnaniTTSError(f"Gnani TTS error {response.status_code}: {response.text[:300]}")

    audio_bytes = response.content
    if len(audio_bytes) < 44:  # WAV header is 44 bytes minimum
        raise GnaniTTSError("Gnani TTS returned suspiciously small audio data.")

    return audio_bytes
