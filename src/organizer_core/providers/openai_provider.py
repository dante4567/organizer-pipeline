"""
OpenAI provider with proper async handling and security.
"""

import logging
from typing import Dict, Any
import httpx

from .base import BaseLLMProvider, LLMResponse, LLMError, LLMErrorType

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """Secure OpenAI provider with proper async/await."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        # Rate limiting for OpenAI
        self._min_request_interval = 0.1  # 10 requests per second max

    def get_required_config_fields(self) -> list[str]:
        """Required configuration fields for OpenAI."""
        return ["api_key"]

    async def _make_request(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """Make request to OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 401:
                    raise LLMError("Invalid OpenAI API key", LLMErrorType.AUTHENTICATION, 401)
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise LLMError("Rate limit exceeded", LLMErrorType.RATE_LIMIT, 429, retry_after)
                elif response.status_code >= 500:
                    raise LLMError("OpenAI server error", LLMErrorType.SERVER_ERROR, response.status_code)
                elif response.status_code != 200:
                    error_data = response.json() if response.content else {}
                    error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
                    raise LLMError(f"OpenAI API error: {error_msg}", LLMErrorType.INVALID_REQUEST, response.status_code)

                data = response.json()

                if "choices" not in data or not data["choices"]:
                    raise LLMError("No response choices from OpenAI", LLMErrorType.INVALID_REQUEST)

                choice = data["choices"][0]
                content = choice["message"]["content"]

                return LLMResponse(
                    content=content,
                    model=data.get("model", self.model),
                    tokens_used=data.get("usage", {}).get("total_tokens"),
                    finish_reason=choice.get("finish_reason"),
                    metadata={
                        "usage": data.get("usage", {}),
                        "response_id": data.get("id")
                    }
                )

            except httpx.RequestError as e:
                logger.error(f"OpenAI request error: {e}")
                raise LLMError(f"Network error: {str(e)}", LLMErrorType.TIMEOUT)
            except httpx.TimeoutException:
                raise LLMError("Request to OpenAI timed out", LLMErrorType.TIMEOUT)