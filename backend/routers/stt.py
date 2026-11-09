"""
STT router — accepts audio upload, calls real Gnani Prisma, returns transcript.
Never returns a fabricated transcript.
"""
import logging
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ..auth import get_current_shop
from ..config import get_settings
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Customer, PriceListItem, Shop
from ..schemas import STTResponse
from ..services import gnani_stt
from ..languages import SUPPORTED_LANGUAGES

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

    # Validate that the selected language supports STT before calling Gnani.
    # This prevents confusing 400 errors for languages like ur-IN / or-IN.
    lang_config = SUPPORTED_LANGUAGES.get(language_code)
    if lang_config and not lang_config.stt_supported:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "transcript": None,
                "request_id": None,
                "language_code": language_code,
                "error": (
                    f"Voice input is not available for {lang_config.name} ({language_code}). "
                    "Please type your transaction manually or switch to a supported language "
                    f"(Kannada, Hindi, English, Tamil, Telugu, Malayalam, Marathi, Bengali, "
                    f"Gujarati, Punjabi, Assamese)."
                ),
            },
        )

    logger.info(
        "STT request: shop=%d lang=%s size=%d content_type=%s filename=%s",
        shop.id, language_code, len(audio_bytes), content_type,
        audio_file.filename or "(no filename)",
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
    db: Session = Depends(get_db),
    shop: Shop = Depends(get_current_shop),
):
    """
    Parse a transcript string into structured transaction fields.
    Matches existing customers and saved price list within the authenticated shop.
    """
    import re
    from ..services.parser import parse_transaction

    # 1. Fetch authenticated shop's existing customers
    customers = list(db.scalars(select(Customer).where(Customer.shop_id == shop.id)).all())
    customer_names = [c.name for c in customers]
    customer_id_map: dict[str, int] = {}
    for c in customers:
        customer_id_map[c.name.lower()] = c.id
        base = re.sub(r"\s*\[demo\]", "", c.name, flags=re.IGNORECASE).strip().lower()
        customer_id_map[base] = c.id

    # 2. Fetch authenticated shop's saved price list
    price_items = list(db.scalars(select(PriceListItem).where(PriceListItem.shop_id == shop.id)).all())
    saved_prices = {p.item_name.lower(): p.unit_price for p in price_items}

    # 3. Deterministically parse transcript
    parsed = parse_transaction(
        transcript=transcript,
        language=language_code,
        existing_customers=customer_names,
        saved_prices=saved_prices,
    )

    # 4. Resolve matched customer ID if available
    if parsed.customer_name:
        lookup_name = parsed.customer_name.strip().lower()
        base_lookup = re.sub(r"\s*\[demo\]", "", lookup_name, flags=re.IGNORECASE).strip()
        matched_id = customer_id_map.get(lookup_name) or customer_id_map.get(base_lookup)
        if matched_id:
            parsed.matched_customer_id = matched_id

    return parsed.model_dump()
