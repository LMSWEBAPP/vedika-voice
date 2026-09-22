import pytest
from app.telephony.audio_pipeline import (
    AudioPipeline,
    linear_to_mulaw,
    mulaw_decode,
    resample_pcm_linear,
)


def test_mulaw_codec_roundtrip():
    # 16-bit PCM test samples: silence, positive value, negative value
    original_pcm = b"\x00\x00\x00\x10\x00\xf0"
    mulaw = linear_to_mulaw(original_pcm)
    assert len(mulaw) == len(original_pcm) // 2

    decoded_pcm = mulaw_decode(mulaw)
    assert len(decoded_pcm) == len(original_pcm)


def test_linear_resampling():
    pipeline = AudioPipeline(phone_sample_rate=8000, ai_sample_rate=16000)

    # 10ms of 8kHz mu-law audio = 80 bytes
    phone_raw = b"\xff" * 80
    ai_pcm = pipeline.receive_from_phone(phone_raw)

    # At 16kHz 16-bit, 10ms = 160 samples = 320 bytes
    assert len(ai_pcm) == 320

    # Encode back to phone format
    encoded_back = pipeline.encode_for_phone(ai_pcm)
    assert len(encoded_back) == 80


def test_calculate_rms():
    silent_pcm = b"\x00\x00" * 100
    assert AudioPipeline.calculate_rms(silent_pcm) == 0.0

    loud_pcm = b"\x00\x40" * 100
    assert AudioPipeline.calculate_rms(loud_pcm) > 0.0
