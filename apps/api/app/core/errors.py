from typing import Any, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel
from app.core.logging import request_id_ctx


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    details: Optional[Any] = None


class StandardErrorResponse(BaseModel):
    error: ErrorDetail


class VeyraException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class NotFoundError(VeyraException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource} with identifier '{identifier}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class AuthenticationError(VeyraException):
    def __init__(self, message: str = "Authentication failed or token expired."):
        super().__init__(
            code="AUTHENTICATION_FAILED",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class PermissionDeniedError(VeyraException):
    def __init__(self, message: str = "Permission denied."):
        super().__init__(
            code="PERMISSION_DENIED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class DNCViolationError(VeyraException):
    def __init__(self, phone: str):
        super().__init__(
            code="DO_NOT_CALL_VIOLATION",
            message=f"Phone number is on the permanent Do-Not-Call (DNC) list and cannot be called.",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"phone": phone}
        )


class ProviderError(VeyraException):
    def __init__(self, provider: str, message: str, details: Optional[Any] = None):
        super().__init__(
            code=f"{provider.upper()}_PROVIDER_ERROR",
            message=f"Error in {provider} integration: {message}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


def format_error_response(exc: VeyraException) -> dict:
    req_id = request_id_ctx.get()
    return {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "request_id": req_id,
            "details": exc.details,
        }
    }
