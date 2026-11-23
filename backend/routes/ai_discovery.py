import logging
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Path
from backend.models.schemas import (
    ProviderInfoModel,
    DiscoveryResultModel,
    ValidateModelRequest,
    ValidateModelResponse,
    ModelInfo,
    SettingsModel
)
from backend.config import config
from backend.services.model_registry import model_registry
from backend.services.model_discovery_service import model_discovery_service

logger = logging.getLogger("testing_platform.routes.ai_discovery")
router = APIRouter(prefix="/api/ai", tags=["AI Model Discovery & Validation"])

@router.get("/providers", response_model=List[ProviderInfoModel])
def get_providers():
    """Returns available AI providers and their configuration status."""
    providers = model_registry.get_available_providers()
    return [
        ProviderInfoModel(
            id=p["id"],
            name=p["name"],
            badge=p["badge"],
            description=p["description"],
            is_configured=p["is_configured"],
            masked_key=p["masked_key"],
            env_var=p.get("env_var"),
            default_model=p.get("default_model")
        )
        for p in providers
    ]

@router.get("/models/{provider}", response_model=DiscoveryResultModel)
def get_provider_models(
    provider: str = Path(..., description="Provider name: gemini, openai, or basic"),
    refresh: bool = Query(False, description="Set true to bypass cache and query the provider API directly")
):
    """
    Dynamically discovers compatible models from the provider API.
    Never returns hardcoded fallback models if discovery fails.
    """
    prov_key = provider.lower().strip()
    result = model_discovery_service.discover_models(prov_key, force_refresh=refresh)

    models_data = [
        ModelInfo(
            id=m["id"],
            name=m["name"],
            description=m.get("description", ""),
            is_free_tier=m.get("is_free_tier", False),
            is_default=m.get("is_default", False)
        )
        for m in result.get("models", [])
    ]

    return DiscoveryResultModel(
        provider=prov_key,
        models=models_data,
        cached=result.get("cached", False),
        cache_age_seconds=result.get("cache_age_seconds", 0.0),
        error=result.get("error"),
        error_type=result.get("error_type"),
        message=result.get("message", "")
    )

@router.post("/validate/{provider}", response_model=ValidateModelResponse)
def validate_provider_model(
    req: ValidateModelRequest,
    provider: str = Path(..., description="Provider name: gemini, openai, or basic")
):
    """
    Validates a specific selected model with a real, safe minimal test generation request.
    """
    prov_key = provider.lower().strip()
    res = model_discovery_service.validate_model_selection(prov_key, req.model_id)
    return ValidateModelResponse(
        valid=res["valid"],
        provider=prov_key,
        model_id=res["model_id"],
        latency_ms=res.get("latency_ms", 0),
        message=res["message"],
        error_type=res.get("error_type")
    )

@router.get("/configuration/status", response_model=SettingsModel)
def get_ai_configuration_status():
    """Returns the current environment credential status and model configuration."""
    config.reload_from_env()
    instructions = {
        "openai": "To enable OpenAI API Mode, add OPENAI_API_KEY=sk-... to your backend .env file.",
        "gemini": "To enable Gemini API Mode, add GEMINI_API_KEY=your_key to your backend .env file. Free tier is available via Google AI Studio.",
        "basic": "Basic Testing Mode requires no credentials and is always available."
    }
    return SettingsModel(
        default_testing_mode=config.DEFAULT_TESTING_MODE or "basic",
        default_automation_framework=config.DEFAULT_AUTOMATION_FRAMEWORK or "playwright",
        openai_configured=config.is_openai_configured(),
        openai_model=config.OPENAI_MODEL,
        openai_masked_key=config.get_masked_key(config.OPENAI_API_KEY),
        gemini_configured=config.is_gemini_configured(),
        gemini_model=config.GEMINI_MODEL,
        gemini_masked_key=config.get_masked_key(config.GEMINI_API_KEY or config.GOOGLE_API_KEY),
        jira_configured=config.is_jira_configured(),
        jira_url=config.JIRA_URL,
        jira_email=config.JIRA_EMAIL,
        jira_mcp_url=config.JIRA_MCP_URL,
        instructions=instructions
    )
