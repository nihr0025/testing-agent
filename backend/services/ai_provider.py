import abc
from typing import Dict, Any, List, Optional, Tuple

class AIProvider(abc.ABC):
    """
    Abstract Base Class for AI Testing Providers in TraceAI Studio.
    Defines common interface for Basic, OpenAI, and Gemini providers.
    """
    name: str = "base"
    display_name: str = "Base Provider"

    @abc.abstractmethod
    def is_configured(self) -> bool:
        """Returns True if the provider credentials/requirements are satisfied."""
        pass

    @abc.abstractmethod
    def get_masked_key(self) -> str:
        """Returns masked API key for display without exposing secrets."""
        pass

    @abc.abstractmethod
    def validate_connection(self) -> Dict[str, Any]:
        """
        Validates API key/connection safely.
        Returns:
            {
                "valid": bool,
                "status": "configured" | "missing" | "invalid" | "quota_exceeded" | "offline",
                "message": str,
                "provider": str,
                "model": Optional[str]
            }
        """
        pass

    @abc.abstractmethod
    def list_models(self) -> List[Dict[str, Any]]:
        """
        Returns list of compatible models discovered from the provider API.
        """
        pass

    @abc.abstractmethod
    def discover_models_from_api(self) -> List[Dict[str, Any]]:
        """
        Directly queries the authenticated provider API for available models.
        Must NOT return hardcoded fallback lists if the API call fails.
        """
        pass

    @abc.abstractmethod
    def test_model_usability(self, model_id: str) -> Dict[str, Any]:
        """
        Executes a safe minimal test request to verify the selected model works.
        """
        pass

    @abc.abstractmethod
    def generate_requirements(
        self,
        website_url: str,
        manual_reqs: str,
        jira_data: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], str, Optional[str]]:
        """
        Agent 1: Requirement Analysis
        Returns: (requirements, actual_provider, fallback_reason)
        """
        pass

    @abc.abstractmethod
    def generate_scenarios(
        self,
        requirements: List[Dict[str, Any]],
        model_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Agent 2: Test Scenario Generation"""
        pass

    @abc.abstractmethod
    def generate_test_cases(
        self,
        scenarios: List[Dict[str, Any]],
        model_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Agent 3: Test Case Design"""
        pass
