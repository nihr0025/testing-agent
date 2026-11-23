import pytest
import json
import uuid
import subprocess
from unittest.mock import MagicMock, patch
from backend.services.gemini_execution_engine import GeminiExecutionEngine, GeminiExecutionError
from backend.services.ai_service import ai_service
from backend.agents.requirement_agent import RequirementAnalysisAgent
from backend.agents.scenario_agent import TestScenarioGenerationAgent
from backend.agents.testcase_agent import TestCaseDesignAgent
from backend.agents.automation_agent import TestAutomationAgent
from backend.agents.execution_agent import TestExecutionAgent
from backend.agents.orchestrator_agent import OrchestrationAgent
from backend.database.db import (
    create_testing_run,
    get_run,
    get_agent_states,
    get_requirements,
    get_scenarios,
    get_test_cases
)

# Prevent pytest from attempting to collect Agent classes as Test classes
RequirementAnalysisAgent.__test__ = False
TestScenarioGenerationAgent.__test__ = False
TestCaseDesignAgent.__test__ = False
TestAutomationAgent.__test__ = False
TestExecutionAgent.__test__ = False

# ---------------------------------------------------------------------------
# 1. Backoff, Jitter, and Retry-After Tests
# ---------------------------------------------------------------------------

def test_exponential_backoff_and_jitter_calculation():
    engine = GeminiExecutionEngine(base_delay_seconds=1.0, max_delay_seconds=20.0, jitter_factor=0.5)
    
    # Attempt 0: 1.0 + jitter
    d0 = engine.calculate_backoff(attempt=0)
    assert 1.05 <= d0 <= 1.55
    
    # Attempt 1: 2.0 + jitter
    d1 = engine.calculate_backoff(attempt=1)
    assert 2.05 <= d1 <= 3.05
    
    # Attempt 2: 4.0 + jitter
    d2 = engine.calculate_backoff(attempt=2)
    assert 4.05 <= d2 <= 6.05
    
    # Retry-After header overrides exponential calculation
    dra = engine.calculate_backoff(attempt=2, retry_after=7.5)
    assert dra == 7.5

def test_transient_error_retry_with_backoff_success():
    """Simulates 503 ServiceUnavailable on attempts 1 and 2, then succeeds on attempt 3."""
    engine = GeminiExecutionEngine(base_delay_seconds=0.01, jitter_factor=0.01)
    
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({"status": "ok", "message": "recovered"})
    
    # Fails twice with 503, succeeds on 3rd attempt
    error_503 = Exception("503 UNAVAILABLE. This model is currently experiencing high demand.")
    mock_client.models.generate_content.side_effect = [error_503, error_503, mock_response]
    
    with patch.object(engine, "_get_client", return_value=mock_client), \
         patch("time.sleep") as mock_sleep:
        
        result = engine.execute(
            prompt="test prompt",
            primary_model="gemini-3.8-flash",
            run_id="TEST-RUN-1",
            agent_name="requirement_agent"
        )
        
        assert result["actual_model"] == "gemini-3.8-flash"
        assert result["retries_count"] == 2
        assert result["failover_occurred"] is False
        assert result["data"]["message"] == "recovered"
        assert mock_sleep.call_count == 2

# ---------------------------------------------------------------------------
# 2. Permanent Errors (No Retry) Tests
# ---------------------------------------------------------------------------

def test_permanent_401_authentication_error_not_retried():
    """401 Authentication errors must abort immediately without retrying."""
    engine = GeminiExecutionEngine(base_delay_seconds=0.01)
    mock_client = MagicMock()
    error_401 = Exception("401 UNAUTHENTICATED. API key not valid. Please pass a valid API key.")
    mock_client.models.generate_content.side_effect = error_401
    
    with patch.object(engine, "_get_client", return_value=mock_client), \
         patch("time.sleep") as mock_sleep:
        
        with pytest.raises(GeminiExecutionError) as exc_info:
            engine.execute(
                prompt="ping",
                primary_model="gemini-3.5-flash",
                run_id="TEST-RUN-AUTH"
            )
        
        assert exc_info.value.error_category == "AuthenticationError"
        assert exc_info.value.total_retries == 0
        assert mock_sleep.call_count == 0  # Zero retries

def test_permanent_403_permission_denied_not_retried():
    """403 Permission / Policy errors must abort immediately without retrying."""
    engine = GeminiExecutionEngine(base_delay_seconds=0.01)
    mock_client = MagicMock()
    error_403 = Exception("403 Forbidden. Request to GET /v1/models not allowed by policy")
    mock_client.models.generate_content.side_effect = error_403
    
    with patch.object(engine, "_get_client", return_value=mock_client), \
         patch("time.sleep") as mock_sleep:
        
        with pytest.raises(GeminiExecutionError) as exc_info:
            engine.execute(
                prompt="ping",
                primary_model="gemini-3.5-flash",
                run_id="TEST-RUN-PERM"
            )
        
        assert exc_info.value.error_category == "PermissionDenied"
        assert exc_info.value.total_retries == 0
        assert mock_sleep.call_count == 0

# ---------------------------------------------------------------------------
# 3. Model Failover & Strict Policy Tests
# ---------------------------------------------------------------------------

def test_model_404_immediate_failover_to_configured_alternative():
    """When a model returns 404 (retired), engine immediately fails over to alternative Gemini model."""
    engine = GeminiExecutionEngine(base_delay_seconds=0.01)
    mock_client = MagicMock()
    
    error_404 = Exception("404 NOT_FOUND. This model models/gemini-2.5-flash is no longer available to new users.")
    mock_success = MagicMock()
    mock_success.text = json.dumps({"result": "success from alt model"})
    
    mock_client.models.generate_content.side_effect = [error_404, mock_success]
    
    with patch.object(engine, "_get_client", return_value=mock_client), \
         patch("time.sleep") as mock_sleep:
        
        result = engine.execute(
            prompt="test prompt",
            primary_model="gemini-2.5-flash",
            alternative_models=["gemini-3.5-flash"],
            run_id="TEST-RUN-FAILOVER"
        )
        
        assert result["selected_model"] == "gemini-2.5-flash"
        assert result["actual_model"] == "gemini-3.5-flash"
        assert result["failover_occurred"] is True
        assert result["data"]["result"] == "success from alt model"
        assert mock_sleep.call_count == 0  # No sleeping on 404, immediate alternative switch

def test_strict_no_switch_to_openai_or_basic():
    """When all candidate Gemini models fail, engine must raise GeminiExecutionError, NEVER switch providers."""
    engine = GeminiExecutionEngine(max_retries_per_model=1, base_delay_seconds=0.001)
    mock_client = MagicMock()
    
    error_503 = Exception("503 UNAVAILABLE. Spike in demand.")
    mock_client.models.generate_content.side_effect = error_503
    
    with patch.object(engine, "_get_client", return_value=mock_client), \
         patch("time.sleep"):
        
        with pytest.raises(GeminiExecutionError) as exc_info:
            engine.execute(
                prompt="test",
                primary_model="gemini-3.8-flash",
                alternative_models=["gemini-3.5-flash"],
                run_id="TEST-RUN-EXHAUST"
            )
        
        assert "gemini-3.8-flash" in exc_info.value.models_attempted
        assert "gemini-3.5-flash" in exc_info.value.models_attempted
        assert exc_info.value.total_retries >= 2

# ---------------------------------------------------------------------------
# 4. Agent Failure Isolation & Preservation of Prior Outputs
# ---------------------------------------------------------------------------

def test_agent_failure_isolation_and_output_preservation():
    """Simulates Agent 3 failing, and verifies Agent 1 and Agent 2 outputs remain intact in SQLite."""
    run_id = f"RUN-ISO-{uuid.uuid4().hex[:6].upper()}"
    create_testing_run(
        run_id=run_id,
        website_url="https://example.com",
        jira_project="",
        jira_issue_id="",
        manual_requirements="Verify checkout flow",
        automation_framework="playwright",
        generation_mode="gemini",
        ai_provider="gemini",
        ai_model="gemini-3.5-flash"
    )
    
    orchestrator = OrchestrationAgent(run_id)
    
    mock_reqs = [{"req_id": "REQ-01", "description": "User must checkout successfully", "priority": "High"}]
    mock_scenarios = [{"scenario_id": "SC-01", "req_id": "REQ-01", "title": "Checkout with valid card", "scenario_type": "Functional", "priority": "High"}]
    
    with patch("backend.services.ai_service.ai_service.generate_requirements", return_value=(mock_reqs, "gemini", None)), \
         patch("backend.services.ai_service.ai_service.generate_scenarios", return_value=mock_scenarios), \
         patch("backend.services.ai_service.ai_service.generate_test_cases", side_effect=GeminiExecutionError("Quota exhausted on Agent 3", selected_model="gemini-3.5-flash", error_category="QuotaExceeded")):
        
        with pytest.raises(RuntimeError) as exc_info:
            orchestrator.run_workflow(
                website_url="https://example.com",
                generation_mode="gemini",
                ai_model="gemini-3.5-flash"
            )
        
        assert "Quota exhausted on Agent 3" in str(exc_info.value)
        
        # Verify SQLite DB: Run is marked FAILED
        run_record = get_run(run_id)
        assert run_record["status"] == "FAILED"
        
        # Verify Agent 1 and Agent 2 artifacts are fully preserved!
        saved_reqs = get_requirements(run_id)
        assert len(saved_reqs) == 1
        assert saved_reqs[0]["req_id"] == "REQ-01"
        
        saved_scenarios = get_scenarios(run_id)
        assert len(saved_scenarios) == 1
        assert saved_scenarios[0]["scenario_id"] == "SC-01"
        
        # Verify Agent 3 state is FAILED with error category
        agent_states = get_agent_states(run_id)
        agent3_state = next(a for a in agent_states if a["agent_name"] == "testcase_agent")
        assert agent3_state["status"] == "FAILED"
        assert agent3_state["error_category"] == "QuotaExceeded"

# ---------------------------------------------------------------------------
# 5. Mocked Tests for All Six Agents with Centralized Gemini Execution
# ---------------------------------------------------------------------------

def test_all_six_agents_centralized_gemini_execution():
    """Runs a complete six-agent orchestration through mocked Centralized Gemini Engine."""
    run_id = f"RUN-6AG-{uuid.uuid4().hex[:6].upper()}"
    create_testing_run(
        run_id=run_id,
        website_url="https://example.com",
        jira_project="",
        jira_issue_id="",
        manual_requirements="Validate user profile and settings",
        automation_framework="playwright",
        generation_mode="gemini",
        ai_provider="gemini",
        ai_model="gemini-3.8-flash",
        alternative_models=["gemini-3.5-flash"]
    )
    
    req_json = {"requirements": [{"req_id": "REQ-01", "description": "Profile update", "priority": "High"}]}
    scen_json = {"scenarios": [{"scenario_id": "SC-01", "req_id": "REQ-01", "title": "Edit Name", "scenario_type": "Functional", "priority": "High"}]}
    cases_json = {"test_cases": [{"case_id": "TC-01", "scenario_id": "SC-01", "title": "Test Name Edit", "priority": "High"}]}
    code_text = "def test_tc_01():\n    assert True\n"
    triage_json = {"analysis_summary": "Clean execution", "flaky_tests_predicted": [], "optimization_suggestions": ["Use page fixture"]}
    report_json = {"executive_summary": "Passed with 100% confidence", "release_recommendation": "Ready for Production", "quality_score": 98, "actionable_recommendations": ["Automate regression suite"]}

    def mock_engine_execute(*args, **kwargs):
        agent_name = kwargs.get("agent_name", "")
        if agent_name == "requirement_agent":
            return {"data": req_json, "selected_model": "gemini-3.8-flash", "actual_model": "gemini-3.8-flash", "retries_count": 0, "models_attempted": ["gemini-3.8-flash"]}
        elif agent_name == "scenario_agent":
            return {"data": scen_json, "selected_model": "gemini-3.8-flash", "actual_model": "gemini-3.8-flash", "retries_count": 0, "models_attempted": ["gemini-3.8-flash"]}
        elif agent_name == "testcase_agent":
            return {"data": cases_json, "selected_model": "gemini-3.8-flash", "actual_model": "gemini-3.8-flash", "retries_count": 0, "models_attempted": ["gemini-3.8-flash"]}
        elif agent_name == "automation_agent":
            return {"data": code_text, "selected_model": "gemini-3.8-flash", "actual_model": "gemini-3.8-flash", "retries_count": 0, "models_attempted": ["gemini-3.8-flash"]}
        elif agent_name == "execution_agent":
            return {"data": triage_json, "selected_model": "gemini-3.8-flash", "actual_model": "gemini-3.8-flash", "retries_count": 0, "models_attempted": ["gemini-3.8-flash"]}
        elif agent_name == "report_agent":
            return {"data": report_json, "selected_model": "gemini-3.8-flash", "actual_model": "gemini-3.8-flash", "retries_count": 0, "models_attempted": ["gemini-3.8-flash"]}
        return {"data": {}, "selected_model": "gemini-3.8-flash", "actual_model": "gemini-3.8-flash", "retries_count": 0, "models_attempted": ["gemini-3.8-flash"]}

    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "1 passed in 0.05s"
    mock_proc.stderr = ""

    with patch("backend.services.gemini_execution_engine.gemini_engine.execute", side_effect=mock_engine_execute), \
         patch("subprocess.run", return_value=mock_proc):
        
        orchestrator = OrchestrationAgent(run_id)
        result = orchestrator.run_workflow(
            website_url="https://example.com",
            generation_mode="gemini",
            ai_model="gemini-3.8-flash",
            alternative_models=["gemini-3.5-flash"]
        )
        
        assert result["run_id"] == run_id
        assert result["metrics"]["total_tests"] == 1
        assert result["metrics"]["passed_tests"] == 1
        assert result["metrics"]["pass_percentage"] == 100.0
        assert result["actual_model"] == "gemini-3.8-flash"
        
        # Verify run in SQLite
        db_run = get_run(run_id)
        assert db_run["status"] == "COMPLETED"
        assert db_run["actual_model"] == "gemini-3.8-flash"
        
        # Verify all 6 agents completed in agent_states
        states = get_agent_states(run_id)
        assert len(states) == 6
        for s in states:
            assert s["status"] == "COMPLETED"
            assert s["actual_model"] == "gemini-3.8-flash"
