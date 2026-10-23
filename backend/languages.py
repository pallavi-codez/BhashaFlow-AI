"""
Centralized Language Registry for BhashaFlow AI.
Records verified capabilities for Gnani Prisma STT, Gnani Timbre TTS,
transaction parser, UI translations, and script text directions.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel


class LanguageConfig(BaseModel):
    code: str                     # e.g. "kn-IN"
    name: str                     # e.g. "Kannada"
    native_name: str              # e.g. "ಕನ್ನಡ"
    stt_supported: bool           # Gnani Prisma STT capability
    tts_supported: bool           # Gnani Timbre TTS capability
    default_voice: str            # Recommended voice name
    voices: List[str]             # Available voices
    ui_translated: bool           # UI strings translated
    parser_supported: bool        # Transaction parser availability
    text_direction: str = "ltr"   # "ltr" or "rtl" (Urdu)
    sample_phrase: str            # Demonstration command in this language
    sample_translation: str       # English explanation of sample phrase


# Central registry of supported Indian languages
SUPPORTED_LANGUAGES: Dict[str, LanguageConfig] = {
    "kn-IN": LanguageConfig(
        code="kn-IN",
        name="Kannada",
        native_name="ಕನ್ನಡ",
        stt_supported=True,
        tts_supported=True,
        default_voice="Kaveri",
        voices=["Kaveri", "Nalini", "Deepak"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Ramesh ge 500 rupees udhar haaku",
        sample_translation="Put 500 rupees credit for Ramesh",
    ),
    "hi-IN": LanguageConfig(
        code="hi-IN",
        name="Hindi",
        native_name="हिन्दी",
        stt_supported=True,
        tts_supported=True,
        default_voice="Nalini",
        voices=["Nalini", "Deepak", "Shivani", "Avinash"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Ramesh ko 500 rupaye udhar likho",
        sample_translation="Write 500 rupees credit for Ramesh",
    ),
    "en-IN": LanguageConfig(
        code="en-IN",
        name="English",
        native_name="English (India)",
        stt_supported=True,
        tts_supported=True,
        default_voice="Deepak",
        voices=["Deepak", "Nalini", "Kaveri"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Ramesh paid 200 rupees",
        sample_translation="Ramesh paid 200 rupees against previous debt",
    ),
    "ta-IN": LanguageConfig(
        code="ta-IN",
        name="Tamil",
        native_name="தமிழ்",
        stt_supported=True,
        tts_supported=True,
        default_voice="Nalini",
        voices=["Nalini", "Deepak"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Ramesh ku 500 roobai kadan podu",
        sample_translation="Add 500 rupees credit for Ramesh",
    ),
    "te-IN": LanguageConfig(
        code="te-IN",
        name="Telugu",
        native_name="తెలుగు",
        stt_supported=True,
        tts_supported=True,
        default_voice="Nalini",
        voices=["Nalini", "Deepak"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Ramesh ki 500 rupayalu appu raayi",
        sample_translation="Write 500 rupees credit for Ramesh",
    ),
    "ml-IN": LanguageConfig(
        code="ml-IN",
        name="Malayalam",
        native_name="മലയാളം",
        stt_supported=True,
        tts_supported=True,
        default_voice="Nalini",
        voices=["Nalini"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Rameshinu 500 roopa kadam ezhuthu",
        sample_translation="Write 500 rupees credit for Ramesh",
    ),
    "mr-IN": LanguageConfig(
        code="mr-IN",
        name="Marathi",
        native_name="मराठी",
        stt_supported=True,
        tts_supported=True,
        default_voice="Nalini",
        voices=["Nalini", "Deepak"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Ramesh la 500 rupaye udhari liha",
        sample_translation="Write 500 rupees credit for Ramesh",
    ),
    "bn-IN": LanguageConfig(
        code="bn-IN",
        name="Bengali",
        native_name="বাংলা",
        stt_supported=True,
        tts_supported=True,
        default_voice="Nalini",
        voices=["Nalini"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Ramesh ke 500 taka baki lekho",
        sample_translation="Write 500 rupees credit for Ramesh",
    ),
    "gu-IN": LanguageConfig(
        code="gu-IN",
        name="Gujarati",
        native_name="ગુજરાતી",
        stt_supported=True,
        tts_supported=True,
        default_voice="Nalini",
        voices=["Nalini"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Ramesh ne 500 rupiya udhar lakho",
        sample_translation="Write 500 rupees credit for Ramesh",
    ),
    "pa-IN": LanguageConfig(
        code="pa-IN",
        name="Punjabi",
        native_name="ਪੰਜਾਬੀ",
        stt_supported=True,
        tts_supported=True,
        default_voice="Nalini",
        voices=["Nalini"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Ramesh nu 500 rupaye udhar likho",
        sample_translation="Write 500 rupees credit for Ramesh",
    ),
    "or-IN": LanguageConfig(
        code="or-IN",
        name="Odia",
        native_name="ଓଡ଼ିଆ",
        stt_supported=True,
        tts_supported=True,
        default_voice="Nalini",
        voices=["Nalini"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Ramesh ku 500 tanka udhara lekha",
        sample_translation="Write 500 rupees credit for Ramesh",
    ),
    "as-IN": LanguageConfig(
        code="as-IN",
        name="Assamese",
        native_name="অসমীয়া",
        stt_supported=True,
        tts_supported=True,
        default_voice="Nalini",
        voices=["Nalini"],
        ui_translated=True,
        parser_supported=True,
        text_direction="ltr",
        sample_phrase="Rameshok 500 toka baaki likha",
        sample_translation="Write 500 rupees credit for Ramesh",
    ),
    "ur-IN": LanguageConfig(
        code="ur-IN",
        name="Urdu",
        native_name="اردو",
        stt_supported=True,
        tts_supported=True,
        default_voice="Nalini",
        voices=["Nalini"],
        ui_translated=True,
        parser_supported=True,
        text_direction="rtl",
        sample_phrase="رمیش کو 500 روپے ادھار لکھو",
        sample_translation="Write 500 rupees credit for Ramesh",
    ),
}


def get_all_languages() -> List[LanguageConfig]:
    return list(SUPPORTED_LANGUAGES.values())


def get_language(code: str) -> Optional[LanguageConfig]:
    return SUPPORTED_LANGUAGES.get(code)
