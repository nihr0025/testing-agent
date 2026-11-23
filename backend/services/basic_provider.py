import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.services.ai_provider import AIProvider
from backend.services.page_inspector import inspect_web_page

logger = logging.getLogger("testing_platform.basic_provider")

class BasicProvider(AIProvider):
    """
    BASIC TESTING MODE PROVIDER
    - 100% API-independent and deterministic.
    - Inspects accessible website DOM information (forms, inputs, buttons, links).
    - Synthesizes functional, negative, boundary, and navigation test cases.
    - Zero cost, zero token limits, works offline.
    """
    name: str = "basic"
    display_name: str = "Basic Testing Mode (Deterministic)"

    def is_configured(self) -> bool:
        return True

    def get_masked_key(self) -> str:
        return "N/A (Offline Mode)"

    def validate_connection(self) -> Dict[str, Any]:
        return {
            "valid": True,
            "status": "configured",
            "message": "Basic Testing Mode is fully operational. Uses local page inspection and deterministic QA logic without external APIs.",
            "provider": "basic",
            "model": "rule-based-engine"
        }

    def list_models(self) -> List[Dict[str, Any]]:
        # Basic mode does not use external models
        return []

    def discover_models_from_api(self) -> List[Dict[str, Any]]:
        # Basic mode operates deterministically without external models
        return []

    def test_model_usability(self, model_id: str) -> Dict[str, Any]:
        return {
            "success": True,
            "model_id": "deterministic",
            "message": "Basic Mode is always operational."
        }

    def generate_requirements(
        self,
        website_url: str,
        manual_reqs: str,
        jira_data: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], str, Optional[str]]:
        inspected = inspect_web_page(website_url) if website_url else {}
        target_name = inspected.get("title") or website_url or "Target Application"

        input_names = [
            inp.get("id") or inp.get("name") or inp.get("placeholder")
            for inp in inspected.get("inputs", [])
            if inp.get("id") or inp.get("name")
        ]
        btn_names = [
            b.get("id") or b.get("text")
            for b in inspected.get("buttons", [])
            if b.get("id") or b.get("text")
        ]
        inputs_summary = f"Identified fields: {', '.join(input_names[:4])}" if input_names else "Discovered form fields"
        buttons_summary = f"Identified triggers: {', '.join(btn_names[:3])}" if btn_names else "Interactive buttons"

        reqs = [
            {
                "req_id": "REQ-01",
                "description": f"Verify page loading, HTTP accessibility, and document title for '{target_name}'.",
                "acceptance_criteria": [
                    "Page loads with HTTP 200 status within 5 seconds.",
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
        return reqs, "basic", None

    def generate_scenarios(
        self,
        requirements: List[Dict[str, Any]],
        model_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
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
                "description": f"Verify successful standard user interaction satisfying: {desc}",
                "scenario_type": "Functional",
                "priority": "High",
                "expected_behavior": "Page responds normally with expected DOM nodes rendered and valid HTTP status code.",
                "generation_mode": "basic",
                "source": "Basic Scenario Synthesizer (Rule Engine)"
            })
            sc_num += 1

            # 2. Negative Testing Scenario
            scenarios.append({
                "scenario_id": f"SC-{sc_num:02d}",
                "req_id": r_id,
                "title": f"Negative Input & Validation Handling for {r_id}",
                "description": f"Attempt invalid, empty, or malicious payloads against controls related to {r_id}.",
                "scenario_type": "Negative",
                "priority": "Medium",
                "expected_behavior": "Application prevents submission, shows clear validation hints, and prevents crash.",
                "generation_mode": "basic",
                "source": "Basic Scenario Synthesizer (Rule Engine)"
            })
            sc_num += 1

            # 3. Navigation / Boundary Testing Scenario
            scenarios.append({
                "scenario_id": f"SC-{sc_num:02d}",
                "req_id": r_id,
                "title": f"Navigation & Boundary Traversal for {r_id}",
                "description": f"Validate edge transitions, query parameter tolerance, and browser back/forward integrity.",
                "scenario_type": "Navigation",
                "priority": "Low",
                "expected_behavior": "Page transitions cleanly, persists session context, and gracefully handles unknown routes.",
                "generation_mode": "basic",
                "source": "Basic Scenario Synthesizer (Rule Engine)"
            })
            sc_num += 1

        return scenarios

    def generate_test_cases(
        self,
        scenarios: List[Dict[str, Any]],
        model_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        test_cases = []
        tc_num = 1
        for sc in scenarios:
            s_id = sc.get("scenario_id", "SC-01")
            sc_type = sc.get("scenario_type", "Functional")
            title = sc.get("title", f"Test {s_id}")

            if sc_type == "Negative":
                steps = [
                    "Open browser and navigate to target application route.",
                    "Locate input controls and clear existing values.",
                    "Submit empty payload or oversized input string.",
                    "Verify inline validation banner or disabled state prevents form submission."
                ]
                expected = "Validation error message displayed; unhandled server exception avoided."
                test_data = {"input_payload": "", "special_characters": "<script>alert(1)</script>"}
            elif sc_type == "Navigation":
                steps = [
                    "Navigate to the application root URL.",
                    "Locate primary navigation anchors and interactive links.",
                    "Click first visible navigation link and assert destination status 200.",
                    "Execute browser back navigation and verify landing view state is restored."
                ]
                expected = "Navigation route transitions smoothly with active page breadcrumb rendered."
                test_data = {"expected_route": "/", "timeout_ms": 10000}
            else:
                steps = [
                    "Launch browser instance and navigate to target URL.",
                    "Assert document title and ensure main body layout is visible.",
                    "Verify interactive controls (buttons, links, inputs) are present and clickable.",
                    "Capture execution duration and assert no console runtime exceptions."
                ]
                expected = "Page loads successfully within budget; all core interactable elements respond."
                test_data = {"viewport": "1280x720", "user_agent": "TraceAI-AutonomousAgent/2.0"}

            test_cases.append({
                "case_id": f"TC-{tc_num:02d}",
                "scenario_id": s_id,
                "title": title,
                "preconditions": [
                    "Application is online and accessible.",
                    "Browser execution environment initialized in headless mode."
                ],
                "test_data": test_data,
                "execution_steps": steps,
                "expected_result": expected,
                "priority": sc.get("priority", "Medium"),
                "status": "Not Executed",
                "generation_mode": "basic",
                "source": "Basic Test Case Engine"
            })
            tc_num += 1

        return test_cases
