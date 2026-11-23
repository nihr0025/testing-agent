import logging
from typing import Dict, Any, List, Optional
from backend.services.ai_provider import AIProvider
from backend.services.basic_provider import BasicProvider
from backend.services.openai_provider import OpenAIProvider
from backend.services.gemini_provider import GeminiProvider
from backend.config import config

logger = logging.getLogger("testing_platform.model_registry")

class ModelRegistry:
    """
    Central Registry for AI Providers and Model Management in TraceAI Studio.
    Provides uniform access to Basic, OpenAI, and Gemini engines.
    """
    def __init__(self):
        self._providers: Dict[str, AIProvider] = {
            "basic": BasicProvider(),
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider()
        }

    def get_provider(self, provider_name: Optional[str] = None) -> AIProvider:
        """Retrieves provider by name with fallback to basic."""
        if not provider_name:
            provider_name = config.DEFAULT_TESTING_MODE or "basic"

        key = provider_name.lower().strip()
        if key in self._providers:
            return self._providers[key]

        # Alias resolution
        if key in ["auto", "ai"]:
            if self._providers["gemini"].is_configured():
                return self._providers["gemini"]
            elif self._providers["openai"].is_configured():
                return self._providers["openai"]
            return self._providers["basic"]

        logger.warning(f"Unknown provider '{provider_name}'. Defaulting to Basic Provider.")
        return self._providers["basic"]

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Returns catalog of providers with their live configuration status."""
        return [
            {
                "id": "basic",
                "name": "Basic Testing Mode",
                "badge": "API-INDEPENDENT",
                "description": "Deterministic Python testing using accessible live page inspection (forms, inputs, links, buttons). 100% free and offline.",
                "is_configured": True,
                "masked_key": "N/A (No key required)",
                "env_var": None,
                "default_model": None
            },
            {
                "id": "openai",
                "name": "OpenAI API Mode",
                "badge": "OPENAI",
                "description": "Advanced multi-step reasoning and exploratory test analysis using GPT models.",
                "is_configured": self._providers["openai"].is_configured(),
                "masked_key": self._providers["openai"].get_masked_key(),
                "env_var": "OPENAI_API_KEY",
                "default_model": config.OPENAI_MODEL
            },
            {
                "id": "gemini",
                "name": "Google Gemini API Mode",
                "badge": "GEMINI",
                "description": "High-speed multimodal generation with generous free-tier support using official Google Gen AI SDK.",
                "is_configured": self._providers["gemini"].is_configured(),
                "masked_key": self._providers["gemini"].get_masked_key(),
                "env_var": "GEMINI_API_KEY",
                "default_model": config.GEMINI_MODEL
            }
        ]

    def list_models(self, provider_name: str, refresh: bool = False) -> List[Dict[str, Any]]:
        """Lists compatible models dynamically for a given provider via ModelDiscoveryService."""
        from backend.services.model_discovery_service import model_discovery_service
        res = model_discovery_service.discover_models(provider_name, force_refresh=refresh)
        return res.get("models", [])

    def discover_models_full(self, provider_name: str, refresh: bool = False) -> Dict[str, Any]:
        """Returns full discovery object including cache info and any error details."""
        from backend.services.model_discovery_service import model_discovery_service
        return model_discovery_service.discover_models(provider_name, force_refresh=refresh)

    def validate_provider(self, provider_name: str) -> Dict[str, Any]:
        """Validates credentials for a given provider."""
        provider = self.get_provider(provider_name)
        return provider.validate_connection()

    def validate_model(self, provider_name: str, model_id: str) -> Dict[str, Any]:
        """Validates specific model generation capability with a real API probe."""
        from backend.services.model_discovery_service import model_discovery_service
        return model_discovery_service.validate_model_selection(provider_name, model_id)

model_registry = ModelRegistry()
