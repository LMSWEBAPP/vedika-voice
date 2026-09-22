import re
from typing import Optional
from app.core.errors import DNCViolationError


class SafetyGuard:
    """
    Guards AI calling operations against safety, compliance, and regulatory violations.
    """

    PROMPT_INJECTION_PATTERNS = [
        r"ignore (all )?previous instructions",
        r"system override",
        r"reveal your (system )?prompt",
        r"output your internal (instructions|keys|passwords)",
        r"you are now in developer mode",
    ]

    @classmethod
    def check_dnc(cls, phone: str, is_dnc: bool) -> None:
        """Enforces Do-Not-Call restrictions strictly."""
        if is_dnc:
            raise DNCViolationError(phone=phone)

    @classmethod
    def sanitize_user_input(cls, text: str) -> str:
        """Sanitizes user speech input against malicious control payloads."""
        cleaned = text.strip()
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, cleaned, re.IGNORECASE):
                return "[Filtered: Potential control override detected]"
        return cleaned

    @classmethod
    def format_ai_disclosure(cls, disclosure_template: Optional[str]) -> str:
        return disclosure_template or "This is an automated AI assistant calling on behalf of our team."
