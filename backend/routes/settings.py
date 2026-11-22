from fastapi import APIRouter
from backend.models.schemas import SettingsModel, UpdateSettingsRequest
from backend.config import config

router = APIRouter(prefix="/api/settings", tags=["Configuration & Settings"])

@router.get("", response_model=SettingsModel)
def get_settings():
    return SettingsModel(
        openai_configured=config.is_openai_configured(),
        openai_model=config.OPENAI_MODEL,
        masked_api_key=config.get_masked_key(config.OPENAI_API_KEY),
        jira_configured=config.is_jira_configured(),
        jira_url=config.JIRA_URL,
        jira_email=config.JIRA_EMAIL,
        default_automation_framework=config.DEFAULT_AUTOMATION_FRAMEWORK,
        jira_mcp_url=config.JIRA_MCP_URL,
        default_generation_mode="ai" if config.is_openai_configured() else "basic"
    )

@router.post("")
def update_settings(req: UpdateSettingsRequest):
    if req.openai_api_key is not None and req.openai_api_key.strip():
        config.OPENAI_API_KEY = req.openai_api_key.strip()
    if req.openai_model is not None and req.openai_model.strip():
        config.OPENAI_MODEL = req.openai_model.strip()
    if req.jira_url is not None:
        config.JIRA_URL = req.jira_url.strip()
    if req.jira_email is not None:
        config.JIRA_EMAIL = req.jira_email.strip()
    if req.jira_api_token is not None and req.jira_api_token.strip():
        config.JIRA_API_TOKEN = req.jira_api_token.strip()
    if req.default_automation_framework is not None:
        val = req.default_automation_framework.lower().strip()
        if val in ["playwright", "selenium"]:
            config.DEFAULT_AUTOMATION_FRAMEWORK = val
    if req.jira_mcp_url is not None:
        config.JIRA_MCP_URL = req.jira_mcp_url.strip()

    return {
        "status": "success",
        "message": "Settings updated successfully.",
        "settings": {
            "openai_configured": config.is_openai_configured(),
            "openai_model": config.OPENAI_MODEL,
            "masked_api_key": config.get_masked_key(config.OPENAI_API_KEY),
            "jira_configured": config.is_jira_configured(),
            "default_automation_framework": config.DEFAULT_AUTOMATION_FRAMEWORK,
            "default_generation_mode": "ai" if config.is_openai_configured() else "basic"
        }
    }

@router.post("/test-ai")
def test_openai_connection():
    if not config.is_openai_configured():
        return {
            "valid": False,
            "error_type": "MissingKey",
            "message": "OpenAI API Key is not set. Basic Testing Mode is enabled and ready to use without an API key."
        }
    try:
        from openai import OpenAI
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        client.models.list()
        return {
            "valid": True,
            "message": f"OpenAI API key verified successfully! AI-Powered Testing Mode is active with model '{config.OPENAI_MODEL}'."
        }
    except Exception as e:
        err_str = str(e)
        if "Authentication" in type(e).__name__ or "401" in err_str:
            return {
                "valid": False,
                "error_type": "AuthenticationError",
                "message": "Authentication failed (401): The provided OpenAI API key is invalid or expired. You can use Basic Testing Mode instead."
            }
        elif "RateLimit" in type(e).__name__ or "429" in err_str or "quota" in err_str.lower():
            return {
                "valid": False,
                "error_type": "QuotaExceeded",
                "message": "OpenAI Quota Exceeded / Rate Limit (429): You have run out of API credits. TraceAI Studio offers Basic Testing Mode to continue testing without API limits."
            }
        else:
            return {
                "valid": False,
                "error_type": "APIError",
                "message": f"OpenAI API check returned error: {err_str[:120]}. Basic Testing Mode is available."
            }
