"""Languages router — exposes centralized language configuration."""
from typing import List
from fastapi import APIRouter

from ..languages import LanguageConfig, get_all_languages, get_language

router = APIRouter(prefix="/api/languages", tags=["languages"])


@router.get("", response_model=List[LanguageConfig])
def list_languages():
    """Return all verified Indian languages with their capabilities and settings."""
    return get_all_languages()


@router.get("/{code}", response_model=LanguageConfig)
def get_language_by_code(code: str):
    lang = get_language(code)
    if not lang:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Language code '{code}' not supported.")
    return lang
