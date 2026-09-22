import math
import struct
from typing import Optional
from app.core.logging import logger

# Precomputed G.711 mu-law decoding table
_MULAW_TO_PCM = []
for i in range(256):
    byte = ~i & 0xFF
    sign = -1 if (byte & 0x80) else 1
    exponent = (byte >> 4) & 0x07
    mantissa = byte & 0x0F
    sample = sign * ((mantissa << 3) + 0x84) << exponent
    sample -= sign * 0x84
    _MULAW_TO_PCM.append(max(min(sample, 32767), -32768))


def mulaw_decode(mulaw_bytes: bytes) -> bytes:
    """Decodes 8-bit G.711 mu-law audio to 16-bit signed linear PCM."""
    samples = [_MULAW_TO_PCM[b] for b in mulaw_bytes]
    return struct.pack(f"<{len(samples)}h", *samples)


def linear_to_mulaw(pcm_bytes: bytes) -> bytes:
    """Encodes 16-bit signed linear PCM to 8-bit G.711 mu-law audio."""
    count = len(pcm_bytes) // 2
    if count == 0:
        return b""
    samples = struct.unpack(f"<{count}h", pcm_bytes)
    result = bytearray(count)

    for idx, sample in enumerate(samples):
        sign = 0x80 if sample < 0 else 0
        sample = abs(sample)
        sample = min(sample + 0x84, 32767)

        # Determine exponent (segment)
        if sample >= 0x4000:
            exp = 7
        elif sample >= 0x2000:
            exp = 6
        elif sample >= 0x1000:
            exp = 5
        elif sample >= 0x0800:
            exp = 4
        elif sample >= 0x0400:
            exp = 3
        elif sample >= 0x0200:
            exp = 2
        elif sample >= 0x0100:
            exp = 1
        else:
            exp = 0

        mantissa = (sample >> (exp + 3)) & 0x0F
        ulaw_byte = ~(sign | (exp << 4) | mantissa) & 0xFF
        result[idx] = ulaw_byte

    return bytes(result)


def resample_pcm_linear(pcm_data: bytes, from_rate: int, to_rate: int) -> bytes:
    """
    Resample 16-bit mono linear PCM between sample rates (e.g. 8000Hz <-> 16000Hz).
    Pure python implementation with no external C-extensions required.
    """
    if from_rate == to_rate or not pcm_data:
        return pcm_data

    num_samples = len(pcm_data) // 2
    if num_samples == 0:
        return b""

    samples = struct.unpack(f"<{num_samples}h", pcm_data)
    ratio = to_rate / from_rate
    new_length = int(num_samples * ratio)
    new_samples = []

    for i in range(new_length):
        pos = i / ratio
        idx = int(pos)
        frac = pos - idx
        if idx + 1 < num_samples:
            interpolated = samples[idx] * (1.0 - frac) + samples[idx + 1] * frac
        else:
            interpolated = samples[idx] if idx < num_samples else 0
        new_samples.append(int(max(min(interpolated, 32767), -32768)))

    return struct.pack(f"<{len(new_samples)}h", *new_samples)


class AudioPipeline:
    """
    Dedicated Audio Pipeline for telephony-to-AI transcoding.
    Decoupled completely from business logic.
    """

    def __init__(
        self,
        phone_sample_rate: int = 8000,
        ai_sample_rate: int = 16000,
        codec: str = "mulaw",
    ):
        self.phone_sample_rate = phone_sample_rate
        self.ai_sample_rate = ai_sample_rate
        self.codec = codec

    def receive_from_phone(self, raw_audio: bytes) -> bytes:
        """
        Receives raw phone bytes, decodes from codec, and resamples to AI rate.
        Returns 16-bit linear PCM at ai_sample_rate (16kHz).
        """
        if not raw_audio:
            return b""

        # 1. Decode to linear 16-bit PCM
        if self.codec == "mulaw":
            pcm = mulaw_decode(raw_audio)
        else:
            pcm = raw_audio

        # 2. Resample from phone rate (8kHz) to AI rate (16kHz)
        ai_pcm = resample_pcm_linear(pcm, self.phone_sample_rate, self.ai_sample_rate)
        return ai_pcm

    def encode_for_phone(self, ai_audio: bytes) -> bytes:
        """
        Receives AI 16-bit linear PCM, resamples to phone rate, and encodes to telephony format.
        """
        if not ai_audio:
            return b""

        # 1. Resample from AI rate (16kHz) down to phone rate (8kHz)
        phone_pcm = resample_pcm_linear(ai_audio, self.ai_sample_rate, self.phone_sample_rate)

        # 2. Encode to codec (mulaw)
        if self.codec == "mulaw":
            return linear_to_mulaw(phone_pcm)
        return phone_pcm

    @staticmethod
    def calculate_rms(pcm_data: bytes) -> float:
        """Calculate Root Mean Square energy to detect speech vs silence."""
        count = len(pcm_data) // 2
        if count == 0:
            return 0.0
        samples = struct.unpack(f"<{count}h", pcm_data)
        sum_squares = sum(s * s for s in samples)
        return math.sqrt(sum_squares / count)
