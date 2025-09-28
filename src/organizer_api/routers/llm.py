"""
LLM API router for natural language processing.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from organizer_core.providers import LLMError, LLMErrorType
from organizer_core.validation.validators import InputValidator, ValidationError
from ..services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter()


class LLMRequest(BaseModel):
    """Request model for LLM interactions."""
    prompt: str = Field(..., min_length=1, max_length=10000, description="User prompt")
    system_prompt: Optional[str] = Field(None, max_length=1000, description="System prompt")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class LLMResponse(BaseModel):
    """Response model for LLM interactions."""
    response: str
    model: str
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None
    context_understood: bool = True


def get_llm_service(request: Request) -> LLMService:
    """Get LLM service from application state."""
    return request.app.state.llm_service


@router.post("/chat", response_model=LLMResponse)
async def chat_with_llm(
    request: LLMRequest,
    llm_service: LLMService = Depends(get_llm_service)
) -> LLMResponse:
    """
    Chat with the LLM for natural language processing.

    This endpoint processes user input and returns AI-generated responses
    for calendar, task, and contact management.
    """
    try:
        # Validate input
        clean_prompt = InputValidator.validate_text(
            request.prompt,
            "prompt",
            min_length=1,
            max_length=10000
        )

        clean_system_prompt = ""
        if request.system_prompt:
            clean_system_prompt = InputValidator.validate_text(
                request.system_prompt,
                "system_prompt",
                max_length=1000
            )

        # Process with LLM service
        result = await llm_service.process_user_input(
            clean_prompt,
            clean_system_prompt,
            request.context or {}
        )

        return LLMResponse(
            response=result.content,
            model=result.model,
            tokens_used=result.tokens_used,
            response_time=result.response_time,
            context_understood=True
        )

    except ValidationError as e:
        logger.warning(f"Validation error in LLM chat: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input: {e}")

    except LLMError as e:
        logger.error(f"LLM error: {e}")
        if e.error_type == LLMErrorType.AUTHENTICATION:
            raise HTTPException(status_code=401, detail="LLM authentication failed")
        elif e.error_type == LLMErrorType.RATE_LIMIT:
            raise HTTPException(
                status_code=429,
                detail="LLM rate limit exceeded",
                headers={"Retry-After": str(e.retry_after or 60)}
            )
        elif e.error_type == LLMErrorType.TIMEOUT:
            raise HTTPException(status_code=504, detail="LLM request timed out")
        else:
            raise HTTPException(status_code=500, detail="LLM service error")

    except Exception as e:
        logger.error(f"Unexpected error in LLM chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/providers", response_model=Dict[str, Any])
async def get_available_providers(
    llm_service: LLMService = Depends(get_llm_service)
) -> Dict[str, Any]:
    """Get information about available LLM providers."""
    try:
        return {
            "current_provider": llm_service.get_current_provider_info(),
            "available_providers": llm_service.get_available_providers(),
            "health_status": await llm_service.health_check()
        }
    except Exception as e:
        logger.error(f"Error getting provider info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get provider information")


@router.post("/health-check", response_model=Dict[str, bool])
async def llm_health_check(
    llm_service: LLMService = Depends(get_llm_service)
) -> Dict[str, bool]:
    """Check health of the LLM service."""
    try:
        is_healthy = await llm_service.health_check()
        return {
            "healthy": is_healthy,
            "provider_available": is_healthy
        }
    except Exception as e:
        logger.error(f"LLM health check failed: {e}", exc_info=True)
        return {
            "healthy": False,
            "provider_available": False
        }