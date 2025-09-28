"""
LLM provider factory for creating providers securely.
"""

import logging
from typing import Dict, Any

from .base import BaseLLMProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider
from .demo_provider import DemoProvider

logger = logging.getLogger(__name__)


def create_llm_provider(provider_name: str, config: Dict[str, Any]) -> BaseLLMProvider:
    """
    Create an LLM provider instance based on the provider name.

    Args:
        provider_name: Name of the provider (openai, anthropic, ollama, demo)
        config: Configuration dictionary for the provider

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If provider name is not supported
        Exception: If provider configuration is invalid
    """
    provider_name = provider_name.lower().strip()

    provider_map = {
        "openai": OpenAIProvider,
        "gpt": OpenAIProvider,  # Alias
        "anthropic": AnthropicProvider,
        "claude": AnthropicProvider,  # Alias
        "ollama": OllamaProvider,
        "local": OllamaProvider,  # Alias
        "demo": DemoProvider,
        "test": DemoProvider,  # Alias
    }

    if provider_name not in provider_map:
        available_providers = list(set(provider_map.keys()))
        raise ValueError(
            f"Unsupported provider: {provider_name}. "
            f"Available providers: {', '.join(available_providers)}"
        )

    provider_class = provider_map[provider_name]

    try:
        logger.info(f"Creating {provider_class.__name__} with model {config.get('model', 'default')}")
        return provider_class(config)

    except Exception as e:
        logger.error(f"Failed to create {provider_class.__name__}: {e}")
        raise ValueError(f"Failed to initialize {provider_name} provider: {str(e)}")


def get_available_providers() -> Dict[str, str]:
    """Get list of available providers with descriptions."""
    return {
        "openai": "OpenAI GPT models (requires API key)",
        "anthropic": "Anthropic Claude models (requires API key)",
        "ollama": "Local Ollama models (requires local installation)",
        "demo": "Demo provider for testing (no API key required)"
    }


def validate_provider_config(provider_name: str, config: Dict[str, Any]) -> Dict[str, str]:
    """
    Validate provider configuration and return any errors.

    Args:
        provider_name: Name of the provider
        config: Configuration dictionary

    Returns:
        Dictionary of field -> error message for any validation errors
    """
    errors = {}

    try:
        # Try to create a temporary instance to validate config
        provider_class = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "ollama": OllamaProvider,
            "demo": DemoProvider
        }.get(provider_name.lower())

        if not provider_class:
            errors["provider"] = f"Unknown provider: {provider_name}"
            return errors

        # Check required fields
        required_fields = provider_class({}).get_required_config_fields()
        for field in required_fields:
            if not config.get(field):
                errors[field] = f"Required field {field} is missing or empty"

        # Validate common fields
        if "max_tokens" in config:
            max_tokens = config["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                errors["max_tokens"] = "max_tokens must be a positive integer"

        if "temperature" in config:
            temperature = config["temperature"]
            if not isinstance(temperature, (int, float)) or not 0 <= temperature <= 2:
                errors["temperature"] = "temperature must be between 0 and 2"

        if "timeout" in config:
            timeout = config["timeout"]
            if not isinstance(timeout, int) or timeout <= 0:
                errors["timeout"] = "timeout must be a positive integer"

    except Exception as e:
        errors["config"] = f"Configuration validation error: {str(e)}"

    return errors