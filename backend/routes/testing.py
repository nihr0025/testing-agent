import uuid
import logging
from typing import Optional, List
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
    generation_mode: str,
    ai_model: str = "",
    alternative_models: Optional[List[str]] = None
):
    try:
        orchestrator = OrchestrationAgent(run_id)
        orchestrator.run_workflow(
            website_url=website_url,
            manual_requirements=manual_reqs,
            jira_project=jira_project,
            jira_issue_id=jira_issue_id,
            automation_framework=framework,
            generation_mode=generation_mode,
            ai_model=ai_model,
            alternative_models=alternative_models or []
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

    # Determine requested provider / mode
    provider_req = (req.ai_provider or req.generation_mode or config.DEFAULT_TESTING_MODE or "basic").lower().strip()
    if provider_req not in ["basic", "gemini", "openai"]:
        provider_req = "basic"

    chosen_model = (req.ai_model or "").strip()
    actual_mode = provider_req
    mode_reason = ""

    # Strict model selection and credential enforcement (No silent fallback)
    if provider_req == "gemini":
        if not config.is_gemini_configured():
            raise HTTPException(
                status_code=400,
                detail="GEMINI_API_KEY (or GOOGLE_API_KEY) is not configured in backend .env. Please add GEMINI_API_KEY to your .env file or choose Basic Mode."
            )
        if not chosen_model:
            raise HTTPException(
                status_code=400,
                detail="No Gemini model was selected. Please select a dynamically discovered model from the dropdown before launching the run."
            )
    elif provider_req == "openai":
        if not config.is_openai_configured():
            raise HTTPException(
                status_code=400,
                detail="OPENAI_API_KEY is not configured in backend .env. Please add OPENAI_API_KEY to your .env file or choose Basic Mode."
            )
        if not chosen_model:
            raise HTTPException(
                status_code=400,
                detail="No OpenAI model was selected. Please select a dynamically discovered model from the dropdown before launching the run."
            )
    else:
        actual_mode = "basic"
        chosen_model = ""

    if framework not in ["playwright", "selenium"]:
        framework = "playwright"

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
    alt_models = [m.strip() for m in (req.alternative_models or []) if m and m.strip()]

    # Initialize testing run & 6 agent records in database
    create_testing_run(
        run_id=run_id,
        website_url=url,
        jira_project=jira_proj,
        jira_issue_id=jira_issue,
        manual_requirements=manual_req,
        automation_framework=framework,
        generation_mode=actual_mode,
        mode_reason=mode_reason,
        ai_provider=actual_mode,
        ai_model=chosen_model,
        alternative_models=alt_models
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
        actual_mode,
        chosen_model,
        alt_models
    )

    return {
        "run_id": run_id,
        "status": "PENDING",
        "automation_framework": framework,
        "generation_mode": actual_mode,
        "ai_provider": actual_mode,
        "ai_model": chosen_model,
        "mode_reason": mode_reason,
        "message": f"Testing run initiated with 6 agents using {framework.upper()} in {actual_mode.upper()} mode."
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
