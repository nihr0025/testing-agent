import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.config import config
from backend.services.page_inspector import inspect_web_page

logger = logging.getLogger("testing_platform.ai_service")

class AIService:
    def __init__(self):
        self.api_key = config.OPENAI_API_KEY
        self.model = config.OPENAI_MODEL or "gpt-4o-mini"
        self._client = None
        self.last_fallback_reason = None

    def _get_client(self):
        if not self._client and config.is_openai_configured():
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=config.OPENAI_API_KEY)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self._client = None
        return self._client

    def is_configured(self) -> bool:
        return config.is_openai_configured()

    def generate_requirements(
        self,
        website_url: str,
        manual_reqs: str,
        jira_data: Optional[Dict[str, Any]] = None,
        preferred_mode: str = "auto"
    ) -> Tuple[List[Dict[str, Any]], str, Optional[str]]:
        """
        Agent 1: Analyzes requirements.
        Returns: (requirements_list, actual_mode, fallback_reason)
        """
        self.last_fallback_reason = None
        client = self._get_client()

        # Decide mode
        use_ai = (preferred_mode == "ai" or preferred_mode == "auto") and client is not None

        if use_ai:
            prompt = f"""You are a Senior QA Requirements Engineer.
Analyze the provided system information and extract structured functional and non-functional requirements.

Website URL: {website_url or 'None'}
Manual Requirements: {manual_reqs or 'None'}
Jira User Story Details: {json.dumps(jira_data or {}, indent=2)}

Return a strict JSON array of requirement objects. Each object must have:
- "req_id": string (e.g. "REQ-01", "REQ-02")
- "description": string
- "acceptance_criteria": list of strings
- "business_rules": list of strings
- "testable_conditions": list of strings
- "missing_information": list of strings (identify any missing or ambiguous requirements)
- "priority": "High" | "Medium" | "Low"
"""
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert QA requirements analyst. Respond ONLY with a valid JSON array."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                raw_text = response.choices[0].message.content
                data = json.loads(raw_text)
                items = []
                if isinstance(data, dict):
                    for k in ["requirements", "data", "items"]:
                        if k in data and isinstance(data[k], list):
                            items = data[k]
                            break
                    if not items:
                        items = [data]
                elif isinstance(data, list):
                    items = data

                for item in items:
                    item["generation_mode"] = "ai"
                    item["source"] = "AI-Powered Analysis (OpenAI)"
                return items, "ai", None

            except Exception as e:
                err_str = str(e)
                if "Authentication" in type(e).__name__ or "401" in err_str:
                    reason = "OpenAI Authentication Error (Invalid API Key). Switched to Basic Testing Mode using page inspection."
                elif "RateLimit" in type(e).__name__ or "429" in err_str or "quota" in err_str.lower():
                    reason = "OpenAI Rate Limit / Quota Exceeded (429). Switched to Basic Testing Mode using page inspection."
                else:
                    reason = f"OpenAI API error ({type(e).__name__}): {err_str[:120]}. Switched to Basic Testing Mode."
                logger.warning(reason)
                self.last_fallback_reason = reason

        # Basic Testing Mode using live inspection
        inspected = inspect_web_page(website_url)
        target_name = inspected.get("title") or website_url or "Target Application"

        # Discovered inputs and controls summary
        input_names = [inp.get("id") or inp.get("name") or inp.get("placeholder") for inp in inspected.get("inputs", []) if inp.get("id") or inp.get("name")]
        btn_names = [b.get("id") or b.get("text") for b in inspected.get("buttons", []) if b.get("id") or b.get("text")]
        inputs_summary = f"Identified fields: {', '.join(input_names[:4])}" if input_names else "Discovered form fields"
        buttons_summary = f"Identified triggers: {', '.join(btn_names[:3])}" if btn_names else "Interactive buttons"

        reqs = [
            {
                "req_id": "REQ-01",
                "description": f"Verify page loading, HTTP accessibility, and document title for '{target_name}'.",
                "acceptance_criteria": [
                    f"Page loads with HTTP 200 status within 5 seconds.",
                    f"Title matches accessible page identity: '{target_name[:40]}'.",
                    "Root layout container and primary navigation elements are visible."
                ],
                "business_rules": [
                    "Public landing routes must be accessible without credential challenge.",
                    "No broken structural layouts or blocking script crashes."
                ],
                "testable_conditions": [
                    "Standard browser page load with DOM content loaded ready state.",
                    "Verification of visible navigation anchors."
                ],
                "missing_information": [
                    "Target page performance budget SLA latency threshold."
                ],
                "priority": "High",
                "generation_mode": "basic",
                "source": "Basic Inspection Engine (Page Inspector)"
            },
            {
                "req_id": "REQ-02",
                "description": f"Validate input controls, search/entry forms, and validation rules ({inputs_summary}).",
                "acceptance_criteria": [
                    "Input fields accept valid alphanumeric characters and symbols.",
                    "Empty submissions on mandatory fields trigger clear inline validation errors.",
                    "Form input maintains state and sanitizes special characters."
                ],
                "business_rules": [
                    "Mandatory fields must prevent empty form submission.",
                    "Search and entry triggers must handle special characters safely."
                ],
                "testable_conditions": [
                    "Valid input string submission.",
                    "Empty input string submission triggering negative validation.",
                    "Exceeding maximum field length bounds."
                ],
                "missing_information": [
                    "Specific regex format specifications for custom input fields."
                ],
                "priority": "High",
                "generation_mode": "basic",
                "source": "Basic Inspection Engine (Page Inspector)"
            },
            {
                "req_id": "REQ-03",
                "description": f"Ensure interactive controls ({buttons_summary}) and navigation links function responsively.",
                "acceptance_criteria": [
                    "Action buttons respond to click interactions within 2 seconds.",
                    "Navigation anchors lead to valid target sections or pages.",
                    "Absence of unhandled JavaScript exceptions during user interactions."
                ],
                "business_rules": [
                    "Clickable triggers must remain enabled when prerequisites are satisfied.",
                    "Dead links or unhandled errors must be captured."
                ],
                "testable_conditions": [
                    "Button click interaction.",
                    "Hyperlink navigation traversal."
                ],
                "missing_information": [
                    "List of external URLs excluded from automation scope."
                ],
                "priority": "Medium",
                "generation_mode": "basic",
                "source": "Basic Inspection Engine (Page Inspector)"
            }
        ]
        return reqs, "basic", self.last_fallback_reason

    def generate_scenarios(
        self,
        requirements: List[Dict[str, Any]],
        mode: str = "basic"
    ) -> List[Dict[str, Any]]:
        """Agent 2: Generates Functional, Negative, and Navigation testing scenarios."""
        client = self._get_client()

        if mode == "ai" and client:
            prompt = f"""You are a QA Test Architect.
Given these requirements, generate comprehensive testing scenarios covering Functional, Negative, Navigation, and Boundary testing.
Avoid duplicates and map every scenario to its corresponding requirement ID.

Requirements:
{json.dumps(requirements, indent=2)}

Return a strict JSON array of scenario objects. Each object must have:
- "scenario_id": string (e.g. "SC-01", "SC-02")
- "req_id": string (must match an existing requirement ID)
- "title": string
- "description": string
- "scenario_type": "Functional" | "Negative" | "Navigation" | "Boundary" | "Integration"
- "priority": "High" | "Medium" | "Low"
- "expected_behavior": string
"""
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a QA test scenario specialist. Return ONLY a valid JSON array."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                raw_text = response.choices[0].message.content
                data = json.loads(raw_text)
                items = []
                if isinstance(data, dict):
                    for k in ["scenarios", "data", "items"]:
                        if k in data and isinstance(data[k], list):
                            items = data[k]
                            break
                    if not items:
                        items = [data]
                elif isinstance(data, list):
                    items = data

                for item in items:
                    item["generation_mode"] = "ai"
                    item["source"] = "AI-Powered Scenario Synthesizer (OpenAI)"
                return items
            except Exception as e:
                logger.warning(f"AI scenario call failed ({e}), using Basic Mode generation.")

        # Basic Mode Scenarios: Functional, Negative, and Navigation
        scenarios = []
        sc_num = 1
        for req in requirements:
            r_id = req.get("req_id", "REQ-01")
            desc = req.get("description", "")

            # 1. Functional Testing Scenario
            scenarios.append({
                "scenario_id": f"SC-{sc_num:02d}",
                "req_id": r_id,
                "title": f"Functional Happy Path Verification for {r_id}",
                "description": f"Verify proper functionality and expected behavior for {desc[:60]}...",
                "scenario_type": "Functional",
                "priority": "High",
                "expected_behavior": "Page responds with HTTP 200, renders target elements, and handles valid user action.",
                "generation_mode": "basic",
                "source": "Basic Scenario Synthesizer (Deterministic)"
            })
            sc_num += 1

            # 2. Negative Testing Scenario
            scenarios.append({
                "scenario_id": f"SC-{sc_num:02d}",
                "req_id": r_id,
                "title": f"Negative Input Validation for {r_id}",
                "description": "Test application behavior when supplied with empty, malformed, or invalid payloads.",
                "scenario_type": "Negative",
                "priority": "Medium",
                "expected_behavior": "System displays a descriptive validation warning without application crash.",
                "generation_mode": "basic",
                "source": "Basic Scenario Synthesizer (Deterministic)"
            })
            sc_num += 1

            # 3. Navigation / Interactive Scenario
            sc_type = "Navigation" if sc_num % 2 == 1 else "Boundary"
            scenarios.append({
                "scenario_id": f"SC-{sc_num:02d}",
                "req_id": r_id,
                "title": f"{sc_type} & Control Responsiveness for {r_id}",
                "description": f"Verify smooth navigation transitions and responsive element clicks under normal usage.",
                "scenario_type": sc_type,
                "priority": "Medium",
                "expected_behavior": "Navigation transitions load smoothly and interactive controls execute actions properly.",
                "generation_mode": "basic",
                "source": "Basic Scenario Synthesizer (Deterministic)"
            })
            sc_num += 1

        return scenarios

    def generate_test_cases(
        self,
        scenarios: List[Dict[str, Any]],
        mode: str = "basic"
    ) -> List[Dict[str, Any]]:
        """Agent 3: Converts scenarios into detailed step-by-step test cases."""
        client = self._get_client()

        if mode == "ai" and client:
            prompt = f"""You are a Test Case Design Specialist.
Convert each test scenario into detailed, actionable test cases with preconditions, test data, execution steps, and expected results.

Scenarios:
{json.dumps(scenarios, indent=2)}

Return a strict JSON array of test case objects. Each object must have:
- "case_id": string (e.g. "TC-01", "TC-02")
- "scenario_id": string (must match scenario ID)
- "title": string
- "preconditions": list of strings
- "test_data": JSON dictionary of test parameters/inputs
- "execution_steps": list of strings
- "expected_result": string
- "priority": "High" | "Medium" | "Low"
- "status": "Not Executed"
"""
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a test case engineer. Return ONLY a valid JSON array."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                raw_text = response.choices[0].message.content
                data = json.loads(raw_text)
                items = []
                if isinstance(data, dict):
                    for k in ["test_cases", "cases", "items"]:
                        if k in data and isinstance(data[k], list):
                            items = data[k]
                            break
                    if not items:
                        items = [data]
                elif isinstance(data, list):
                    items = data

                for item in items:
                    item["generation_mode"] = "ai"
                    item["source"] = "AI-Powered Test Case Engine (OpenAI)"
                return items
            except Exception as e:
                logger.warning(f"AI test case design failed ({e}), using Basic Mode generation.")

        # Basic Mode Test Cases
        test_cases = []
        tc_num = 1
        for sc in scenarios:
            s_id = sc.get("scenario_id", "SC-01")
            s_type = sc.get("scenario_type", "Functional")
            title = sc.get("title", f"Test Case for {s_id}")

            if s_type == "Negative":
                steps = [
                    "Open target application URL in browser",
                    "Navigate to form or query input area",
                    "Submit blank values or invalid characters",
                    "Trigger submit or search button action",
                    "Assert error banner or inline validation message is visible"
                ]
                expected = "Validation message displayed and form does not accept invalid submission."
                test_data = {"input_query": "", "invalid_string": "!@#$%^&*()"}
            elif s_type == "Navigation":
                steps = [
                    "Open target application URL in browser",
                    "Verify initial landing page state",
                    "Locate primary navigation anchors and links",
                    "Click navigation link and observe URL/DOM transition",
                    "Confirm target view or section is presented without error"
                ]
                expected = "Navigation succeeds and target view renders with valid content."
                test_data = {"nav_timeout_ms": 5000}
            elif s_type == "Boundary":
                steps = [
                    "Open target application URL in browser",
                    "Locate text or query input field",
                    "Enter maximum boundary character length (e.g. 255 chars)",
                    "Submit entry and verify application response",
                    "Ensure browser and application handle boundary input safely"
                ]
                expected = "Boundary input processed safely without browser crash or 500 error."
                test_data = {"boundary_string": "A" * 255}
            else:
                steps = [
                    "Open target application URL in browser",
                    "Wait for DOM content to finish loading (DOM ready state)",
                    "Verify page title and main layout container",
                    "Locate primary interactive button or navigation link",
                    "Confirm element is visible and clickable"
                ]
                expected = "Page loads successfully with HTTP 200, valid title, and visible interactive controls."
                test_data = {"timeout_ms": 5000, "expected_status": 200}

            test_cases.append({
                "case_id": f"TC-{tc_num:02d}",
                "scenario_id": s_id,
                "title": title,
                "preconditions": [
                    "Browser engine (Chromium/WebDriver) is initialized",
                    "Target web application endpoint is accessible",
                    "Network connectivity is stable"
                ],
                "test_data": test_data,
                "execution_steps": steps,
                "expected_result": expected,
                "priority": sc.get("priority", "Medium"),
                "status": "Not Executed",
                "generation_mode": "basic",
                "source": "Basic Test Case Engine (Deterministic)"
            })
            tc_num += 1

        return test_cases

ai_service = AIService()
