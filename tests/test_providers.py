"""
Unit tests for LLM providers.
"""

import pytest
from organizer_core.providers import (
    create_llm_provider,
    DemoProvider,
    OpenAIProvider,
    AnthropicProvider,
    OllamaProvider
)
from organizer_core.providers.base import LLMResponse


class TestProviderFactory:
    """Tests for LLM provider factory."""

    @pytest.mark.unit
    def test_create_demo_provider(self):
        """Test creating demo provider."""
        provider = create_llm_provider("demo", {"model": "demo"})
        assert isinstance(provider, DemoProvider)

    @pytest.mark.unit
    def test_create_openai_provider(self):
        """Test creating OpenAI provider."""
        provider = create_llm_provider("openai", {
            "model": "gpt-4",
            "api_key": "test-key"
        })
        assert isinstance(provider, OpenAIProvider)

    @pytest.mark.unit
    def test_create_anthropic_provider(self):
        """Test creating Anthropic provider."""
        provider = create_llm_provider("anthropic", {
            "model": "claude-3-opus",
            "api_key": "test-key"
        })
        assert isinstance(provider, AnthropicProvider)

    @pytest.mark.unit
    def test_create_ollama_provider(self):
        """Test creating Ollama provider."""
        provider = create_llm_provider("ollama", {
            "model": "llama2",
            "base_url": "http://localhost:11434"
        })
        assert isinstance(provider, OllamaProvider)

    @pytest.mark.unit
    def test_invalid_provider_type(self):
        """Test that invalid provider type raises error."""
        with pytest.raises(ValueError, match="Unknown provider"):
            create_llm_provider("invalid", {})


class TestDemoProvider:
    """Tests for DemoProvider."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_demo_provider_response(self, demo_provider):
        """Test demo provider generates response."""
        response = await demo_provider.generate_response("Hello, test")
        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model == "demo-model-v1"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_demo_provider_handles_empty_message(self, demo_provider):
        """Test demo provider handles empty message."""
        response = await demo_provider.generate_response("")
        assert isinstance(response, LLLMResponse)
        assert response.content is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_demo_provider_multiple_calls(self, demo_provider):
        """Test demo provider handles multiple calls."""
        response1 = await demo_provider.generate_response("First message")
        response2 = await demo_provider.generate_response("Second message")

        assert response1.content is not None
        assert response2.content is not None
        # Responses should be similar but demo provider doesn't guarantee uniqueness

    @pytest.mark.unit
    def test_demo_provider_name(self, demo_provider):
        """Test demo provider has correct name."""
        assert demo_provider.name == "demo"

    @pytest.mark.unit
    def test_demo_provider_model(self, demo_provider):
        """Test demo provider has model set."""
        assert demo_provider.model == "demo"


class TestLLMResponse:
    """Tests for LLMResponse model."""

    @pytest.mark.unit
    def test_create_response(self):
        """Test creating LLM response."""
        response = LLMResponse(
            content="Test response",
            model="test-model",
            provider="test-provider"
        )
        assert response.content == "Test response"
        assert response.model == "test-model"
        assert response.provider == "test-provider"

    @pytest.mark.unit
    def test_response_with_metadata(self):
        """Test response with metadata."""
        response = LLMResponse(
            content="Test",
            model="test-model",
            provider="test-provider",
            metadata={"tokens": 100, "latency": 0.5}
        )
        assert response.metadata["tokens"] == 100
        assert response.metadata["latency"] == 0.5

    @pytest.mark.unit
    def test_response_requires_content(self):
        """Test that content is required."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            LLMResponse(
                model="test-model",
                provider="test-provider"
            )


class TestProviderConfiguration:
    """Tests for provider configuration."""

    @pytest.mark.unit
    def test_demo_provider_config(self):
        """Test demo provider with custom config."""
        provider = create_llm_provider("demo", {
            "model": "custom-demo-model"
        })
        assert provider.model == "custom-demo-model"

    @pytest.mark.unit
    def test_provider_requires_model(self):
        """Test that provider requires model in config."""
        # Demo provider should work without model (uses default)
        provider = create_llm_provider("demo", {})
        assert provider.model is not None
