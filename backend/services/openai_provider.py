import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.config import config
from backend.services.ai_provider import AIProvider

logger = logging.getLogger("testing_platform.openai_provider")

INCOMPATIBLE_PREFIXES = (
    "text-embedding", "dall-e", "whisper", "tts", "babbage", "davinci",
    "canary", "realtime", "audio", "moderation", "instruct", "curie", "ada"
)

class OpenAIProvider(AIProvider):
    """
    OPENAI API MODE PROVIDER
    - Reads OPENAI_API_KEY exclusively from backend .env.
    - Strictly avoids hardcoded fallback models or fixed model IDs.
    - Dynamically discovers models via client.models.list() using the authenticated API key.
    - Enforces user-selected model with zero silent fallback.
    """
    name: str = "openai"
    display_name: str = "OpenAI API Mode"

    def __init__(self):
        self._client = None

    def _get_client(self):
        if not self._client and self.is_configured():
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=config.OPENAI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self._client = None
        return self._client

    def is_configured(self) -> bool:
        return bool(config.OPENAI_API_KEY and len(config.OPENAI_API_KEY.strip()) > 5)

    def get_masked_key(self) -> str:
        return config.get_masked_key(config.OPENAI_API_KEY)

    def discover_models_from_api(self) -> List[Dict[str, Any]]:
        """
        Dynamically queries the official OpenAI models.list() API.
        Never returns a hardcoded or simulated fallback catalog.
        """
        client = self._get_client()
        if not client:
            raise RuntimeError(
                "OpenAI client is not configured. OPENAI_API_KEY is missing from backend .env."
            )

        models_resp = client.models.list()
        discovered = []

        for m in models_resp:
            mid = getattr(m, "id", "") or ""
            mid_lower = mid.lower()

            # Filter for text/chat models
            is_candidate = (
                mid_lower.startswith("gpt-") or
                mid_lower.startswith("o1") or
                mid_lower.startswith("o3") or
                mid_lower.startswith("chatgpt-")
            )
            if not is_candidate:
                continue

            # Exclude known non-chat or embedding prefixes
            if any(mid_lower.startswith(p) for p in INCOMPATIBLE_PREFIXES):
                continue

            discovered.append({
                "id": mid,
                "name": mid,
                "description": "Compatible OpenAI text generation model",
                "is_free_tier": False
            })

        # Sort alphabetically
        discovered.sort(key=lambda x: x["id"])
        return discovered

    def test_model_usability(self, model_id: str) -> Dict[str, Any]:
        """
        Verifies model generation capability with a minimal, safe request.
        """
        client = self._get_client()
        if not client:
            raise RuntimeError("OpenAI client is not configured.")

        clean_model = model_id.strip()
        response = client.chat.completions.create(
            model=clean_model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5
        )
        return {
            "success": True,
            "model_id": clean_model,
            "response_snippet": response.choices[0].message.content if response.choices else ""
        }

    def validate_connection(self) -> Dict[str, Any]:
        """
        Validates API key credentials safely by checking model listing capability.
        """
        if not self.is_configured():
            return {
                "valid": False,
                "status": "missing",
                "message": "OPENAI_API_KEY is not configured in backend .env file. Please add OPENAI_API_KEY to your .env file.",
                "provider": "openai",
                "model": None
            }
        try:
            from openai import OpenAI
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            client.models.list()
            return {
                "valid": True,
                "status": "configured",
                "message": "OpenAI API key verified successfully! Ready to dynamically query available models.",
                "provider": "openai",
                "model": None
            }
        except Exception as e:
            err_str = str(e)
            err_type = type(e).__name__
            if "Authentication" in err_type or "401" in err_str:
                return {
                    "valid": False,
                    "status": "invalid",
                    "message": "OpenAI Authentication Failed (401): The OPENAI_API_KEY in .env is invalid or expired.",
                    "provider": "openai",
                    "model": None
                }
            elif "RateLimit" in err_type or "429" in err_str or "quota" in err_str.lower():
                return {
                    "valid": False,
                    "status": "quota_exceeded",
                    "message": "OpenAI Quota Exceeded (429): Account has run out of credits or hit rate limits.",
                    "provider": "openai",
                    "model": None
                }
            elif "PermissionDenied" in err_type or "403" in err_str:
                return {
                    "valid": False,
                    "status": "invalid",
                    "message": "OpenAI Permission Denied (403): Check project/key permissions or country restrictions.",
                    "provider": "openai",
                    "model": None
                }
            return {
                "valid": False,
                "status": "invalid",
                "message": f"OpenAI check failed ({err_type}): {err_str[:120]}",
                "provider": "openai",
                "model": None
            }

    def list_models(self) -> List[Dict[str, Any]]:
        from backend.services.model_discovery_service import model_discovery_service
        res = model_discovery_service.discover_models("openai")
        return res.get("models", [])

    def generate_requirements(
        self,
        website_url: str,
        manual_reqs: str,
        jira_data: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], str, Optional[str]]:
        client = self._get_client()
        if not client:
            raise RuntimeError("OpenAI client is not configured. OPENAI_API_KEY is missing from .env.")

        if not model_name or not model_name.strip():
            raise ValueError("No OpenAI model was selected. Please select a model explicitly before starting.")

        selected_model = model_name.strip()
        prompt = f"""You are a Senior QA Requirements Engineer.
Analyze the provided system information and extract structured functional and non-functional requirements.

Website URL: {website_url or 'None'}
Manual Requirements: {manual_reqs or 'None'}
Jira User Story Details: {json.dumps(jira_data or {}, indent=2)}

Return a JSON object with a "requirements" list. Each object must have:
- "req_id": string (e.g. "REQ-01")
- "description": string
- "acceptance_criteria": list of strings
- "business_rules": list of strings
- "testable_conditions": list of strings
- "missing_information": list of strings
- "priority": "High" | "Medium" | "Low"
"""
        try:
            resp = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You are a professional QA analyst. Respond ONLY with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            raw = resp.choices[0].message.content or "{}"
            data = json.loads(raw)
            items = data.get("requirements") if isinstance(data, dict) else data
            if not isinstance(items, list):
                items = [data]

            for item in items:
                item["generation_mode"] = "ai"
                item["ai_provider"] = "openai"
                item["ai_model"] = selected_model
                item["source"] = f"OpenAI ({selected_model})"

            return items, "openai", None

        except Exception as e:
            logger.error(f"OpenAI requirement generation failed on model '{selected_model}': {e}")
            raise RuntimeError(f"OpenAI model '{selected_model}' failed during requirement generation: {e}")

    def generate_scenarios(
        self,
        requirements: List[Dict[str, Any]],
        model_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        client = self._get_client()
        if not client:
            raise RuntimeError("OpenAI client is not configured.")

        if not model_name or not model_name.strip():
            raise ValueError("No OpenAI model was selected. Please select a model explicitly before starting.")

        selected_model = model_name.strip()
        prompt = f"""Given these requirements, generate comprehensive testing scenarios covering Functional, Negative, Navigation, and Boundary testing.
Map every scenario to its corresponding requirement ID.

Requirements:
{json.dumps(requirements, indent=2)}

Return a JSON object with a "scenarios" list. Each object must have:
- "scenario_id": string (e.g. "SC-01")
- "req_id": string
- "title": string
- "description": string
- "scenario_type": "Functional" | "Negative" | "Navigation" | "Boundary" | "Integration"
- "priority": "High" | "Medium" | "Low"
- "expected_behavior": string
"""
        try:
            resp = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You are a QA scenario architect. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            items = data.get("scenarios") if isinstance(data, dict) else data
            if not isinstance(items, list):
                items = [data]

            for item in items:
                item["generation_mode"] = "ai"
                item["ai_provider"] = "openai"
                item["ai_model"] = selected_model
                item["source"] = f"OpenAI ({selected_model})"

            return items

        except Exception as e:
            logger.error(f"OpenAI scenario generation failed on model '{selected_model}': {e}")
            raise RuntimeError(f"OpenAI model '{selected_model}' failed during scenario generation: {e}")

    def generate_test_cases(
        self,
        scenarios: List[Dict[str, Any]],
        model_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        client = self._get_client()
        if not client:
            raise RuntimeError("OpenAI client is not configured.")

        if not model_name or not model_name.strip():
            raise ValueError("No OpenAI model was selected. Please select a model explicitly before starting.")

        selected_model = model_name.strip()
        prompt = f"""Convert the following test scenarios into concrete, step-by-step test cases for browser automation.

Scenarios:
{json.dumps(scenarios, indent=2)}

Return a JSON object with a "test_cases" list. Each object must have:
- "case_id": string (e.g. "TC-01")
- "scenario_id": string
- "title": string
- "preconditions": list of strings
- "test_data": JSON object with key-value pairs
- "execution_steps": list of strings
- "expected_result": string
- "priority": "High" | "Medium" | "Low"
- "status": "Not Executed"
"""
        try:
            resp = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You are a QA automation testcase designer. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            data = json.loads(resp.choices[0].message.content or "{}")
            items = data.get("test_cases") if isinstance(data, dict) else data
            if not isinstance(items, list):
                items = [data]

            for item in items:
                item["generation_mode"] = "ai"
                item["ai_provider"] = "openai"
                item["ai_model"] = selected_model
                item["source"] = f"OpenAI ({selected_model})"

            return items

        except Exception as e:
            logger.error(f"OpenAI testcase generation failed on model '{selected_model}': {e}")
            raise RuntimeError(f"OpenAI model '{selected_model}' failed during testcase generation: {e}")
