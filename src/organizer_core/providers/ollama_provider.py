"""
Ollama local provider with proper async handling.
"""

import logging
from typing import Dict, Any
import httpx

from .base import BaseLLMProvider, LLMResponse, LLMError, LLMErrorType

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Secure Ollama local provider."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "http://localhost:11434")

        # Ollama typically runs locally, so more permissive rate limiting
        self._min_request_interval = 0.05  # 20 requests per second max

    def get_required_config_fields(self) -> list[str]:
        """Ollama only requires base_url, which has a default."""
        return []

    async def _make_request(self, prompt: str, system_prompt: str = "") -> LLMResponse:
        """Make request to Ollama API."""
        headers = {
            "Content-Type": "application/json"
        }

        # Format prompt for Ollama
        formatted_prompt = prompt
        if system_prompt:
            formatted_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"

        payload = {
            "model": self.model,
            "prompt": formatted_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )

                if response.status_code == 404:
                    raise LLMError(
                        f"Model {self.model} not found in Ollama. Please pull the model first.",
                        LLMErrorType.INVALID_REQUEST,
                        404
                    )
                elif response.status_code >= 500:
                    raise LLMError("Ollama server error", LLMErrorType.SERVER_ERROR, response.status_code)
                elif response.status_code != 200:
                    error_msg = f"Ollama API error: HTTP {response.status_code}"
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", error_msg)
                    except:
                        pass
                    raise LLMError(error_msg, LLMErrorType.INVALID_REQUEST, response.status_code)

                data = response.json()

                if "response" not in data:
                    raise LLMError("No response from Ollama", LLMErrorType.INVALID_REQUEST)

                content = data["response"].strip()

                return LLMResponse(
                    content=content,
                    model=data.get("model", self.model),
                    tokens_used=data.get("eval_count"),  # Ollama uses eval_count for output tokens
                    finish_reason="stop" if data.get("done", False) else "incomplete",
                    metadata={
                        "eval_count": data.get("eval_count"),
                        "eval_duration": data.get("eval_duration"),
                        "prompt_eval_count": data.get("prompt_eval_count"),
                        "prompt_eval_duration": data.get("prompt_eval_duration"),
                        "total_duration": data.get("total_duration")
                    }
                )

            except httpx.ConnectError:
                raise LLMError(
                    f"Cannot connect to Ollama at {self.base_url}. Please ensure Ollama is running.",
                    LLMErrorType.SERVER_ERROR
                )
            except httpx.RequestError as e:
                logger.error(f"Ollama request error: {e}")
                raise LLMError(f"Network error: {str(e)}", LLMErrorType.TIMEOUT)
            except httpx.TimeoutException:
                raise LLMError("Request to Ollama timed out", LLMErrorType.TIMEOUT)