"""
This file defines LLM client interfaces and implements an OpenRouter API client.
It handles request generation, retries with exponential backoff, error handling, and connection testing for benchmark tasks.
"""

import time
import random
import requests
from abc import ABC, abstractmethod
from benchmark_arabic_llms.core.exceptions import (
    ClientError,
    RateLimitError,
    PaymentError,
    TokenLimitError,
    TimeoutError,
)


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        """Generate response from LLM."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the client can connect to the API."""
        pass


class BaseHTTPClient(LLMClient):
    """Shared retry/request logic for HTTP-based LLM clients.

    Subclasses must set ``self.endpoint`` and implement
    ``_build_headers()`` and ``_build_request_data()``.
    """

    def __init__(self, api_key: str, model: str, max_retries: int = 3, endpoint: str = ""):
        self.api_key = api_key
        self.model = model
        self.max_retries = max_retries
        self.endpoint = endpoint

    # ------------------------------------------------------------------
    # Abstract helpers that subclasses must provide
    # ------------------------------------------------------------------

    @abstractmethod
    def _build_headers(self) -> dict:
        """Build request headers."""

    @abstractmethod
    def _build_request_data(self, prompt: str, temperature: float) -> dict:
        """Build request payload."""

    # ------------------------------------------------------------------
    # Shared implementation
    # ------------------------------------------------------------------

    def _get_retry_wait(self, attempt: int, retry_after: str | None = None) -> float:
        """Compute backoff duration with jitter and a hard cap."""
        if retry_after:
            try:
                return min(float(retry_after), 8.0) + random.uniform(0, 1)
            except ValueError:
                pass
        return min(float(2 ** attempt), 8.0) + random.uniform(0, 1)

    def generate(self, prompt: str, temperature: float = 0.0) -> str:
        """Generate a response with exponential-backoff retry logic."""
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Prompt must be a non-empty string")

        headers = self._build_headers()
        data = self._build_request_data(prompt, temperature)

        for attempt in range(self.max_retries):
            try:
                return self._make_request(headers, data)

            except requests.exceptions.HTTPError as e:
                resp = getattr(e, "response", None)
                status = getattr(resp, "status_code", None)

                error_details = {
                    "status_code": status,
                    "attempt": attempt + 1,
                    "max_retries": self.max_retries,
                }

                if resp is not None:
                    error_details["response_headers"] = dict(resp.headers)
                    try:
                        error_details["response_body"] = resp.text[:500]
                    except Exception:
                        pass

                # 429 Rate limit
                if status == 429:
                    retry_after = None
                    if resp is not None:
                        retry_after = resp.headers.get("Retry-After")

                    wait = self._get_retry_wait(attempt, retry_after)
                    if retry_after:
                        error_details["retry_after"] = retry_after

                    if attempt == self.max_retries - 1:
                        raise RateLimitError(
                            f"Rate limit exceeded after {self.max_retries} attempts",
                            retry_after=int(retry_after) if retry_after else None,
                            error_details=error_details,
                        )

                    time.sleep(wait)
                    continue

                # 402 / 403 Payment / billing
                elif status in [402, 403]:
                    response_text = resp.text.lower() if resp else ""
                    if any(kw in response_text for kw in ("payment", "billing", "quota", "credit")):
                        raise PaymentError(
                            f"Payment/billing issue: {status} {e}",
                            error_details=error_details,
                        )

                # 400 Token limit
                elif status == 400:
                    response_text = resp.text.lower() if resp else ""
                    if any(kw in response_text for kw in ("token", "max_tokens", "context_length")):
                        raise TokenLimitError(
                            f"Token limit exceeded: {e}",
                            error_details=error_details,
                        )

                # Any other HTTP error
                if attempt == self.max_retries - 1:
                    raise ClientError(
                        f"API request failed after {self.max_retries} attempts: {status} {e}",
                        error_type="http_error",
                        error_details=error_details,
                    )

                time.sleep(self._get_retry_wait(attempt))

            except requests.exceptions.Timeout:
                error_details = {
                    "attempt": attempt + 1,
                    "max_retries": self.max_retries,
                    "timeout": 30,
                }
                if attempt == self.max_retries - 1:
                    raise TimeoutError(
                        f"Request timed out after {self.max_retries} attempts",
                        error_details=error_details,
                    )
                time.sleep(self._get_retry_wait(attempt))

            except requests.exceptions.RequestException as e:
                error_details = {
                    "attempt": attempt + 1,
                    "max_retries": self.max_retries,
                    "error_class": type(e).__name__,
                }
                if attempt == self.max_retries - 1:
                    raise ClientError(
                        f"API request failed after {self.max_retries} attempts: {e}",
                        error_type="network_error",
                        error_details=error_details,
                    )
                time.sleep(self._get_retry_wait(attempt))

    def test_connection(self) -> bool:
        """Test API connection."""
        try:
            self.generate("Hello", temperature=0.0)
            return True
        except Exception:
            return False

    def _make_request(self, headers: dict, data: dict) -> str:
        """Make HTTP request and parse response."""
        response = requests.post(self.endpoint, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return self._extract_content(result)

    def _extract_content(self, result: dict) -> str:
        """Extract content from API response."""
        if "choices" not in result or not result["choices"]:
            raise ValueError("Invalid response: no choices")

        message = result["choices"][0].get("message", {})
        content = message.get("content")

        if not content:
            raise ValueError("Invalid response: no content")

        return content


class OpenRouterClient(BaseHTTPClient):
    """OpenRouter API client implementation."""

    def __init__(self, api_key: str, model: str, max_retries: int = 3):
        super().__init__(
            api_key=api_key,
            model=model,
            max_retries=max_retries,
            endpoint="https://openrouter.ai/api/v1/chat/completions",
        )

    def _build_headers(self) -> dict:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Arabic LLM Benchmark",
        }

    def _build_request_data(self, prompt: str, temperature: float) -> dict:
        """Build request payload."""
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an assistant specialized in Arabic NLP tasks.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": max(0.0, min(2.0, temperature)),
            "max_tokens": 2000,
        }


class GroqClient(BaseHTTPClient):
    """Groq API client implementation."""

    def __init__(self, api_key: str, model: str, max_retries: int = 3):
        super().__init__(
            api_key=api_key,
            model=model,
            max_retries=max_retries,
            endpoint="https://api.groq.com/openai/v1/chat/completions",
        )

    def _build_headers(self) -> dict:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_request_data(self, prompt: str, temperature: float) -> dict:
        """Build request payload."""
        return {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an assistant specialized in Arabic NLP tasks.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": max(0.0, min(2.0, temperature)),
            "max_tokens": 2000,
        }


class ClientFactory:
    """Factory for creating LLM clients."""

    @staticmethod
    def create_openrouter_client(
        api_key: str, model: str, max_retries: int = 3
    ) -> OpenRouterClient:
        """Create OpenRouter client with connection test."""
        client = OpenRouterClient(api_key=api_key, model=model, max_retries=max_retries)

        if not client.test_connection():
            raise ClientError("Failed to connect to OpenRouter API")

        return client

    @staticmethod
    def create_groq_client(
        api_key: str, model: str, max_retries: int = 3
    ) -> GroqClient:
        """Create Groq client with connection test."""
        client = GroqClient(api_key=api_key, model=model, max_retries=max_retries)

        if not client.test_connection():
            raise ClientError("Failed to connect to Groq API")

        return client
