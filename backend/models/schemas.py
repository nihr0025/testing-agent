from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class StartRunRequest(BaseModel):
    website_url: Optional[str] = Field(default="", description="URL of the website to test")
    jira_project: Optional[str] = Field(default="", description="Jira project key (optional)")
    jira_issue_id: Optional[str] = Field(default="", description="Jira issue key/ID (optional)")
    manual_requirements: Optional[str] = Field(default="", description="Manual requirement text (optional)")
    automation_framework: str = Field(default="playwright", description="playwright or selenium")
    generation_mode: str = Field(default="basic", description="basic, gemini, or openai")
    ai_provider: Optional[str] = Field(default=None, description="basic, gemini, or openai")
    ai_model: Optional[str] = Field(default=None, description="Specific model ID to use for generation")
    alternative_models: Optional[List[str]] = Field(default=[], description="Configured Gemini alternative models for failover")

class AgentStateModel(BaseModel):
    agent_name: str
    display_name: str
    step_order: int
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_data: Optional[Any] = None
    error_message: Optional[str] = None
    retries_count: Optional[int] = 0
    selected_model: Optional[str] = ""
    actual_model: Optional[str] = ""
    models_attempted: Optional[List[str]] = []
    error_category: Optional[str] = ""

class RequirementModel(BaseModel):
    req_id: str
    description: str
    acceptance_criteria: List[str] = []
    business_rules: List[str] = []
    testable_conditions: List[str] = []
    missing_information: List[str] = []
    priority: str = "Medium"
    generation_mode: str = "basic"
    source: str = "Basic Inspection Engine"
    ai_provider: Optional[str] = "basic"
    ai_model: Optional[str] = ""

class ScenarioModel(BaseModel):
    scenario_id: str
    req_id: str
    title: str
    description: Optional[str] = ""
    scenario_type: str = "Functional"
    priority: str = "Medium"
    expected_behavior: Optional[str] = ""
    generation_mode: str = "basic"
    source: str = "Basic Scenario Engine"
    ai_provider: Optional[str] = "basic"
    ai_model: Optional[str] = ""

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
    generation_mode: str = "basic"
    source: str = "Basic Test Case Engine"
    ai_provider: Optional[str] = "basic"
    ai_model: Optional[str] = ""

class ExecutionResultModel(BaseModel):
    case_id: str
    status: str
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
    generation_mode: str = "basic"
    mode_reason: Optional[str] = ""
    ai_provider: Optional[str] = "basic"
    ai_model: Optional[str] = ""
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

class ModelInfo(BaseModel):
    id: str
    name: str
    description: str
    is_free_tier: bool = False
    is_default: bool = False

class ValidateModelRequest(BaseModel):
    model_id: str = Field(description="The exact model ID to validate via live API probe")

class ValidateModelResponse(BaseModel):
    valid: bool
    provider: str
    model_id: str
    latency_ms: int = 0
    message: str
    error_type: Optional[str] = None

class DiscoveryResultModel(BaseModel):
    provider: str
    models: List[ModelInfo] = []
    cached: bool = False
    cache_age_seconds: Optional[float] = 0.0
    error: Optional[str] = None
    error_type: Optional[str] = None
    message: Optional[str] = ""

class ProviderInfoModel(BaseModel):
    id: str
    name: str
    badge: str
    description: str
    is_configured: bool
    masked_key: str
    env_var: Optional[str] = None
    default_model: Optional[str] = None

class ProviderTestResult(BaseModel):
    valid: bool
    status: str
    message: str
    provider: str
    model: Optional[str] = None

class SettingsModel(BaseModel):
    # Testing Mode
    default_testing_mode: str
    default_automation_framework: str

    # OpenAI Info
    openai_configured: bool
    openai_model: str
    openai_masked_key: str

    # Gemini Info
    gemini_configured: bool
    gemini_model: str
    gemini_masked_key: str

    # Jira Info
    jira_configured: bool
    jira_url: str
    jira_email: str
    jira_mcp_url: Optional[str] = ""

    # Helpful instruction strings
    instructions: Dict[str, str] = {}

class UpdateSettingsRequest(BaseModel):
    openai_model: Optional[str] = None
    gemini_model: Optional[str] = None
    default_testing_mode: Optional[str] = None
    default_automation_framework: Optional[str] = None
    jira_url: Optional[str] = None
    jira_email: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_mcp_url: Optional[str] = None

class JiraIssueItem(BaseModel):
    key: str
    summary: str
    description: Optional[str] = ""
    issue_type: str = "Story"
    status: str = "Open"
    priority: str = "Medium"
