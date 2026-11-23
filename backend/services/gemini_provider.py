import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.config import config
from backend.services.ai_provider import AIProvider

logger = logging.getLogger("testing_platform.gemini_provider")

INCOMPATIBLE_GEMINI_KEYWORDS = (
    "embedding", "imagen", "aqa", "vision", "bison", "gecko", "text-bison", "chat-bison"
)

class GeminiProvider(AIProvider):
    """
    GOOGLE GEMINI API MODE PROVIDER
    - Uses official google-genai SDK (v3+).
    - Reads GEMINI_API_KEY or GOOGLE_API_KEY exclusively from backend .env.
    - Strictly avoids hardcoded fallback models or fixed model IDs.
    - Dynamically discovers models via client.models.list() using the authenticated API key.
    - Enforces user-selected model with zero silent fallback.
    """
    name: str = "gemini"
    display_name: str = "Google Gemini API Mode"

    def __init__(self):
        self._client = None

    def _get_client(self):
        if not self._client and self.is_configured():
            try:
                from google import genai
                api_key = config.GEMINI_API_KEY or config.GOOGLE_API_KEY
                self._client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Google Gen AI client: {e}")
                self._client = None
        return self._client

    def is_configured(self) -> bool:
        key = config.GEMINI_API_KEY or config.GOOGLE_API_KEY
        return bool(key and len(key.strip()) > 5)

    def get_masked_key(self) -> str:
        key = config.GEMINI_API_KEY or config.GOOGLE_API_KEY
        return config.get_masked_key(key)

    def discover_models_from_api(self) -> List[Dict[str, Any]]:
        """
        Dynamically queries the official Google Gen AI models.list() API.
        Never returns a hardcoded or simulated fallback catalog.
        """
        client = self._get_client()
        if not client:
            raise RuntimeError(
                "Gemini client is not configured. GEMINI_API_KEY is missing from backend .env."
            )

        models_iterable = client.models.list()
        discovered = []

        for m in models_iterable:
            raw_id = getattr(m, "name", "") or ""
            mid = raw_id[len("models/"):] if raw_id.startswith("models/") else raw_id
            mid_lower = mid.lower()

            # Filter for Gemini models capable of text/content generation
            if not ("gemini" in mid_lower or "gemma" in mid_lower):
                continue
            if any(kw in mid_lower for kw in INCOMPATIBLE_GEMINI_KEYWORDS):
                continue

            # Check supported actions if provided by SDK object
            supported_actions = getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", None)
            if supported_actions and isinstance(supported_actions, (list, tuple)):
                actions_lower = [str(a).lower() for a in supported_actions]
                if not any("generatecontent" in a for a in actions_lower):
                    continue

            display_name = getattr(m, "display_name", None) or mid
            description = getattr(m, "description", None) or "Official Google Gemini multimodal model"
            is_flash = "flash" in mid_lower

            discovered.append({
                "id": mid,
                "name": display_name,
                "description": description,
                "is_free_tier": is_flash
            })

        # Sort so that flash models appear first, then alphabetically
        discovered.sort(key=lambda x: (not x["is_free_tier"], x["id"]))
        return discovered

    def test_model_usability(self, model_id: str) -> Dict[str, Any]:
        """
        Verifies model generation capability with a minimal, safe request.
        """
        client = self._get_client()
        if not client:
            raise RuntimeError("Gemini client is not configured.")

        clean_model = model_id.strip()
        if clean_model.startswith("models/"):
            clean_model = clean_model[len("models/"):]

        response = client.models.generate_content(
            model=clean_model,
            contents="ping"
        )
        return {
            "success": True,
            "model_id": clean_model,
            "response_snippet": (response.text or "")[:50]
        }

    def validate_connection(self) -> Dict[str, Any]:
        """
        Validates API key credentials safely by checking model listing capability.
        Never exposes the actual API key.
        """
        if not self.is_configured():
            return {
                "valid": False,
                "status": "missing",
                "message": "GEMINI_API_KEY (or GOOGLE_API_KEY) is not configured in backend .env file. Please add GEMINI_API_KEY=your_key to your .env file.",
                "provider": "gemini",
                "model": None
            }
        try:
            from google import genai
            api_key = config.GEMINI_API_KEY or config.GOOGLE_API_KEY
            client = genai.Client(api_key=api_key)
            models_iter = client.models.list(config={"page_size": 5})
            first_model = next(iter(models_iter), None)
            return {
                "valid": True,
                "status": "configured",
                "message": "Google Gemini API key verified successfully! Ready to dynamically query available models.",
                "provider": "gemini",
                "model": None
            }
        except Exception as e:
            err_str = str(e)
            err_type = type(e).__name__
            if "401" in err_str or "API_KEY_INVALID" in err_str:
                return {
                    "valid": False,
                    "status": "invalid",
                    "error_code": 401,
                    "message": "Gemini Authentication Failed (401): The API key in .env is invalid or unrecognized.",
                    "provider": "gemini",
                    "model": None
                }
            elif "403" in err_str or "PermissionDenied" in err_type or "Forbidden" in err_str:
                return {
                    "valid": False,
                    "status": "forbidden",
                    "error_code": 403,
                    "message": "Gemini Permission Denied (403): Request not allowed by policy. Ensure the Generative Language API is enabled and no API key or IP restrictions block generativelanguage.googleapis.com.",
                    "provider": "gemini",
                    "model": None
                }
            elif "404" in err_str or "NOT_FOUND" in err_str:
                return {
                    "valid": False,
                    "status": "not_found",
                    "error_code": 404,
                    "message": "Gemini Resource Not Found (404): The requested model or endpoint was not found or has been retired by Google.",
                    "provider": "gemini",
                    "model": None
                }
            elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                return {
                    "valid": False,
                    "status": "quota_exceeded",
                    "error_code": 429,
                    "message": "Gemini Quota Exceeded (429): Quota exhausted or rate limit reached for this API key tier.",
                    "provider": "gemini",
                    "model": None
                }
            elif "503" in err_str or "UNAVAILABLE" in err_str:
                return {
                    "valid": False,
                    "status": "unavailable",
                    "error_code": 503,
                    "message": "Google Gemini Service Unavailable (503): High temporary demand on Google's servers. Please retry in a few moments or choose another model.",
                    "provider": "gemini",
                    "model": None
                }
            return {
                "valid": False,
                "status": "error",
                "message": f"Gemini connection failed ({err_type}): {err_str}",
                "provider": "gemini",
                "model": None
            }

    def list_models(self) -> List[Dict[str, Any]]:
        from backend.services.model_discovery_service import model_discovery_service
        res = model_discovery_service.discover_models("gemini")
        return res.get("models", [])

    def _call_gemini_json(
        self,
        prompt: str,
        system_instruction: str,
        model_name: str,
        alternative_models: Optional[List[str]] = None,
        run_id: str = "SYSTEM",
        agent_name: str = "orchestrator"
    ) -> Dict[str, Any]:
        """Invokes Gemini via the Centralized Execution Engine with retries and alternative model failover."""
        from backend.services.gemini_execution_engine import gemini_engine
        return gemini_engine.execute(
            prompt=prompt,
            system_instruction=system_instruction,
            primary_model=model_name,
            alternative_models=alternative_models,
            json_output=True,
            run_id=run_id,
            agent_name=agent_name
        )

    def _call_gemini_text(
        self,
        prompt: str,
        system_instruction: str,
        model_name: str,
        alternative_models: Optional[List[str]] = None,
        run_id: str = "SYSTEM",
        agent_name: str = "orchestrator"
    ) -> Dict[str, Any]:
        """Invokes Gemini for free-form text or code via the Centralized Execution Engine."""
        from backend.services.gemini_execution_engine import gemini_engine
        return gemini_engine.execute(
            prompt=prompt,
            system_instruction=system_instruction,
            primary_model=model_name,
            alternative_models=alternative_models,
            json_output=False,
            run_id=run_id,
            agent_name=agent_name
        )

    def generate_requirements(
        self,
        website_url: str,
        manual_reqs: str,
        jira_data: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        run_id: str = "SYSTEM"
    ) -> Tuple[List[Dict[str, Any]], str, Optional[str], Dict[str, Any]]:
        if not model_name or not model_name.strip():
            raise ValueError("No Gemini model was selected. Please select a model explicitly before starting.")

        selected_model = model_name.strip()
        system_instruction = "You are a Senior QA Requirements Engineer. Respond ONLY with a valid JSON object."
        prompt = f"""Analyze the provided system information and extract structured functional and non-functional requirements.

Website URL: {website_url or 'None'}
Manual Requirements: {manual_reqs or 'None'}
Jira User Story Details: {json.dumps(jira_data or {}, indent=2)}

Return a strict JSON object with a "requirements" key containing a list of requirement objects. Each object must have:
- "req_id": string (e.g. "REQ-01", "REQ-02")
- "description": string
- "acceptance_criteria": list of strings
- "business_rules": list of strings
- "testable_conditions": list of strings
- "missing_information": list of strings
- "priority": "High" | "Medium" | "Low"
"""
        engine_res = self._call_gemini_json(
            prompt=prompt,
            system_instruction=system_instruction,
            model_name=selected_model,
            alternative_models=alternative_models,
            run_id=run_id,
            agent_name="requirement_agent"
        )
        data = engine_res.get("data", {})
        actual_model = engine_res.get("actual_model", selected_model)
        items = data.get("requirements") if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = [data]

        for item in items:
            item["generation_mode"] = "ai"
            item["ai_provider"] = "gemini"
            item["ai_model"] = actual_model
            item["source"] = f"Google Gemini ({actual_model})"

        return items, "gemini", None, engine_res

    def generate_scenarios(
        self,
        requirements: List[Dict[str, Any]],
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        run_id: str = "SYSTEM"
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not model_name or not model_name.strip():
            raise ValueError("No Gemini model was selected. Please select a model explicitly.")

        selected_model = model_name.strip()
        system_instruction = "You are an expert QA Test Architect. Return ONLY a valid JSON object."
        prompt = f"""Given these requirements, generate comprehensive testing scenarios covering Functional, Negative, Navigation, and Boundary testing.
Avoid duplicates and map every scenario to its corresponding requirement ID.

Requirements:
{json.dumps(requirements, indent=2)}

Return a strict JSON object with a "scenarios" key containing a list of scenario objects. Each object must have:
- "scenario_id": string (e.g. "SC-01", "SC-02")
- "req_id": string (must match an existing requirement ID)
- "title": string
- "description": string
- "scenario_type": "Functional" | "Negative" | "Navigation" | "Boundary" | "Integration"
- "priority": "High" | "Medium" | "Low"
- "expected_behavior": string
"""
        engine_res = self._call_gemini_json(
            prompt=prompt,
            system_instruction=system_instruction,
            model_name=selected_model,
            alternative_models=alternative_models,
            run_id=run_id,
            agent_name="scenario_agent"
        )
        data = engine_res.get("data", {})
        actual_model = engine_res.get("actual_model", selected_model)
        items = data.get("scenarios") if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = [data]

        for item in items:
            item["generation_mode"] = "ai"
            item["ai_provider"] = "gemini"
            item["ai_model"] = actual_model
            item["source"] = f"Google Gemini ({actual_model})"

        return items, engine_res

    def generate_test_cases(
        self,
        scenarios: List[Dict[str, Any]],
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        run_id: str = "SYSTEM"
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        if not model_name or not model_name.strip():
            raise ValueError("No Gemini model was selected. Please select a model explicitly.")

        selected_model = model_name.strip()
        system_instruction = "You are a Lead QA Automation Engineer. Return ONLY a valid JSON object."
        prompt = f"""Convert the following test scenarios into concrete, step-by-step test cases for browser automation.

Scenarios:
{json.dumps(scenarios, indent=2)}

Return a strict JSON object with a "test_cases" key containing a list of test case objects. Each object must have:
- "case_id": string (e.g. "TC-01", "TC-02")
- "scenario_id": string (must match a scenario ID)
- "title": string
- "preconditions": list of strings
- "test_data": JSON object with key-value pairs of input parameters
- "execution_steps": list of strings detailing exact execution steps
- "expected_result": string
- "priority": "High" | "Medium" | "Low"
- "status": "Not Executed"
"""
        engine_res = self._call_gemini_json(
            prompt=prompt,
            system_instruction=system_instruction,
            model_name=selected_model,
            alternative_models=alternative_models,
            run_id=run_id,
            agent_name="testcase_agent"
        )
        data = engine_res.get("data", {})
        actual_model = engine_res.get("actual_model", selected_model)
        items = data.get("test_cases") if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = [data]

        for item in items:
            item["generation_mode"] = "ai"
            item["ai_provider"] = "gemini"
            item["ai_model"] = actual_model
            item["source"] = f"Google Gemini ({actual_model})"

        return items, engine_res

    def generate_automation_script(
        self,
        test_case: Dict[str, Any],
        target_url: str,
        framework: str = "playwright",
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        run_id: str = "SYSTEM"
    ) -> Tuple[str, Dict[str, Any]]:
        """AGENT 4: Generates robust Playwright or Selenium automation script using centralized Gemini engine."""
        if not model_name or not model_name.strip():
            raise ValueError("No Gemini model was selected for test automation script generation.")

        selected_model = model_name.strip()
        system_instruction = (
            f"You are a Principal Test Automation Engineer specializing in {framework.upper()} and pytest. "
            "Write robust, production-grade Python test scripts with proper timeouts, clean assertions, and error handling. "
            "Output ONLY valid Python code without Markdown formatting or fences."
        )
        prompt = f"""Generate a complete, executable pytest script for the following test case using {framework.upper()}.
Target Website URL: {target_url}
Test Case Details: {json.dumps(test_case, indent=2)}

Requirements:
1. Define a pytest test function named test_{test_case.get('case_id', 'tc_01').lower().replace('-', '_')}().
2. Must run headless with a timeout of 15000ms.
3. Validate HTTP response status, document title, and visibility of main elements.
4. Catch exceptions gracefully and ensure browser/context cleanup in a finally block.
5. Return ONLY pure Python code without markdown backticks.
"""
        engine_res = self._call_gemini_text(
            prompt=prompt,
            system_instruction=system_instruction,
            model_name=selected_model,
            alternative_models=alternative_models,
            run_id=run_id,
            agent_name="automation_agent"
        )
        raw_code = engine_res.get("data", "")
        # Clean markdown code fences if present
        clean_code = raw_code.strip()
        if clean_code.startswith("```python"):
            clean_code = clean_code[9:]
        elif clean_code.startswith("```"):
            clean_code = clean_code[3:]
        if clean_code.endswith("```"):
            clean_code = clean_code[:-3]

        return clean_code.strip(), engine_res

    def analyze_execution_results(
        self,
        execution_results: List[Dict[str, Any]],
        framework: str = "playwright",
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        run_id: str = "SYSTEM"
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """AGENT 5: Analyzes pytest execution results, diagnoses failure stack traces, and detects flaky test candidates."""
        if not model_name or not model_name.strip():
            raise ValueError("No Gemini model was selected for execution triage.")

        selected_model = model_name.strip()
        system_instruction = "You are a Senior QA Reliability Engineer. Return ONLY a valid JSON object."
        prompt = f"""Analyze the following actual test execution results produced by {framework.upper()} test runs.
Classify failure root causes, evaluate stability, predict potential flaky tests, and provide actionable resolution hints.

Execution Results:
{json.dumps(execution_results, indent=2)}

Return a strict JSON object with:
- "analysis_summary": string
- "flaky_tests_predicted": list of test case IDs likely to be flaky
- "failure_categories": list of objects with "case_id", "category" (e.g. "SelectorDrift", "TimingTimeout", "Server500", "AssertionMismatch"), and "remediation"
- "optimization_suggestions": list of actionable suggestions
- "stability_rating": "High" | "Medium" | "Low"
"""
        engine_res = self._call_gemini_json(
            prompt=prompt,
            system_instruction=system_instruction,
            model_name=selected_model,
            alternative_models=alternative_models,
            run_id=run_id,
            agent_name="execution_agent"
        )
        return engine_res.get("data", {}), engine_res

    def generate_quality_report(
        self,
        metrics: Dict[str, Any],
        execution_results: List[Dict[str, Any]],
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        run_id: str = "SYSTEM"
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """AGENT 6: Generates executive QA synthesis, release risk assessment, and quality gate audit."""
        if not model_name or not model_name.strip():
            raise ValueError("No Gemini model was selected for quality reporting.")

        selected_model = model_name.strip()
        system_instruction = "You are a VP of Quality Engineering. Return ONLY a valid JSON object."
        prompt = f"""Review the test run metrics and execution outcomes to produce an executive quality assessment.

Metrics:
{json.dumps(metrics, indent=2)}

Sample Execution Results:
{json.dumps(execution_results[:10], indent=2)}

Return a strict JSON object with:
- "executive_summary": string
- "release_recommendation": "Ready for Production" | "Ready for Staging" | "Blocked by Critical Failures"
- "quality_score": integer (0 to 100)
- "key_risks": list of strings
- "actionable_recommendations": list of strings
"""
        engine_res = self._call_gemini_json(
            prompt=prompt,
            system_instruction=system_instruction,
            model_name=selected_model,
            alternative_models=alternative_models,
            run_id=run_id,
            agent_name="report_agent"
        )
        return engine_res.get("data", {}), engine_res
