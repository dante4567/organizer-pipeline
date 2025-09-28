"""
Anthropic Claude provider with proper async handling.
"""

import logging
from typing import Dict, Any
import httpx

from .base import BaseLLMProvider, LLMResponse, LLMError, LLMErrorType

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """Secure Anthropic Claude provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.anthropic.com/v1")

        if not self.api_key:
            raise ValueError("Anthropic API key is required")

        # Claude-specific rate limiting
        self._min_request_interval = 0.2  # 5 requests per second max

    def get_required_config_fields(self) -> list[str]:
        """Required configuration fields for Anthropic."""
        return ["api_key"]

    async def _make_request(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """Make request to Anthropic API."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        # Format prompt for Claude
        formatted_prompt = prompt
        if system_prompt:
            formatted_prompt = f"System: {system_prompt}\n\nHuman: {prompt}\n\nAssistant:"
        else:
            formatted_prompt = f"Human: {prompt}\n\nAssistant:"

        payload = {
            "model": self.model,
            "prompt": formatted_prompt,
            "max_tokens_to_sample": self.max_tokens,
            "temperature": self.temperature
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/complete",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 401:
                    raise LLMError("Invalid Anthropic API key", LLMErrorType.AUTHENTICATION, 401)
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise LLMError("Rate limit exceeded", LLMErrorType.RATE_LIMIT, 429, retry_after)
                elif response.status_code >= 500:
                    raise LLMError("Anthropic server error", LLMErrorType.SERVER_ERROR, response.status_code)
                elif response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                    raise LLMError(f"Anthropic API error: {error_msg}", LLMErrorType.INVALID_REQUEST, response.status_code)

                data = response.json()

                if "completion" not in data:
                    raise LLMError("No completion from Anthropic", LLMErrorType.INVALID_REQUEST)

                content = data["completion"].strip()

                return LLMResponse(
                    content=content,
                    model=data.get("model", self.model),
                    tokens_used=data.get("usage", {}).get("total_tokens"),
                    finish_reason=data.get("stop_reason"),
                    metadata={
                        "usage": data.get("usage", {}),
                        "response_id": data.get("id")
                    }
                )

            except httpx.RequestError as e:
                logger.error(f"Anthropic request error: {e}")
                raise LLMError(f"Network error: {str(e)}", LLMErrorType.TIMEOUT)
            except httpx.TimeoutException:
                raise LLMError("Request to Anthropic timed out", LLMErrorType.TIMEOUT)