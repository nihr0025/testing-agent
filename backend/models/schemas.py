from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class StartRunRequest(BaseModel):
    website_url: Optional[str] = Field(default="", description="URL of the website to test")
    jira_project: Optional[str] = Field(default="", description="Jira project key (optional)")
    jira_issue_id: Optional[str] = Field(default="", description="Jira issue key/ID (optional)")
    manual_requirements: Optional[str] = Field(default="", description="Manual requirement text (optional)")
    automation_framework: str = Field(default="playwright", description="playwright or selenium")
    generation_mode: str = Field(default="auto", description="ai, basic, or auto")

class AgentStateModel(BaseModel):
    agent_name: str
    display_name: str
    step_order: int
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_data: Optional[Any] = None
    error_message: Optional[str] = None

class RequirementModel(BaseModel):
    req_id: str
    description: str
    acceptance_criteria: List[str] = []
    business_rules: List[str] = []
    testable_conditions: List[str] = []
    missing_information: List[str] = []
    priority: str = "Medium"
    generation_mode: str = "ai"
    source: str = "AI-Powered"

class ScenarioModel(BaseModel):
    scenario_id: str
    req_id: str
    title: str
    description: Optional[str] = ""
    scenario_type: str = "Functional" # Functional, Negative, Boundary, Navigation, Integration
    priority: str = "Medium"
    expected_behavior: Optional[str] = ""
    generation_mode: str = "ai"
    source: str = "AI-Powered"

class TestCaseModel(BaseModel):
    case_id: str
    scenario_id: str
    title: str
    preconditions: List[str] = []
    test_data: Dict[str, Any] = {}
    execution_steps: List[str] = []
    expected_result: str
    priority: str = "Medium"
    status: str = "Not Executed"
    framework: str = "playwright"
    script_path: Optional[str] = None
    code_snippet: Optional[str] = None
    generation_mode: str = "ai"
    source: str = "AI-Powered"

class ExecutionResultModel(BaseModel):
    case_id: str
    status: str # Passed, Failed, Skipped
    actual_result: Optional[str] = ""
    expected_result: Optional[str] = ""
    error_message: Optional[str] = None
    duration_sec: float = 0.0
    screenshot_path: Optional[str] = None
    log_output: Optional[str] = None
    timestamp: str

class TestRunSummary(BaseModel):
    run_id: str
    created_at: str
    status: str
    website_url: Optional[str] = ""
    jira_project: Optional[str] = ""
    jira_issue_id: Optional[str] = ""
    manual_requirements: Optional[str] = ""
    automation_framework: str = "playwright"
    generation_mode: str = "ai"
    mode_reason: Optional[str] = ""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    pass_percentage: float = 0.0
    summary: Optional[str] = None
    error_message: Optional[str] = None

class DashboardMetrics(BaseModel):
    total_runs: int
    total_test_cases: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    pass_percentage: float
    total_requirements: int
    covered_requirements: int
    total_scenarios: int

class SettingsModel(BaseModel):
    openai_configured: bool
    openai_model: str
    masked_api_key: str
    jira_configured: bool
    jira_url: str
    jira_email: str
    default_automation_framework: str
    jira_mcp_url: Optional[str] = ""
    default_generation_mode: str = "auto"

class UpdateSettingsRequest(BaseModel):
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = None
    jira_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_api_token: Optional[str] = None
    default_automation_framework: Optional[str] = None
    jira_mcp_url: Optional[str] = None
    default_generation_mode: Optional[str] = None

class JiraIssueItem(BaseModel):
    key: str
    summary: str
    description: Optional[str] = ""
    issue_type: str = "Story"
    status: str = "Open"
    priority: str = "Medium"
