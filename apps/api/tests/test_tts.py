import pytest
from httpx import AsyncClient
from app.services.tts_service import normalize_text_for_speech, tts_service, is_devanagari_hindi


def test_normalize_text_for_speech():
    sample = "**Madhu**: Hello! We build custom CRM and AI software in a 15-min demo."
    cleaned = normalize_text_for_speech(sample)
    assert "**" not in cleaned
    assert "C.R.M." in cleaned
    assert "A.I." in cleaned
    assert "fifteen minute" in cleaned


def test_is_devanagari_hindi():
    assert is_devanagari_hindi("नमस्ते, आप कैसे हैं?") is True
    assert is_devanagari_hindi("Hello, how are you?") is False


def test_resolve_voice():
    assert tts_service.resolve_voice("Madhu") == "en-IN-NeerjaExpressiveNeural"
    assert tts_service.resolve_voice("Rohan") == "en-IN-PrabhatNeural"
    assert tts_service.resolve_voice("Swara") == "hi-IN-SwaraNeural"
    assert tts_service.resolve_voice("Kore") == "en-IN-NeerjaNeural"
    # Hindi text auto-detection
    assert tts_service.resolve_voice(text="नमस्ते") == "hi-IN-SwaraNeural"


@pytest.mark.asyncio
async def test_tts_service_synthesis():
    text = "Hello, this is a test of ultra-realistic human neural speech synthesis."
    b64 = await tts_service.synthesize_to_base64(text, voice_name="Madhu")
    assert isinstance(b64, str)
    assert len(b64) > 1000


@pytest.mark.asyncio
async def test_synthesize_speech_endpoint(client: AsyncClient):
    resp = await client.post(
        "/api/v1/agents/synthesize-speech",
        json={
            "text": "Hello, good day! This is Madhu calling from our custom software team.",
            "voice_name": "Madhu"
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "audio_base64" in data
    assert len(data["audio_base64"]) > 500
    assert data["format"] == "audio/mp3"


@pytest.mark.asyncio
async def test_list_voices_endpoint(client: AsyncClient):
    resp = await client.get("/api/v1/agents/voices")
    assert resp.status_code == 200
    voices = resp.json()
    assert len(voices) >= 5
    voice_names = [v["name"] for v in voices]
    assert "Madhu" in voice_names
