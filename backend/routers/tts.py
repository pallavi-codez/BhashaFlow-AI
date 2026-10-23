"""
TTS router — accepts text, calls real Gnani Timbre, streams WAV audio.
Never returns synthesised-browser audio or fake bytes.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ..auth import get_current_shop
from ..models import Shop
from ..schemas import TTSRequest
from ..services import gnani_tts
from ..services.gnani_tts import TIMBRE_V25_VOICES, TIMBRE_V30_VOICES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tts", tags=["tts"])


@router.post("/speak")
async def speak(
    data: TTSRequest,
    shop: Shop = Depends(get_current_shop),
):
    """
    Synthesise speech with Gnani Timbre. Returns a WAV audio stream.
    Raises 422 if Gnani fails — does NOT fall back to browser speech synthesis.
    """
    # Validate voice belongs to chosen model
    if data.model == "timbre-v2.5" and data.voice not in TIMBRE_V25_VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Voice '{data.voice}' not valid for timbre-v2.5. "
                   f"Valid voices: {TIMBRE_V25_VOICES}",
        )
    if data.model == "timbre-v3.0" and data.voice not in TIMBRE_V30_VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Voice '{data.voice}' not valid for timbre-v3.0. "
                   f"Valid voices: {TIMBRE_V30_VOICES}",
        )

    logger.info(
        "TTS request: shop=%d voice=%s lang=%s chars=%d",
        shop.id, data.voice, data.language, len(data.text),
    )

    try:
        audio_bytes = await gnani_tts.synthesize(
            text=data.text,
            voice=data.voice,
            model=data.model,
            language=data.language,
            speed=data.speed,
        )
    except gnani_tts.GnaniTTSError as exc:
        logger.error("Gnani TTS error: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc))

    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/wav",
        headers={"Content-Length": str(len(audio_bytes))},
    )


@router.get("/voices")
def list_voices():
    """Return documented voice catalog."""
    return {
        "timbre-v2.5": TIMBRE_V25_VOICES,
        "timbre-v3.0": TIMBRE_V30_VOICES,
    }
