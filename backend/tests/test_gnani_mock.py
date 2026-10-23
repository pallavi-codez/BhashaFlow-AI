"""
Tests for Gnani STT and TTS integration using httpx mocks.
External APIs are mocked — the production app uses real API calls.
"""
import pytest
import pytest_asyncio
from decimal import Decimal


# ── STT tests ────────────────────────────────────────────────────────────────

class TestGnaniSTT:
    def test_stt_success_returns_transcript(self, auth_client, respx_mock):
        """When Gnani returns 200, the transcript is returned to caller."""
        respx_mock.post("https://api.vachana.ai/stt/v3").respond(
            200,
            json={
                "success": True,
                "request_id": "req_test_001",
                "timestamp": "20251226_143052.123",
                "transcript": "Ramesh ge 500 rupees udhar haaku",
            },
        )
        # Need a valid GNANI_API_KEY to get past the check in the service
        import os
        os.environ["GNANI_API_KEY"] = "test-key"

        audio_bytes = b"\x52\x49\x46\x46" + b"\x00" * 40  # minimal fake WAV
        response = auth_client.post(
            "/api/stt/transcribe",
            files={"audio_file": ("recording.wav", audio_bytes, "audio/wav")},
            data={"language_code": "kn-IN"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["transcript"] == "Ramesh ge 500 rupees udhar haaku"

    def test_stt_gnani_401_returns_error(self, auth_client, respx_mock):
        """Gnani 401 must return a clear error, not a fake transcript."""
        respx_mock.post("https://api.vachana.ai/stt/v3").respond(401)
        import os
        os.environ["GNANI_API_KEY"] = "bad-key"

        audio_bytes = b"\x52\x49\x46\x46" + b"\x00" * 40
        response = auth_client.post(
            "/api/stt/transcribe",
            files={"audio_file": ("recording.wav", audio_bytes, "audio/wav")},
            data={"language_code": "kn-IN"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False
        assert data["transcript"] is None
        assert "error" in data

    def test_stt_gnani_500_returns_error(self, auth_client, respx_mock):
        """Gnani server error must return error, not fake transcript."""
        respx_mock.post("https://api.vachana.ai/stt/v3").respond(500, text="Server Error")
        import os
        os.environ["GNANI_API_KEY"] = "test-key"

        audio_bytes = b"\x52\x49\x46\x46" + b"\x00" * 40
        response = auth_client.post(
            "/api/stt/transcribe",
            files={"audio_file": ("recording.wav", audio_bytes, "audio/wav")},
            data={"language_code": "kn-IN"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["success"] is False

    def test_stt_empty_audio_rejected(self, auth_client):
        """Empty audio file must be rejected before calling Gnani."""
        response = auth_client.post(
            "/api/stt/transcribe",
            files={"audio_file": ("recording.wav", b"", "audio/wav")},
            data={"language_code": "kn-IN"},
        )
        assert response.status_code == 400

    def test_stt_invalid_mime_rejected(self, auth_client):
        """Non-audio content type must be rejected (415)."""
        response = auth_client.post(
            "/api/stt/transcribe",
            files={"audio_file": ("file.txt", b"hello world", "text/plain")},
            data={"language_code": "kn-IN"},
        )
        assert response.status_code == 415

    def test_stt_no_key_returns_error(self, auth_client, respx_mock):
        """Without GNANI_API_KEY, must return error not fake transcript."""
        import os
        os.environ.pop("GNANI_API_KEY", None)
        # Reset settings cache
        from backend.config import get_settings
        get_settings.cache_clear()
        # env var removed → key="", service should raise
        audio_bytes = b"\x52\x49\x46\x46" + b"\x00" * 40
        response = auth_client.post(
            "/api/stt/transcribe",
            files={"audio_file": ("recording.wav", audio_bytes, "audio/wav")},
            data={"language_code": "kn-IN"},
        )
        assert response.status_code == 422
        assert response.json()["success"] is False
        assert response.json()["transcript"] is None


# ── TTS tests ─────────────────────────────────────────────────────────────────

# Minimal valid WAV header (44 bytes)
_FAKE_WAV = b"RIFF" + (36).to_bytes(4, "little") + b"WAVEfmt " + (16).to_bytes(4, "little") + \
            b"\x01\x00\x01\x00" + (48000).to_bytes(4, "little") + (96000).to_bytes(4, "little") + \
            b"\x02\x00\x10\x00" + b"data" + (0).to_bytes(4, "little")


class TestGnaniTTS:
    def test_tts_success_returns_audio(self, auth_client, respx_mock):
        """When Gnani returns WAV bytes, they must be streamed back."""
        respx_mock.post("https://api.vachana.ai/api/v1/tts/inference").respond(
            200, content=_FAKE_WAV, headers={"Content-Type": "audio/wav"}
        )
        import os
        os.environ["GNANI_API_KEY"] = "test-key"
        from backend.config import get_settings
        get_settings.cache_clear()

        response = auth_client.post(
            "/api/tts/speak",
            json={
                "text": "Ramesh, five hundred rupees added",
                "language": "kn-IN",
                "voice": "Kaveri",
                "model": "timbre-v2.5",
                "speed": 1.0,
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"
        assert len(response.content) >= 44  # WAV header minimum

    def test_tts_gnani_error_raises_422(self, auth_client, respx_mock):
        """Gnani TTS failure must return 422, never fake audio."""
        respx_mock.post("https://api.vachana.ai/api/v1/tts/inference").respond(500)
        import os
        os.environ["GNANI_API_KEY"] = "test-key"
        from backend.config import get_settings
        get_settings.cache_clear()

        response = auth_client.post(
            "/api/tts/speak",
            json={"text": "Hello", "language": "kn-IN", "voice": "Kaveri", "model": "timbre-v2.5"},
        )
        assert response.status_code == 422

    def test_tts_invalid_voice_rejected(self, auth_client):
        """Voice not in documented catalog must be rejected before calling Gnani."""
        import os
        os.environ["GNANI_API_KEY"] = "test-key"
        from backend.config import get_settings
        get_settings.cache_clear()

        response = auth_client.post(
            "/api/tts/speak",
            json={"text": "Test", "language": "kn-IN", "voice": "FakeVoice", "model": "timbre-v2.5"},
        )
        assert response.status_code == 400

    def test_tts_voice_catalog_endpoint(self, auth_client):
        """Voice catalog endpoint must return documented voices."""
        response = auth_client.get("/api/tts/voices")
        assert response.status_code == 200
        data = response.json()
        assert "timbre-v2.5" in data
        assert "Kaveri" in data["timbre-v2.5"]
        assert "timbre-v3.0" in data


# ── API error display test ────────────────────────────────────────────────────

class TestAPIErrorDisplay:
    def test_unconfirmed_txn_not_in_balance(self, auth_client, db, shop, customer):
        """Unconfirmed transaction must not appear in balance."""
        from backend import crud
        from backend.models import TransactionType
        from backend.schemas import TransactionCreate

        txn_data = TransactionCreate(
            customer_id=customer.id,
            txn_type=TransactionType.CREDIT_SALE,
            amount=Decimal("500"),
        )
        crud.create_transaction(db, shop.id, txn_data)

        # Check balance — must be 0 since not confirmed
        balance = crud.compute_customer_balance(db, shop.id, customer.id)
        assert balance == Decimal("0")
