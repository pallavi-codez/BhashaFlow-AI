"""
Gnani AI Prisma — Speech-to-Text (REST v3).

Endpoint: POST https://api.vachana.ai/stt/v3
Auth:     X-API-Key-ID header
Body:     multipart/form-data
  - audio_file       (bytes)
  - language_code    e.g. kn-IN
  - format           "transcribe" (with ITN) | "verbatim"
  - itn_native_numerals  "true" | "false"
Response: { success, request_id, timestamp, transcript, model,
            processing_time, end_to_end_latency }

Audio format note
-----------------
Browsers typically record as audio/webm;codecs=opus which Gnani does NOT accept.
Gnani's supported formats: aac, flac, wav, ogg, mp3, m4a.
We convert to WAV (16 kHz mono 16-bit) via audio_convert before uploading.

Language code note
------------------
Gnani Prisma supports: as-IN, bn-IN, en-IN, gu-IN, hi-IN, indic-auto,
                        kn-IN, ml-IN, mr-IN, pa-IN, ta-IN, te-IN.
Codes NOT supported: ur-IN, or-IN (return 400 INVALID_LANGUAGE_CODE).
The router validates language support before calling Gnani; unsupported
languages receive a clear 422 with a user-friendly error message.

Minimum audio note
------------------
Gnani returns success=True with transcript="" for silence or non-speech audio.
The backend raises GnaniSTTError in that case with a user-friendly message.
"""
from __future__ import annotations

import logging

import httpx

from ..config import get_settings
from .audio_convert import AudioConversionError, ensure_gnani_compatible

logger = logging.getLogger(__name__)

_STT_URL = "https://api.vachana.ai/stt/v3"

# Language codes that Gnani Prisma STT actually accepts.
# Verified against API error response INVALID_LANGUAGE_CODE.
GNANI_STT_SUPPORTED_LANGUAGES: frozenset[str] = frozenset({
    "as-IN", "bn-IN", "en-IN", "gu-IN", "hi-IN",
    "indic-auto", "kn-IN", "ml-IN", "mr-IN", "pa-IN", "ta-IN", "te-IN",
})

# Minimum blob size in bytes below which we reject before sending to Gnani.
# A 0.5-second WAV at 16kHz mono 16-bit = 16000 bytes, so 2000 bytes is a
# safe lower bound that rejects header-only or truncated recordings.
_MIN_AUDIO_BYTES = 2_000


class GnaniSTTError(Exception):
    """Raised when the Gnani STT API returns an error or is misconfigured."""


async def transcribe(
    audio_bytes: bytes,
    language_code: str,
    content_type: str = "audio/webm",
    format: str = "transcribe",
    itn_native_numerals: bool = True,
) -> dict:
    """
    Call Gnani Prisma STT and return the full response dict.

    Audio is automatically converted to WAV if the browser produced an
    unsupported format (e.g. WebM/Opus).

    Raises GnaniSTTError on any failure — callers must NOT fabricate a fallback transcript.

    Returns: {success: bool, request_id: str, timestamp: str, transcript: str}
    """
    settings = get_settings()
    if not settings.gnani_api_key:
        raise GnaniSTTError(
            "GNANI_API_KEY is not configured. "
            "Set it in backend/.env before using speech-to-text."
        )

    if not audio_bytes:
        raise GnaniSTTError("No audio data received. The recording may be empty.")

    if len(audio_bytes) < _MIN_AUDIO_BYTES:
        raise GnaniSTTError(
            f"Audio recording is too short ({len(audio_bytes)} bytes). "
            "Please speak for at least 1 second and try again."
        )

    # ── Validate language code before calling Gnani ────────────────────────────
    if language_code not in GNANI_STT_SUPPORTED_LANGUAGES:
        raise GnaniSTTError(
            f"Speech recognition is not available for language '{language_code}'. "
            f"Supported languages: {', '.join(sorted(GNANI_STT_SUPPORTED_LANGUAGES))}. "
            "Please type your transaction manually or switch to a supported language."
        )

    # ── Convert to a Gnani-supported format if necessary ──────────────────────
    try:
        final_bytes, final_mime, filename = ensure_gnani_compatible(
            audio_bytes, content_type
        )
    except AudioConversionError as exc:
        raise GnaniSTTError(
            f"Could not convert audio to a Gnani-supported format: {exc}. "
            "Supported formats: aac, flac, wav, ogg, mp3, m4a."
        ) from exc

    logger.info(
        "Sending to Gnani STT: file=%s mime=%s original_size=%d final_size=%d lang=%s",
        filename, final_mime, len(audio_bytes), len(final_bytes), language_code,
    )

    headers = {
        "X-API-Key-ID": settings.gnani_api_key,
    }
    files = {
        "audio_file": (filename, final_bytes, final_mime),
    }
    data = {
        "language_code": language_code,
        "format":        format,
        "itn_native_numerals": str(itn_native_numerals).lower(),
    }

    try:
        async with httpx.AsyncClient(timeout=settings.gnani_timeout_seconds) as client:
            response = await client.post(_STT_URL, headers=headers, files=files, data=data)
    except httpx.TimeoutException as exc:
        raise GnaniSTTError(
            f"Speech recognition timed out after {settings.gnani_timeout_seconds}s. "
            "Please check your internet connection and try again."
        ) from exc
    except httpx.RequestError as exc:
        raise GnaniSTTError(
            f"Could not connect to speech recognition service: {exc}. "
            "Please check your internet connection."
        ) from exc

    if response.status_code == 400:
        body = response.text[:400]
        logger.error("Gnani STT 400 error: %s", body)
        # Try to extract user-friendly message from Gnani's error JSON
        try:
            err_payload = response.json()
            err_detail = err_payload.get("error", {})
            if isinstance(err_detail, dict):
                err_msg = err_detail.get("message", body)
            else:
                err_msg = str(err_detail)
        except Exception:
            err_msg = body
        raise GnaniSTTError(f"Speech recognition request was rejected: {err_msg}")
    if response.status_code == 401:
        raise GnaniSTTError("Speech recognition API key is invalid or missing (401). Contact support.")
    if response.status_code == 429:
        raise GnaniSTTError("Speech recognition rate limit reached (429). Please wait a moment and try again.")
    if response.status_code >= 500:
        raise GnaniSTTError(f"Speech recognition service is temporarily unavailable ({response.status_code}). Please try again.")
    if response.status_code != 200:
        raise GnaniSTTError(
            f"Speech recognition error {response.status_code}: {response.text[:300]}"
        )

    try:
        payload = response.json()
    except Exception as exc:
        raise GnaniSTTError(
            f"Speech recognition returned an unexpected response (non-JSON): {response.text[:200]}"
        ) from exc

    if not payload.get("success"):
        err = payload.get("error", payload)
        raise GnaniSTTError(f"Speech recognition reported a failure: {err}")

    transcript = payload.get("transcript", "")
    processing_time = payload.get("processing_time", 0)

    logger.info(
        "Gnani STT response: request_id=%s model=%s processing_time=%.3fs transcript_len=%d",
        payload.get("request_id", ""),
        payload.get("model", ""),
        processing_time,
        len(transcript),
    )

    if not transcript or not transcript.strip():
        # Distinguish between very fast (silence) and normal processing
        if processing_time < 0.2:
            raise GnaniSTTError(
                "No speech was detected in the recording. "
                "Please speak clearly, hold the microphone closer, and try again."
            )
        raise GnaniSTTError(
            "Speech was not recognized. Please speak clearly and try again. "
            "Make sure you are speaking in the selected language."
        )

    return {
        "success":     True,
        "request_id":  payload.get("request_id", ""),
        "timestamp":   payload.get("timestamp", ""),
        "transcript":  transcript.strip(),
    }
