"""
STT router — accepts audio upload, calls real Gnani Prisma, returns transcript.
Never returns a fabricated transcript.
"""
import logging
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ..auth import get_current_shop
from ..config import get_settings
from ..models import Shop
from ..schemas import STTResponse
from ..services import gnani_stt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/stt", tags=["stt"])

_ALLOWED_MIME_PREFIXES = ("audio/",)
_MAX_BYTES = get_settings().max_audio_size_mb * 1024 * 1024


@router.post("/transcribe", response_model=STTResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language_code: str = Form("kn-IN"),
    shop: Shop = Depends(get_current_shop),
):
    """
    Upload audio (WebM/WAV/OGG/MP3/MP4) → Gnani Prisma → transcript.
    Returns 422 if Gnani fails; never fakes a result.
    """
    content_type = audio_file.content_type or "audio/webm"
    if not any(content_type.startswith(p) for p in _ALLOWED_MIME_PREFIXES):
        raise HTTPException(status_code=415, detail=f"Unsupported audio format: {content_type}")

    audio_bytes = await audio_file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(status_code=400, detail="Audio file is empty.")
    if len(audio_bytes) > _MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Audio too large. Max size: {get_settings().max_audio_size_mb} MB.",
        )

    logger.info(
        "STT request: shop=%d lang=%s size=%d content_type=%s",
        shop.id, language_code, len(audio_bytes), content_type,
    )

    try:
        result = await gnani_stt.transcribe(
            audio_bytes=audio_bytes,
            language_code=language_code,
            content_type=content_type,
            format="transcribe",
            itn_native_numerals=True,
        )
    except gnani_stt.GnaniSTTError as exc:
        logger.error("Gnani STT error: %s", exc)
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "transcript": None,
                "request_id": None,
                "language_code": language_code,
                "error": str(exc),
            },
        )

    return STTResponse(
        success=True,
        transcript=result["transcript"],
        request_id=result["request_id"],
        language_code=language_code,
    )


@router.post("/parse")
async def parse_transcript(
    transcript: str = Form(...),
    language_code: str = Form("kn-IN"),
    shop: Shop = Depends(get_current_shop),
):
    """Parse a transcript string into structured transaction fields."""
    from ..services.parser import parse_transaction
    parsed = parse_transaction(transcript, language_code)
    return parsed.model_dump()
