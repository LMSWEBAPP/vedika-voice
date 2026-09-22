import logging
import re
import sys
from contextvars import ContextVar
from typing import Optional

request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def mask_phone_number(phone: Optional[str]) -> str:
    """
    Mask phone number for data privacy compliance.
    Example: '+919876543210' -> '+91******3210'
    """
    if not phone:
        return ""
    clean = phone.strip()
    if len(clean) <= 4:
        return "****"
    # Keep leading country code / first 3 chars, mask middle, keep last 4 digits
    if clean.startswith("+"):
        prefix = clean[:3]
        suffix = clean[-4:]
        masked_length = max(len(clean) - 7, 3)
        return f"{prefix}{'*' * masked_length}{suffix}"
    else:
        suffix = clean[-4:]
        masked_length = max(len(clean) - 4, 3)
        return f"{'*' * masked_length}{suffix}"


class StructuredFormatter(logging.Formatter):
    """Formats logs with correlation IDs, masking sensitive fields."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        corr_id = correlation_id_ctx.get()
        
        prefix_parts = []
        if req_id:
            prefix_parts.append(f"[req:{req_id}]")
        if corr_id:
            prefix_parts.append(f"[corr:{corr_id}]")
        
        prefix = " ".join(prefix_parts)
        original_msg = super().format(record)
        
        # Mask phone numbers in formatted log messages
        # Look for regex patterns resembling phone numbers: +?[\d\s-]{8,15}
        masked_msg = re.sub(
            r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            lambda m: mask_phone_number(m.group(0)),
            original_msg
        )
        
        if prefix:
            return f"{prefix} {masked_msg}"
        return masked_msg


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger("veyra")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        formatter = StructuredFormatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger


logger = setup_logging()
