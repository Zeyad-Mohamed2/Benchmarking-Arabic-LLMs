"""
This file defines custom exception classes for the benchmark system.
It provides specific error types for data loading, client operations, and evaluation failures.
"""

from typing import Optional, Dict, Any


class BenchmarkError(Exception):
    """Base exception for benchmark errors."""

    pass


class DataLoadError(BenchmarkError):
    """Raised when data loading fails."""

    pass


class ClientError(BenchmarkError):
    """Raised when client operations fail.
    
    Attributes:
        message: Error message
        error_type: Type of error (e.g., 'rate_limit', 'payment', 'timeout', 'api_error')
        error_details: Additional error details (status code, headers, etc.)
    """

    def __init__(
        self,
        message: str,
        error_type: str = "api_error",
        error_details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.error_details = error_details or {}

    def __str__(self):
        return self.message


class RateLimitError(ClientError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ):
        details = error_details or {}
        if retry_after:
            details['retry_after'] = retry_after
        super().__init__(message, error_type="rate_limit", error_details=details)
        self.retry_after = retry_after


class PaymentError(ClientError):
    """Raised when payment/billing issues occur."""

    def __init__(self, message: str, error_details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_type="payment", error_details=error_details)


class TokenLimitError(ClientError):
    """Raised when token limit is exceeded."""

    def __init__(self, message: str, error_details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_type="token_limit", error_details=error_details)


class TimeoutError(ClientError):
    """Raised when request times out."""

    def __init__(self, message: str, error_details: Optional[Dict[str, Any]] = None):
        super().__init__(message, error_type="timeout", error_details=error_details)


class EvaluationError(BenchmarkError):
    """Raised when evaluation fails."""

    pass
