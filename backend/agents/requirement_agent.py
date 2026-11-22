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
    5. In AI Mode: Calls OpenAI API with structured prompt (falls back to Basic Mode if key invalid or quota exhausted).
    6. Identifies functional conditions and missing/ambiguous requirements.
    7. Generates a structured requirements document in JSON.
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
        generation_mode: str = "auto"
    ) -> Tuple[List[Dict[str, Any]], str, Optional[str]]:
        logger.info(f"[{self.run_id}] Agent 1: Starting requirement analysis (Requested mode: {generation_mode})...")
        update_agent_status(self.run_id, self.agent_name, "RUNNING")

        try:
            jira_data = None
            if jira_issue_id:
                logger.info(f"[{self.run_id}] Retrieving Jira issue '{jira_issue_id}' via MCP...")
                jira_data = jira_client.get_issue_details(jira_issue_id)

            # Generate requirements (AI or Basic Mode)
            requirements, actual_mode, fallback_reason = ai_service.generate_requirements(
                website_url=website_url,
                manual_reqs=manual_requirements,
                jira_data=jira_data,
                preferred_mode=generation_mode
            )

            # Persist to database
            save_requirements(self.run_id, requirements, generation_mode=actual_mode)
            update_agent_status(
                self.run_id,
                self.agent_name,
                "COMPLETED",
                output_data={
                    "mode": actual_mode,
                    "fallback_reason": fallback_reason,
                    "count": len(requirements),
                    "requirements": requirements
                }
            )
            logger.info(f"[{self.run_id}] Agent 1: Generated {len(requirements)} requirements using {actual_mode.upper()} mode.")
            return requirements, actual_mode, fallback_reason

        except Exception as e:
            err = f"Requirement analysis failed: {str(e)}"
            logger.error(f"[{self.run_id}] Agent 1 error: {err}")
            update_agent_status(self.run_id, self.agent_name, "FAILED", error_message=err)
            raise RuntimeError(err)
