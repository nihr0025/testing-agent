import uuid
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from backend.models.schemas import StartRunRequest, DashboardMetrics
from backend.database.db import (
    create_testing_run,
    get_run,
    get_all_runs,
    get_agent_states,
    get_requirements,
    get_scenarios,
    get_test_cases,
    get_execution_results,
    get_report,
    get_dashboard_metrics
)
from backend.agents.orchestrator_agent import OrchestrationAgent
from backend.config import config

logger = logging.getLogger("testing_platform.routes.testing")
router = APIRouter(prefix="/api/testing", tags=["Testing Automation"])

def run_orchestrator_background(
    run_id: str,
    website_url: str,
    manual_reqs: str,
    jira_project: str,
    jira_issue_id: str,
    framework: str,
    generation_mode: str
):
    try:
        orchestrator = OrchestrationAgent(run_id)
        orchestrator.run_workflow(
            website_url=website_url,
            manual_requirements=manual_reqs,
            jira_project=jira_project,
            jira_issue_id=jira_issue_id,
            automation_framework=framework,
            generation_mode=generation_mode
        )
    except Exception as e:
        logger.error(f"Background execution failed for {run_id}: {e}")

@router.post("/start")
def start_testing_run(req: StartRunRequest, background_tasks: BackgroundTasks):
    url = (req.website_url or "").strip()
    jira_proj = (req.jira_project or "").strip()
    jira_issue = (req.jira_issue_id or "").strip()
    manual_req = (req.manual_requirements or "").strip()
    framework = (req.automation_framework or config.DEFAULT_AUTOMATION_FRAMEWORK).lower()
    gen_mode = (req.generation_mode or "auto").lower().strip()

    if framework not in ["playwright", "selenium"]:
        framework = "playwright"

    if gen_mode not in ["ai", "basic", "auto"]:
        gen_mode = "auto"

    # Resolve mode if auto
    initial_mode = gen_mode
    mode_reason = ""
    if gen_mode == "auto":
        if config.is_openai_configured():
            initial_mode = "ai"
        else:
            initial_mode = "basic"
            mode_reason = "OPENAI_API_KEY not configured. Auto-selected Basic Testing Mode."
    elif gen_mode == "ai" and not config.is_openai_configured():
        initial_mode = "basic"
        mode_reason = "AI Mode requested but OPENAI_API_KEY is not configured. Automatically fell back to Basic Mode."

    # Input validation: At least one input source must be provided
    if not url and not jira_issue and not manual_req:
        raise HTTPException(
            status_code=400,
            detail="Please provide at least a Website URL, a Jira Issue ID, or manual requirements."
        )

    # Validate target URL if provided (SSRF security protection)
    if url:
        valid, msg = config.validate_target_url(url)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)

    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"

    # Initialize testing run & 6 agent records in database
    create_testing_run(
        run_id=run_id,
        website_url=url,
        jira_project=jira_proj,
        jira_issue_id=jira_issue,
        manual_requirements=manual_req,
        automation_framework=framework,
        generation_mode=initial_mode,
        mode_reason=mode_reason
    )

    # Launch multi-agent workflow
    background_tasks.add_task(
        run_orchestrator_background,
        run_id,
        url,
        manual_req,
        jira_proj,
        jira_issue,
        framework,
        initial_mode
    )

    return {
        "run_id": run_id,
        "status": "PENDING",
        "automation_framework": framework,
        "generation_mode": initial_mode,
        "mode_reason": mode_reason,
        "message": f"Testing run initiated with 6 agents using {framework.upper()} in {initial_mode.upper()} mode."
    }

@router.get("/runs")
def list_runs():
    return get_all_runs(limit=50)

@router.get("/{run_id}/status")
def get_run_status(run_id: str):
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return run

@router.get("/{run_id}/agents")
def get_run_agents(run_id: str):
    run = get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    agents = get_agent_states(run_id)
    return {"run_id": run_id, "agents": agents}

@router.get("/{run_id}/requirements")
def get_run_requirements(run_id: str):
    return get_requirements(run_id)

@router.get("/{run_id}/scenarios")
def get_run_scenarios(run_id: str):
    return get_scenarios(run_id)

@router.get("/{run_id}/testcases")
def get_run_testcases(run_id: str):
    return get_test_cases(run_id)

@router.get("/{run_id}/results")
def get_run_results(run_id: str):
    return get_execution_results(run_id)

@router.get("/{run_id}/report")
def get_run_report(run_id: str):
    rep = get_report(run_id)
    if not rep:
        raise HTTPException(status_code=404, detail=f"Report not yet generated for '{run_id}'.")
    return rep

@router.get("/dashboard/metrics")
def get_metrics():
    return get_dashboard_metrics()
