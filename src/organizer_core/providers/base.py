"""
Base LLM provider with security and proper async patterns.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
import time
from enum import Enum

logger = logging.getLogger(__name__)


class LLMErrorType(str, Enum):
    """LLM error types for better error handling."""
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    INVALID_REQUEST = "invalid_request"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class LLMResponse:
    """Structured LLM response with metadata."""
    content: str
    model: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMError(Exception):
    """Custom LLM error with structured information."""

    def __init__(self, message: str, error_type: LLMErrorType = LLMErrorType.UNKNOWN,
                 status_code: Optional[int] = None, retry_after: Optional[int] = None):
        super().__init__(message)
        self.error_type = error_type
        self.status_code = status_code
        self.retry_after = retry_after


class BaseLLMProvider(ABC):
    """
    Secure base class for all LLM providers.
    Implements proper async patterns, error handling, and security.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "unknown")
        self.max_tokens = config.get("max_tokens", 2000)
        self.temperature = config.get("temperature", 0.3)
        self.timeout = config.get("timeout", 30)

        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum seconds between requests

        # Validation
        self._validate_config()

    def _validate_config(self) -> None:
        """Validate provider configuration."""
        required_fields = self.get_required_config_fields()
        for field in required_fields:
            if field not in self.config:
                raise ValueError(f"Missing required config field: {field}")

        # Validate numeric values
        if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
            raise ValueError("max_tokens must be a positive integer")

        if not isinstance(self.temperature, (int, float)) or not 0 <= self.temperature <= 2:
            raise ValueError("temperature must be between 0 and 2")

        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise ValueError("timeout must be a positive integer")

    @abstractmethod
    def get_required_config_fields(self) -> list[str]:
        """Return list of required configuration fields."""
        pass

    async def _rate_limit(self) -> None:
        """Implement basic rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)

        self._last_request_time = time.time()

    def _sanitize_prompt(self, prompt: str) -> str:
        """Sanitize user input to prevent prompt injection."""
        if not isinstance(prompt, str):
            raise ValueError("Prompt must be a string")

        # Limit prompt length
        max_prompt_length = 10000
        if len(prompt) > max_prompt_length:
            logger.warning(f"Prompt truncated from {len(prompt)} to {max_prompt_length} characters")
            prompt = prompt[:max_prompt_length]

        # Remove potentially dangerous patterns
        dangerous_patterns = [
            "IGNORE PREVIOUS INSTRUCTIONS",
            "SYSTEM:",
            "\\n\\n---\\n\\n",
            "```system",
        ]

        prompt_upper = prompt.upper()
        for pattern in dangerous_patterns:
            if pattern in prompt_upper:
                logger.warning(f"Potentially dangerous pattern detected in prompt: {pattern}")
                prompt = prompt.replace(pattern, "[FILTERED]")
                prompt = prompt.replace(pattern.lower(), "[FILTERED]")

        return prompt.strip()

    def _sanitize_system_prompt(self, system_prompt: str) -> str:
        """Sanitize system prompt."""
        if not system_prompt:
            return ""

        # System prompts should be more restricted
        max_system_length = 1000
        if len(system_prompt) > max_system_length:
            system_prompt = system_prompt[:max_system_length]

        return system_prompt.strip()

    @abstractmethod
    async def _make_request(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """Make the actual API request. Must be implemented by subclasses."""
        pass

    async def generate_response(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """
        Generate response with full security and error handling.
        """
        start_time = time.time()

        try:
            # Rate limiting
            await self._rate_limit()

            # Input sanitization
            clean_prompt = self._sanitize_prompt(prompt)
            clean_system_prompt = self._sanitize_system_prompt(system_prompt)

            logger.info(f"Making LLM request to {self.__class__.__name__} with model {self.model}")

            # Make the request with timeout
            response = await asyncio.wait_for(
                self._make_request(clean_prompt, clean_system_prompt),
                timeout=self.timeout
            )

            response.response_time = time.time() - start_time
            logger.info(f"LLM request completed in {response.response_time:.2f}s")

            return response

        except asyncio.TimeoutError:
            error_msg = f"Request timed out after {self.timeout} seconds"
            logger.error(error_msg)
            raise LLMError(error_msg, LLMErrorType.TIMEOUT)

        except LLMError:
            # Re-raise LLM errors as-is
            raise

        except Exception as e:
            error_msg = f"Unexpected error in {self.__class__.__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise LLMError(error_msg, LLMErrorType.UNKNOWN)

    async def health_check(self) -> bool:
        """Check if the provider is healthy and can make requests."""
        try:
            response = await self.generate_response("Hello", "Respond with 'OK'")
            return "OK" in response.content.upper()
        except Exception as e:
            logger.error(f"Health check failed for {self.__class__.__name__}: {e}")
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "provider": self.__class__.__name__,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout
        }