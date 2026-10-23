"""
Gnani AI Prisma — Speech-to-Text (REST v3).

Endpoint: POST https://api.vachana.ai/stt/v3
Auth:     X-API-Key-ID header
Body:     multipart/form-data
  - audio_file       (bytes)
  - language_code    e.g. kn-IN
  - format           "transcribe" (with ITN) | "verbatim"
  - itn_native_numerals  "true" | "false"
Response: { success, request_id, timestamp, transcript }
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from ..config import get_settings

logger = logging.getLogger(__name__)

_STT_URL = "https://api.vachana.ai/stt/v3"

# Audio formats the browser may produce — mapped to file extension hint for Gnani
_MIME_TO_EXT = {
    "audio/webm":       "webm",
    "audio/webm;codecs=opus": "webm",
    "audio/ogg":        "ogg",
    "audio/ogg;codecs=opus": "ogg",
    "audio/wav":        "wav",
    "audio/wave":       "wav",
    "audio/mpeg":       "mp3",
    "audio/mp4":        "mp4",
    "audio/x-m4a":      "m4a",
    "audio/aac":        "aac",
}


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
        raise GnaniSTTError("No audio data received.")

    # Determine file extension from content-type for the filename sent to Gnani
    ext = _MIME_TO_EXT.get(content_type.split(";")[0].strip(), "webm")
    filename = f"recording.{ext}"

    headers = {
        "X-API-Key-ID": settings.gnani_api_key,
    }

    files = {
        "audio_file": (filename, audio_bytes, content_type),
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
        raise GnaniSTTError(f"Gnani STT request timed out after {settings.gnani_timeout_seconds}s") from exc
    except httpx.RequestError as exc:
        raise GnaniSTTError(f"Gnani STT network error: {exc}") from exc

    if response.status_code == 401:
        raise GnaniSTTError("Gnani STT: Invalid or missing API key (401 Unauthorized).")
    if response.status_code == 429:
        raise GnaniSTTError("Gnani STT: Rate limit exceeded (429). Please try again later.")
    if response.status_code >= 500:
        raise GnaniSTTError(f"Gnani STT: Server error ({response.status_code}). Try again.")
    if response.status_code != 200:
        raise GnaniSTTError(
            f"Gnani STT error {response.status_code}: {response.text[:300]}"
        )

    try:
        payload = response.json()
    except Exception as exc:
        raise GnaniSTTError(f"Gnani STT returned non-JSON response: {response.text[:200]}") from exc

    if not payload.get("success"):
        raise GnaniSTTError(f"Gnani STT reported failure: {payload}")

    transcript = payload.get("transcript", "")
    if not transcript:
        raise GnaniSTTError("Gnani STT returned an empty transcript.")

    return {
        "success":     True,
        "request_id":  payload.get("request_id", ""),
        "timestamp":   payload.get("timestamp", ""),
        "transcript":  transcript,
    }
