import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.config import config

logger = logging.getLogger("testing_platform.model_discovery")

# Default in-memory cache TTL: 5 minutes (300 seconds)
DEFAULT_CACHE_TTL_SECONDS = 300

class ModelDiscoveryService:
    """
    Centralized Model Discovery & Validation Service.
    - Dynamically discovers models using authenticated provider APIs.
    - Strictly avoids hardcoded fallback models or simulated model catalogs.
    - Provides in-memory caching with configurable TTL and force-refresh capability.
    - Validates individual models with real, safe minimal test requests.
    - Reports authentication, permission, quota, and network errors separately.
    """

    def __init__(self, cache_ttl: int = DEFAULT_CACHE_TTL_SECONDS):
        self.cache_ttl = cache_ttl
        # provider -> (timestamp, list_of_models)
        self._cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}

    def clear_cache(self, provider: Optional[str] = None):
        """Clears the model discovery cache for a provider or all providers."""
        if provider:
            self._cache.pop(provider.lower().strip(), None)
        else:
            self._cache.clear()

    def discover_models(self, provider_name: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Discovers compatible models from the provider API.
        Never returns a fake or hardcoded model list if discovery fails.
        """
        from backend.services.model_registry import model_registry

        prov_key = provider_name.lower().strip()
        provider = model_registry.get_provider(prov_key)

        # Basic mode does not use AI models
        if prov_key == "basic":
            return {
                "provider": "basic",
                "models": [],
                "cached": False,
                "error": None,
                "error_type": None,
                "message": "Basic Mode operates deterministically using live DOM extraction with zero external AI models."
            }

        # Check configuration
        if not provider.is_configured():
            env_var = "GEMINI_API_KEY" if prov_key == "gemini" else "OPENAI_API_KEY"
            return {
                "provider": prov_key,
                "models": [],
                "cached": False,
                "error": f"{env_var} is not configured in backend .env. Please configure {env_var} to discover models.",
                "error_type": "MissingCredentials",
                "message": f"Credentials missing: {env_var} must be set in backend/.env"
            }

        now = time.time()
        # Check cache if not forcing refresh
        if not force_refresh and prov_key in self._cache:
            cache_time, cached_models = self._cache[prov_key]
            if (now - cache_time) < self.cache_ttl:
                return {
                    "provider": prov_key,
                    "models": cached_models,
                    "cached": True,
                    "cache_age_seconds": round(now - cache_time, 1),
                    "error": None,
                    "error_type": None,
                    "message": f"Retrieved {len(cached_models)} dynamically discovered models from cache."
                }

        # Perform live discovery via provider API
        try:
            discovered_models = provider.discover_models_from_api()
            if not discovered_models:
                return {
                    "provider": prov_key,
                    "models": [],
                    "cached": False,
                    "error": f"Provider API returned an empty model list for '{prov_key}'.",
                    "error_type": "EmptyModelList",
                    "message": "No compatible text generation models found on this account."
                }

            # Cache the successful discovery
            self._cache[prov_key] = (now, discovered_models)
            return {
                "provider": prov_key,
                "models": discovered_models,
                "cached": False,
                "cache_age_seconds": 0.0,
                "error": None,
                "error_type": None,
                "message": f"Successfully retrieved {len(discovered_models)} models directly from {provider.display_name}."
            }
        except Exception as e:
            err_str = str(e)
            err_type = type(e).__name__
            logger.error(f"Model discovery failed for provider '{prov_key}': {err_str}")

            error_category = "DiscoveryError"
            if "401" in err_str or "Authentication" in err_type or "API_KEY_INVALID" in err_str:
                error_category = "AuthenticationError"
            elif "403" in err_str or "PermissionDenied" in err_type or "Forbidden" in err_str:
                error_category = "PermissionDenied"
            elif "404" in err_str or "NotFoundError" in err_type or "not found" in err_str.lower():
                error_category = "ModelNotFound"
            elif "429" in err_str or "RateLimit" in err_type or "quota" in err_str.lower() or "RESOURCE_EXHAUSTED" in err_str:
                error_category = "QuotaExceeded"
            elif "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
                error_category = "ServiceUnavailable"
            elif "500" in err_str or "InternalServerError" in err_type:
                error_category = "ServerError"
            elif "Connection" in err_type or "Timeout" in err_type or "network" in err_str.lower():
                error_category = "NetworkError"

            return {
                "provider": prov_key,
                "models": [],
                "cached": False,
                "error": err_str,
                "error_type": error_category,
                "message": f"Model discovery failed ({error_category}): {err_str}"
            }

    def validate_model_selection(self, provider_name: str, model_id: str) -> Dict[str, Any]:
        """
        Validates a specific model with a real, safe minimal generation request.
        """
        from backend.services.model_registry import model_registry

        prov_key = provider_name.lower().strip()
        if not model_id or not model_id.strip():
            return {
                "valid": False,
                "provider": prov_key,
                "model_id": "",
                "latency_ms": 0,
                "error_type": "InvalidModelSelection",
                "message": "No model ID was specified. You must explicitly select a model."
            }

        provider = model_registry.get_provider(prov_key)
        if prov_key == "basic":
            return {
                "valid": True,
                "provider": "basic",
                "model_id": "deterministic",
                "latency_ms": 0,
                "message": "Basic Mode does not require AI model validation."
            }

        if not provider.is_configured():
            env_var = "GEMINI_API_KEY" if prov_key == "gemini" else "OPENAI_API_KEY"
            return {
                "valid": False,
                "provider": prov_key,
                "model_id": model_id,
                "latency_ms": 0,
                "error_type": "MissingCredentials",
                "message": f"Provider credentials missing in .env ({env_var})."
            }

        start_time = time.time()
        try:
            result = provider.test_model_usability(model_id.strip())
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "valid": True,
                "provider": prov_key,
                "model_id": model_id.strip(),
                "latency_ms": latency_ms,
                "error_type": None,
                "message": f"Model '{model_id.strip()}' validated successfully via real generation probe ({latency_ms}ms)."
            }
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            err_str = str(e)
            err_type = type(e).__name__

            error_category = "GenerationError"
            if "401" in err_str or "Authentication" in err_type or "API_KEY_INVALID" in err_str:
                error_category = "AuthenticationError"
            elif "403" in err_str or "PermissionDenied" in err_type or "Forbidden" in err_str:
                error_category = "PermissionDenied"
            elif "404" in err_str or "NotFoundError" in err_type or "not found" in err_str.lower() or "no longer available" in err_str.lower():
                error_category = "ModelNotFound"
            elif "429" in err_str or "RateLimit" in err_type or "quota" in err_str.lower() or "RESOURCE_EXHAUSTED" in err_str:
                error_category = "QuotaExceeded"
            elif "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
                error_category = "ServiceUnavailable"
            elif "500" in err_str or "InternalServerError" in err_type:
                error_category = "ServerError"
            elif "Connection" in err_type or "Timeout" in err_type or "network" in err_str.lower():
                error_category = "NetworkError"

            return {
                "valid": False,
                "provider": prov_key,
                "model_id": model_id.strip(),
                "latency_ms": latency_ms,
                "error_type": error_category,
                "message": f"Validation failed for model '{model_id.strip()}' ({error_category}): {err_str}"
            }

model_discovery_service = ModelDiscoveryService()
