import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.services.model_registry import model_registry

logger = logging.getLogger("testing_platform.ai_service")

class AIService:
    """
    Facade service coordinating AI providers (Basic, OpenAI, Gemini)
    across the six agents of TraceAI Studio.
    Strictly prevents cross-provider silent fallback unless explicit user consent is provided.
    Supports alternative model failover within the same provider (e.g. Gemini primary -> Gemini alternative).
    """
    def __init__(self):
        self.last_fallback_reason: Optional[str] = None
        self.last_execution_metadata: Dict[str, Any] = {}

    def generate_requirements(
        self,
        website_url: str,
        manual_reqs: str = "",
        jira_data: Optional[Dict[str, Any]] = None,
        preferred_mode: str = "basic",
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        allow_fallback: bool = False,
        run_id: str = "SYSTEM"
    ) -> Tuple[List[Dict[str, Any]], str, Optional[str]]:
        self.last_fallback_reason = None
        self.last_execution_metadata = {}
        prov_key = (preferred_mode or "basic").lower().strip()
        provider = model_registry.get_provider(prov_key)

        # Basic mode requires no external model
        if provider.name == "basic":
            return provider.generate_requirements(website_url, manual_reqs, jira_data, model_name=None)

        # AI Modes require explicit model selection
        if not model_name or not model_name.strip():
            raise ValueError(f"No AI model was specified for {provider.display_name}. An explicit model must be selected by the user.")

        # Check credentials
        if not provider.is_configured():
            env_var = "GEMINI_API_KEY" if provider.name == "gemini" else "OPENAI_API_KEY"
            err_msg = f"{provider.display_name} was requested, but credentials ({env_var}) are not configured in backend .env."
            if not allow_fallback:
                logger.error(err_msg)
                raise RuntimeError(err_msg)
            # Explicit fallback allowed
            logger.warning(f"{err_msg} Fallback consented: switching to Basic Mode.")
            self.last_fallback_reason = err_msg
            basic_provider = model_registry.get_provider("basic")
            reqs, _, _ = basic_provider.generate_requirements(website_url, manual_reqs, jira_data)
            return reqs, "basic", err_msg

        try:
            if provider.name == "gemini":
                res = provider.generate_requirements(
                    website_url=website_url,
                    manual_reqs=manual_reqs,
                    jira_data=jira_data,
                    model_name=model_name.strip(),
                    alternative_models=alternative_models,
                    run_id=run_id
                )
                if len(res) == 4:
                    reqs, mode, reason, meta = res
                else:
                    reqs, mode, reason = res
                    meta = {}
                self.last_execution_metadata = meta
                return reqs, mode, reason
            else:
                return provider.generate_requirements(website_url, manual_reqs, jira_data, model_name=model_name.strip())
        except Exception as e:
            err_msg = f"Requirement generation failed on provider '{provider.name}' with selected model '{model_name}': {e}"
            logger.error(err_msg)
            if not allow_fallback:
                raise RuntimeError(err_msg) from e
            self.last_fallback_reason = err_msg
            basic_provider = model_registry.get_provider("basic")
            reqs, _, _ = basic_provider.generate_requirements(website_url, manual_reqs, jira_data)
            return reqs, "basic", err_msg

    def generate_scenarios(
        self,
        requirements: List[Dict[str, Any]],
        mode: str = "basic",
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        allow_fallback: bool = False,
        run_id: str = "SYSTEM"
    ) -> List[Dict[str, Any]]:
        prov_key = (mode or "basic").lower().strip()
        provider = model_registry.get_provider(prov_key)

        if provider.name == "basic":
            return provider.generate_scenarios(requirements)

        if not model_name or not model_name.strip():
            raise ValueError(f"No AI model was specified for {provider.display_name}. An explicit model must be selected.")

        try:
            if provider.name == "gemini":
                res = provider.generate_scenarios(
                    requirements=requirements,
                    model_name=model_name.strip(),
                    alternative_models=alternative_models,
                    run_id=run_id
                )
                if isinstance(res, tuple) and len(res) == 2:
                    scenarios, meta = res
                else:
                    scenarios, meta = res, {}
                self.last_execution_metadata = meta
                return scenarios
            else:
                return provider.generate_scenarios(requirements, model_name=model_name.strip())
        except Exception as e:
            err_msg = f"Scenario generation failed on provider '{provider.name}' with model '{model_name}': {e}"
            logger.error(err_msg)
            if not allow_fallback:
                raise RuntimeError(err_msg) from e
            basic_provider = model_registry.get_provider("basic")
            return basic_provider.generate_scenarios(requirements)

    def generate_test_cases(
        self,
        scenarios: List[Dict[str, Any]],
        mode: str = "basic",
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        allow_fallback: bool = False,
        run_id: str = "SYSTEM"
    ) -> List[Dict[str, Any]]:
        prov_key = (mode or "basic").lower().strip()
        provider = model_registry.get_provider(prov_key)

        if provider.name == "basic":
            return provider.generate_test_cases(scenarios)

        if not model_name or not model_name.strip():
            raise ValueError(f"No AI model was specified for {provider.display_name}. An explicit model must be selected.")

        try:
            if provider.name == "gemini":
                res = provider.generate_test_cases(
                    scenarios=scenarios,
                    model_name=model_name.strip(),
                    alternative_models=alternative_models,
                    run_id=run_id
                )
                if isinstance(res, tuple) and len(res) == 2:
                    cases, meta = res
                else:
                    cases, meta = res, {}
                self.last_execution_metadata = meta
                return cases
            else:
                return provider.generate_test_cases(scenarios, model_name=model_name.strip())
        except Exception as e:
            err_msg = f"Test case design failed on provider '{provider.name}' with model '{model_name}': {e}"
            logger.error(err_msg)
            if not allow_fallback:
                raise RuntimeError(err_msg) from e
            basic_provider = model_registry.get_provider("basic")
            return basic_provider.generate_test_cases(scenarios)

    def generate_automation_script(
        self,
        test_case: Dict[str, Any],
        target_url: str,
        framework: str = "playwright",
        mode: str = "basic",
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        run_id: str = "SYSTEM"
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """Agent 4: AI Automation Script generation with Gemini or template fallback."""
        prov_key = (mode or "basic").lower().strip()
        if prov_key == "gemini":
            provider = model_registry.get_provider("gemini")
            if provider.is_configured() and model_name:
                code, meta = provider.generate_automation_script(
                    test_case=test_case,
                    target_url=target_url,
                    framework=framework,
                    model_name=model_name.strip(),
                    alternative_models=alternative_models,
                    run_id=run_id
                )
                self.last_execution_metadata = meta
                return code, meta
        return None, {}

    def analyze_execution(
        self,
        execution_results: List[Dict[str, Any]],
        framework: str = "playwright",
        mode: str = "basic",
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        run_id: str = "SYSTEM"
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """Agent 5: AI Execution Triage & Flaky Test Prediction."""
        prov_key = (mode or "basic").lower().strip()
        if prov_key == "gemini":
            provider = model_registry.get_provider("gemini")
            if provider.is_configured() and model_name:
                insights, meta = provider.analyze_execution_results(
                    execution_results=execution_results,
                    framework=framework,
                    model_name=model_name.strip(),
                    alternative_models=alternative_models,
                    run_id=run_id
                )
                self.last_execution_metadata = meta
                return insights, meta
        return None, {}

    def generate_quality_report(
        self,
        metrics: Dict[str, Any],
        execution_results: List[Dict[str, Any]],
        mode: str = "basic",
        model_name: Optional[str] = None,
        alternative_models: Optional[List[str]] = None,
        run_id: str = "SYSTEM"
    ) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
        """Agent 6: AI Executive Quality Report & Release Evaluation."""
        prov_key = (mode or "basic").lower().strip()
        if prov_key == "gemini":
            provider = model_registry.get_provider("gemini")
            if provider.is_configured() and model_name:
                report, meta = provider.generate_quality_report(
                    metrics=metrics,
                    execution_results=execution_results,
                    model_name=model_name.strip(),
                    alternative_models=alternative_models,
                    run_id=run_id
                )
                self.last_execution_metadata = meta
                return report, meta
        return None, {}

ai_service = AIService()
