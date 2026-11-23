import logging
from typing import Dict, Any, List, Optional, Tuple
from backend.services.ai_service import ai_service
from backend.mcp.jira_client import jira_client
from backend.database.db import save_requirements, update_agent_status

logger = logging.getLogger("testing_platform.agent1_requirement")

class RequirementAnalysisAgent:
    """
    AGENT 1: REQUIREMENT ANALYSIS AGENT
    Responsibilities:
    1. Accept website URL, Jira issue ID, or manual requirements.
    2. Connect to Jira using MCP when Jira information is provided.
    3. Retrieve user story, description, acceptance criteria, and business rules.
    4. In Basic Mode: Inspects accessible website information (HTML title, forms, inputs, links, buttons).
    5. In AI Mode: Calls Gemini or OpenAI API with structured JSON output enforcement.
    6. Centralized Gemini Reliability: Retries transient errors up to 3 times with exponential backoff & jitter.
    7. Supports configured alternative Gemini models. Never switches to OpenAI or Basic silently.
    8. Records selected and actual model metadata.
    """
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.agent_name = "requirement_agent"

    def execute(
        self,
        website_url: str,
        manual_requirements: str = "",
        jira_project: str = "",
        jira_issue_id: str = "",
        generation_mode: str = "basic",
        ai_model: Optional[str] = None,
        alternative_models: Optional[List[str]] = None
    ) -> Tuple[List[Dict[str, Any]], str, Optional[str]]:
        logger.info(
            f"[{self.run_id}] Agent 1: Starting requirement analysis "
            f"(Mode: {generation_mode.upper()}, Model: {ai_model or 'default'}, Alternatives: {alternative_models or []})..."
        )
        update_agent_status(self.run_id, self.agent_name, "RUNNING")

        try:
            jira_data = None
            if jira_issue_id:
                logger.info(f"[{self.run_id}] Retrieving Jira issue '{jira_issue_id}' via MCP...")
                jira_data = jira_client.get_issue_details(jira_issue_id)

            # Generate requirements via centralized AI service
            requirements, actual_mode, fallback_reason = ai_service.generate_requirements(
                website_url=website_url,
                manual_reqs=manual_requirements,
                jira_data=jira_data,
                preferred_mode=generation_mode,
                model_name=ai_model,
                alternative_models=alternative_models,
                run_id=self.run_id
            )

            meta = ai_service.last_execution_metadata or {}
            selected_model = meta.get("selected_model", ai_model or "")
            actual_model = meta.get("actual_model", ai_model or "")
            retries_count = meta.get("retries_count", 0)
            models_attempted = meta.get("models_attempted", [ai_model] if ai_model else [])

            # Persist to database
            save_requirements(
                self.run_id,
                requirements,
                generation_mode=actual_mode,
                ai_provider=actual_mode,
                ai_model=actual_model or ""
            )

            update_agent_status(
                self.run_id,
                self.agent_name,
                "COMPLETED",
                output_data={
                    "mode": actual_mode,
                    "selected_model": selected_model,
                    "actual_model": actual_model,
                    "retries_count": retries_count,
                    "models_attempted": models_attempted,
                    "fallback_reason": fallback_reason,
                    "count": len(requirements),
                    "requirements": requirements
                },
                retries_count=retries_count,
                selected_model=selected_model,
                actual_model=actual_model,
                models_attempted=models_attempted
            )
            logger.info(f"[{self.run_id}] Agent 1: Generated {len(requirements)} requirements (Actual Model: {actual_model}, Retries: {retries_count}).")
            return requirements, actual_mode, fallback_reason

        except Exception as e:
            err = f"Requirement analysis failed: {str(e)}"
            error_cat = getattr(e, "error_category", "ExecutionError")
            attempted = getattr(e, "models_attempted", [ai_model] if ai_model else [])
            retries = getattr(e, "total_retries", 0)
            logger.error(f"[{self.run_id}] Agent 1 error: {err}")
            update_agent_status(
                self.run_id,
                self.agent_name,
                "FAILED",
                error_message=err,
                retries_count=retries,
                selected_model=ai_model or "",
                models_attempted=attempted,
                error_category=error_cat
            )
            raise
