import asyncio
import base64
import re
from typing import Dict, Optional, Tuple
import edge_tts
from app.core.logging import logger

# High-fidelity Microsoft Neural TTS voice mappings for authentic human speech
VOICE_MAP: Dict[str, str] = {
    # Flagship Pan-India Persona "Madhu" - Warm, gentle, articulate, bilingual Indian English/Hindi
    "aoede": "en-IN-NeerjaExpressiveNeural",
    "kore": "en-IN-NeerjaNeural",
    "madhu": "en-IN-NeerjaExpressiveNeural",
    "neerja": "en-IN-NeerjaExpressiveNeural",
    "neerja_natural": "en-IN-NeerjaNeural",

    # Professional Indian Male Persona "Rohan / Prabhat"
    "puck": "en-IN-PrabhatNeural",
    "prabhat": "en-IN-PrabhatNeural",
    "rohan": "en-IN-PrabhatNeural",

    # Fluent Hindi Personas
    "swara": "hi-IN-SwaraNeural",
    "madhur": "hi-IN-MadhurNeural",

    # US English Personas
    "jenny": "en-US-JennyNeural",
    "guy": "en-US-GuyNeural",
    "fenrir": "en-US-GuyNeural",
    "charon": "en-US-ChristopherNeural",
}

DEFAULT_NEURAL_VOICE = "en-IN-NeerjaExpressiveNeural"
FALLBACK_NEURAL_VOICE = "en-IN-NeerjaNeural"


def normalize_text_for_speech(text: str) -> str:
    """
    Cleans up conversational text for ultra-realistic neural speech synthesis:
    - Strips markdown formatting (bold, italic, headers, bullets).
    - Pronounces acronyms smoothly (A.I., C.R.M., A.P.I., D.N.C.).
    - Replaces technical abbreviations with spoken phrases.
    - Preserves natural conversational pauses (commas, ellipses).
    """
    if not text:
        return ""

    s = text.strip()

    # Remove markdown bold/italic (**word**, *word*, __word__, _word_)
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"\*([^*]+)\*", r"\1", s)
    s = re.sub(r"__([^_]+)__", r"\1", s)
    s = re.sub(r"_([^_]+)_", r"\1", s)

    # Remove markdown headers and bullet points (#, ##, -, *)
    s = re.sub(r"^\s*#+\s*", "", s, flags=re.MULTILINE)
    s = re.sub(r"^\s*[-*•]\s+", "", s, flags=re.MULTILINE)

    # Remove backticks and blockquotes
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"^\s*>\s*", "", s, flags=re.MULTILINE)

    # Normalize acronyms so they are pronounced clearly as initials
    s = re.sub(r"\bAI\b", "A.I.", s)
    s = re.sub(r"\bCRM\b", "C.R.M.", s)
    s = re.sub(r"\bAPI\b", "A.P.I.", s)
    s = re.sub(r"\bAPIs\b", "A.P.I.s", s)
    s = re.sub(r"\bDNC\b", "D.N.C.", s)
    s = re.sub(r"\bSaaS\b", "Sass", s)
    s = re.sub(r"\bSMS\b", "S.M.S.", s)
    s = re.sub(r"\bURL\b", "U.R.L.", s)

    # Expand colloquial time / units for smooth phone speech
    s = re.sub(r"\b15-min\b", "fifteen minute", s, flags=re.IGNORECASE)
    s = re.sub(r"\b15\s*min\b", "fifteen minute", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(\d+)\s*mins\b", r"\1 minutes", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(\d+)\s*min\b", r"\1 minute", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(\d+)\s*hrs\b", r"\1 hours", s, flags=re.IGNORECASE)
    s = re.sub(r"\b(\d+)\s*hr\b", r"\1 hour", s, flags=re.IGNORECASE)
    s = re.sub(r"\b₹\s*(\d+)", r"\1 rupees", s)

    # Strip excess whitespace
    s = re.sub(r"\s+", " ", s).strip()

    return s


def is_devanagari_hindi(text: str) -> bool:
    """Detects if text contains Devanagari Hindi characters."""
    return bool(re.search(r"[\u0900-\u097F]", text))


class TTSService:
    """
    Production-grade Neural TTS Service delivering ultra-realistic,
    emotionally expressive human speech with natural Indian English and multilingual cadence.
    """

    @classmethod
    def resolve_voice(cls, voice_name: Optional[str] = None, text: Optional[str] = None) -> str:
        """Resolves requested voice profile name to Microsoft Edge Neural voice identifier."""
        if text and is_devanagari_hindi(text):
            return "hi-IN-SwaraNeural"

        if not voice_name:
            return DEFAULT_NEURAL_VOICE

        key = voice_name.strip().lower()
        # Direct match or partial match in VOICE_MAP
        if key in VOICE_MAP:
            return VOICE_MAP[key]

        for k, v in VOICE_MAP.items():
            if k in key:
                return v

        # If user passed a full edge-tts voice string e.g. "en-IN-NeerjaNeural"
        if "neural" in key:
            return voice_name

        return DEFAULT_NEURAL_VOICE

    @classmethod
    async def synthesize_to_bytes(
        cls,
        text: str,
        voice_name: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ) -> bytes:
        """
        Synthesizes text into high-fidelity MP3 neural audio bytes.
        Includes automatic fallback if expressive preview voice encounters network restrictions.
        """
        clean_text = normalize_text_for_speech(text)
        if not clean_text:
            return b""

        primary_voice = cls.resolve_voice(voice_name, clean_text)
        voices_to_try = [primary_voice]
        if primary_voice != FALLBACK_NEURAL_VOICE:
            voices_to_try.append(FALLBACK_NEURAL_VOICE)

        for voice in voices_to_try:
            try:
                communicate = edge_tts.Communicate(clean_text, voice, rate=rate, pitch=pitch)
                audio_chunks = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_chunks.append(chunk["data"])
                audio_data = b"".join(audio_chunks)
                if audio_data:
                    return audio_data
            except Exception as exc:
                logger.warning(f"[TTSService] Synthesis failed with voice {voice}: {exc}")

        return b""

    @classmethod
    async def synthesize_to_base64(
        cls,
        text: str,
        voice_name: Optional[str] = None,
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ) -> str:
        """Synthesizes text and returns standard Base64-encoded MP3 audio string."""
        audio_bytes = await cls.synthesize_to_bytes(text, voice_name, rate, pitch)
        if not audio_bytes:
            return ""
        return base64.b64encode(audio_bytes).decode("utf-8")


tts_service = TTSService()
