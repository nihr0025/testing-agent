import logging
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from backend.models.schemas import (
    SettingsModel,
    UpdateSettingsRequest,
    ModelInfo,
    ProviderTestResult,
    ValidateModelRequest,
    ValidateModelResponse
)
from backend.config import config
from backend.services.model_registry import model_registry
from backend.services.model_discovery_service import model_discovery_service

logger = logging.getLogger("testing_platform.routes.settings")
router = APIRouter(prefix="/api/settings", tags=["Configuration & Settings"])

@router.get("", response_model=SettingsModel)
def get_settings():
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

@router.post("")
def update_settings(req: UpdateSettingsRequest):
    if req.openai_model is not None and req.openai_model.strip():
        config.OPENAI_MODEL = req.openai_model.strip()
    if req.gemini_model is not None and req.gemini_model.strip():
        config.GEMINI_MODEL = req.gemini_model.strip()
    if req.default_testing_mode is not None and req.default_testing_mode.strip():
        val = req.default_testing_mode.lower().strip()
        if val in ["basic", "gemini", "openai"]:
            config.DEFAULT_TESTING_MODE = val
    if req.default_automation_framework is not None:
        val = req.default_automation_framework.lower().strip()
        if val in ["playwright", "selenium"]:
            config.DEFAULT_AUTOMATION_FRAMEWORK = val
    if req.jira_url is not None:
        config.JIRA_URL = req.jira_url.strip()
    if req.jira_email is not None:
        config.JIRA_EMAIL = req.jira_email.strip()
    if req.jira_api_token is not None and req.jira_api_token.strip():
        config.JIRA_API_TOKEN = req.jira_api_token.strip()
    if req.jira_mcp_url is not None:
        config.JIRA_MCP_URL = req.jira_mcp_url.strip()

    return {
        "status": "success",
        "message": "Settings updated successfully (Credentials remain exclusively in .env).",
        "settings": {
            "default_testing_mode": config.DEFAULT_TESTING_MODE,
            "default_automation_framework": config.DEFAULT_AUTOMATION_FRAMEWORK,
            "openai_model": config.OPENAI_MODEL,
            "gemini_model": config.GEMINI_MODEL,
            "openai_configured": config.is_openai_configured(),
            "gemini_configured": config.is_gemini_configured()
        }
    }

@router.get("/models", response_model=List[ModelInfo])
def list_provider_models(
    provider: str = Query("gemini", description="gemini, openai, or basic"),
    refresh: bool = Query(False, description="Set true to force live discovery from provider API")
):
    """Returns dynamically discovered compatible models for the selected provider."""
    try:
        disc = model_discovery_service.discover_models(provider, force_refresh=refresh)
        models = disc.get("models", [])
        return [
            ModelInfo(
                id=m["id"],
                name=m["name"],
                description=m.get("description", ""),
                is_free_tier=m.get("is_free_tier", False),
                is_default=m.get("is_default", False)
            )
            for m in models
        ]
    except Exception as e:
        logger.error(f"Error fetching models for provider {provider}: {e}")
        return []

@router.post("/validate-model", response_model=ValidateModelResponse)
def validate_model_selection(
    req: ValidateModelRequest,
    provider: str = Query("gemini", description="gemini or openai")
):
    """Safely verifies generation capability on the selected model with a minimal test probe."""
    res = model_discovery_service.validate_model_selection(provider, req.model_id)
    return ValidateModelResponse(
        valid=res["valid"],
        provider=provider,
        model_id=res["model_id"],
        latency_ms=res.get("latency_ms", 0),
        message=res["message"],
        error_type=res.get("error_type")
    )

@router.post("/test-provider", response_model=ProviderTestResult)
def test_provider_connection(provider: str = Query("gemini", description="gemini or openai")):
    """Tests provider API credentials and connection safely."""
    try:
        result = model_registry.validate_provider(provider)
        return ProviderTestResult(
            valid=result.get("valid", False),
            status=result.get("status", "invalid"),
            message=result.get("message", "Validation completed."),
            provider=result.get("provider", provider),
            model=result.get("model")
        )
    except Exception as e:
        logger.error(f"Provider test failed for {provider}: {e}")
        return ProviderTestResult(
            valid=False,
            status="error",
            message=f"Validation failed: {str(e)}",
            provider=provider,
            model=None
        )

@router.post("/test-ai")
def test_ai_legacy(provider: Optional[str] = None):
    """Legacy endpoint for compatibility."""
    target_prov = provider or ("openai" if config.is_openai_configured() else "gemini" if config.is_gemini_configured() else "openai")
    return test_provider_connection(target_prov)
