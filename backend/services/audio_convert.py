"""
Audio format conversion for Gnani STT compatibility.

Root-cause diagnosis (2026-10-23):
  - Browser MediaRecorder produces audio/webm;codecs=opus.
  - Gnani Prisma accepts: aac, flac, wav, ogg, mp3, m4a — NOT webm.
  - Previous pydub-based approach failed because pydub calls ffprobe for
    mediainfo before decoding. imageio-ffmpeg bundles only ffmpeg, not
    ffprobe, so AudioSegment.from_file() raised FileNotFoundError for
    ffprobe even though AudioSegment.converter was set correctly.

Fix:
  - Use ffmpeg directly via subprocess (no pydub, no ffprobe).
  - Input format is declared explicitly with -f so no probing is needed.
  - Output is WAV PCM 16-bit 16 kHz mono — accepted by Gnani and ideal
    for speech recognition.
  - If ffmpeg fails, AudioConversionError is raised with the stderr output
    so the error is never silently swallowed.
"""
from __future__ import annotations

import io
import logging
import subprocess

logger = logging.getLogger(__name__)

# ── Locate the imageio-ffmpeg bundled binary once at import time ──────────────
try:
    import imageio_ffmpeg as _iio_ffmpeg
    _FFMPEG_EXE: str = _iio_ffmpeg.get_ffmpeg_exe()
    logger.debug("audio_convert: ffmpeg binary = %s", _FFMPEG_EXE)
    _FFMPEG_AVAILABLE = True
except Exception as _exc:
    _FFMPEG_EXE = "ffmpeg"   # will fail gracefully at conversion time
    _FFMPEG_AVAILABLE = False
    logger.warning("audio_convert: imageio-ffmpeg not available: %s", _exc)

# Formats Gnani Prisma actually accepts (from its error response):
#   wav, ogg, flac, m4a, aac, mp3
# NOTE: "mp4" is NOT accepted by Gnani even though it is a valid audio format.
#   audio/mp4;codecs=opus (recorded by Edge/Chrome on Windows) must be converted.
#   m4a IS accepted — it is a different container to Gnani, despite similar MIME types.
_GNANI_ACCEPTED = {"aac", "flac", "wav", "ogg", "mp3", "m4a"}

# Map MIME base type -> (file extension, ffmpeg -f input-format hint)
_MIME_INFO: dict[str, tuple[str, str]] = {
    "audio/webm":   ("webm", "webm"),
    "audio/ogg":    ("ogg",  "ogg"),
    "audio/wav":    ("wav",  "wav"),
    "audio/wave":   ("wav",  "wav"),
    "audio/mpeg":   ("mp3",  "mp3"),
    "audio/mp3":    ("mp3",  "mp3"),
    "audio/mp4":    ("mp4",  "mp4"),   # NOT in _GNANI_ACCEPTED — will be converted to WAV
    "audio/x-m4a":  ("m4a",  "mov"),
    "audio/m4a":    ("m4a",  "mov"),
    "audio/aac":    ("aac",  "aac"),
    "audio/flac":   ("flac", "flac"),
    "audio/x-flac": ("flac", "flac"),
}


class AudioConversionError(Exception):
    """Raised when audio cannot be converted to a Gnani-compatible format."""


def _mime_base(content_type: str) -> str:
    """'audio/webm;codecs=opus'  →  'audio/webm'"""
    return content_type.split(";")[0].strip().lower()


def needs_conversion(content_type: str) -> bool:
    """Return True if this MIME type must be converted before sending to Gnani."""
    base = _mime_base(content_type)
    ext, _ = _MIME_INFO.get(base, ("", ""))
    return ext not in _GNANI_ACCEPTED


def convert_to_wav(audio_bytes: bytes, content_type: str) -> tuple[bytes, str]:
    """
    Convert *audio_bytes* to WAV PCM 16-bit / 16 kHz / mono using ffmpeg
    directly via subprocess (no pydub / no ffprobe required).

    The input format hint (-f) is taken from _MIME_INFO so ffmpeg never
    needs to probe the file — critical because imageio-ffmpeg ships only
    the ffmpeg binary, not ffprobe.

    Returns (wav_bytes, "audio/wav").
    Raises AudioConversionError on any failure, with the full stderr in
    the message so the cause is never silently hidden.
    """
    if not _FFMPEG_AVAILABLE:
        raise AudioConversionError(
            "imageio-ffmpeg is not installed. "
            "Run: pip install imageio-ffmpeg"
        )

    base = _mime_base(content_type)
    _, ffmpeg_fmt = _MIME_INFO.get(base, ("", "webm"))

    logger.info(
        "audio_convert: converting %s (%d bytes) to WAV via ffmpeg (input_fmt=%s)",
        content_type, len(audio_bytes), ffmpeg_fmt,
    )

    cmd = [
        _FFMPEG_EXE,
        "-y",                  # overwrite output without asking
        "-f", ffmpeg_fmt,      # declare input format explicitly — no probing
        "-i", "pipe:0",        # read from stdin
        "-ar", "16000",        # 16 kHz sample rate (good for STT)
        "-ac", "1",            # mono
        "-sample_fmt", "s16",  # 16-bit signed PCM
        "-f", "wav",           # output format
        "pipe:1",              # write to stdout
    ]

    try:
        proc = subprocess.run(
            cmd,
            input=audio_bytes,
            capture_output=True,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise AudioConversionError(
            f"ffmpeg binary not found at {_FFMPEG_EXE!r}: {exc}"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise AudioConversionError("ffmpeg conversion timed out after 30s") from exc

    if proc.returncode != 0:
        stderr_tail = proc.stderr[-400:].decode("utf-8", errors="replace")
        raise AudioConversionError(
            f"ffmpeg exited with code {proc.returncode} "
            f"(input_fmt={ffmpeg_fmt!r}, content_type={content_type!r}).\n"
            f"ffmpeg stderr:\n{stderr_tail}"
        )

    wav_bytes = proc.stdout
    if len(wav_bytes) < 44:  # WAV header is 44 bytes minimum
        raise AudioConversionError(
            f"ffmpeg produced only {len(wav_bytes)} bytes — likely an encoding error. "
            f"stderr: {proc.stderr[-200:].decode('utf-8', errors='replace')}"
        )

    logger.info(
        "audio_convert: conversion OK — %d bytes WAV (magic=%r)",
        len(wav_bytes), wav_bytes[:4],
    )
    return wav_bytes, "audio/wav"


def ensure_gnani_compatible(
    audio_bytes: bytes, content_type: str
) -> tuple[bytes, str, str]:
    """
    Return (final_bytes, final_content_type, filename) ready to upload to
    Gnani Prisma STT.

    If the incoming format is already in Gnani's accepted list, the bytes
    are returned unchanged.  Otherwise they are converted to WAV.
    Raises AudioConversionError on conversion failure — never falls back
    silently to the original bytes.
    """
    base = _mime_base(content_type)
    ext, _ = _MIME_INFO.get(base, ("webm", "webm"))

    if ext in _GNANI_ACCEPTED:
        logger.debug(
            "audio_convert: %s (%s) is Gnani-compatible — no conversion needed",
            content_type, ext,
        )
        return audio_bytes, content_type, f"recording.{ext}"

    # Must convert — never silently pass through unsupported bytes
    logger.info(
        "audio_convert: %s not accepted by Gnani — converting to WAV", content_type
    )
    wav_bytes, wav_mime = convert_to_wav(audio_bytes, content_type)
    return wav_bytes, wav_mime, "recording.wav"
